import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import ChallengeHintPanel from '../components/ChallengeHintPanel';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const BrokenAuthAttackPage: React.FC = () => {
  const [username, setUsername] = useState('admin@scale.edu');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showAdmin, setShowAdmin] = useState(false);
  const [lastRequest, setLastRequest] = useState('');
  const [lastExecutedQuery, setLastExecutedQuery] = useState('');
  const [lastDbResult, setLastDbResult] = useState('');
  const [lastExplanation, setLastExplanation] = useState('');
  const [attackStatus, setAttackStatus] = useState<'success' | 'failed' | 'idle'>('idle');
  const navigate = useNavigate();
  const liveQuery = `SELECT * FROM users WHERE username = '${username}' AND password = '${password}'`;

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    const reqBody = { username, password };
    setLastRequest(JSON.stringify(reqBody, null, 2));
    try {
      const res = await axios.post(
        `${API_URL}/api/auth/login`,
        { username, password },
        { params: { challenge: 'broken-auth' } },
      );
      setLastExecutedQuery(res.data.executed_query || liveQuery);
      setLastDbResult(JSON.stringify(res.data.returned_user ?? null, null, 2));
      setLastExplanation(res.data.explanation || '');

      if (res.data.bypass_success) {
        setAttackStatus('success');
        // Keep challenge token isolated so challenge login does not overwrite platform session.
        sessionStorage.setItem('challenge_token_broken_auth', res.data.access_token);
        const token = sessionStorage.getItem('token') || res.data.access_token;
        try {
          await axios.post(
            `${API_URL}/api/challenges/mark-attack-complete`,
            {},
            {
              params: { challenge_type: 'broken-auth' },
              headers: { Authorization: `Bearer ${token}` },
            },
          );
          await axios.post(
            `${API_URL}/api/challenges/state/update`,
            {
              challenge_id: 'broken-auth',
              current_stage: 'admin-dashboard',
              attempt_delta: 1,
            },
            { headers: { Authorization: `Bearer ${token}` } },
          );
        } catch {
          // ignore
        }

        setShowAdmin(true);
        setTimeout(() => navigate('/challenges/attack-success?type=broken-auth'), 2000);
      } else {
        setAttackStatus('failed');
      }
    } catch (err: any) {
      setAttackStatus('failed');
      const detail = err?.response?.data?.detail;
      if (detail?.executed_query) setLastExecutedQuery(detail.executed_query);
      if (detail) setLastDbResult(JSON.stringify(detail.returned_user ?? null, null, 2));
      if (detail?.explanation) setLastExplanation(detail.explanation);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="text-white p-6 max-w-5xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">Broken Authentication Challenge</h1>
      <p className="text-gray-400 mb-6">
        Objective: login as <span className="font-semibold">admin</span> without knowing the real password.
      </p>
      <div className="mb-6 bg-gray-900 border border-indigo-700 rounded p-3 text-sm text-indigo-200">
        Try manipulating the query using SQL injection (e.g. bypass authentication).
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Login portal */}
        <div className="bg-gray-900 p-6 rounded-lg border border-gray-700">
          <h2 className="text-xl font-bold text-blue-400 mb-4">Target: Admin Login Portal</h2>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm mb-1">Username (email)</label>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                className="w-full p-2 bg-gray-800 rounded border border-gray-600"
              />
            </div>
            <div>
              <label className="block text-sm mb-1">Password</label>
              <input
                type="text"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full p-2 bg-gray-800 rounded border border-gray-600"
                placeholder="Try some injection patterns..."
              />
            </div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-red-600 hover:bg-red-700 p-3 rounded font-bold transition"
            >
              {isSubmitting ? 'Submitting...' : 'Login'}
            </button>
          </form>

          <ChallengeHintPanel challengeId="broken-auth" />
        </div>

        <div className="bg-gray-900 p-4 rounded-lg border border-gray-700">
          <h2 className="text-lg font-bold text-emerald-300 mb-3">Challenge Status</h2>
          <p className={`font-semibold mb-2 ${attackStatus === 'success' ? 'text-green-300' : attackStatus === 'failed' ? 'text-red-300' : 'text-gray-300'}`}>
            {attackStatus === 'success' ? '✔ SUCCESS - Injection worked' : attackStatus === 'failed' ? '❌ FAILED - Injection did not bypass auth' : 'Waiting for attempt'}
          </p>
          <p className="text-sm text-gray-300">
            {lastExplanation || "Input is directly concatenated in the SQL query. A payload like ' OR 1=1 -- can make the WHERE condition always true."}
          </p>
          {showAdmin && (
            <div className="bg-green-900/30 border border-green-700 rounded p-3 text-xs">
              <div className="font-bold text-green-300 mb-1">Welcome Admin!</div>
              <p className="text-green-100">
                You have successfully bypassed authentication and accessed the protected admin dashboard.
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gray-900 border border-gray-700 rounded p-3">
          <h3 className="text-sm font-bold text-gray-200 mb-2">Request</h3>
          <pre className="text-xs text-green-300 whitespace-pre-wrap">{lastRequest || 'No request yet.'}</pre>
        </div>
        <div className="bg-gray-900 border border-gray-700 rounded p-3">
          <h3 className="text-sm font-bold text-gray-200 mb-2">Query (Live + Executed)</h3>
          <p className="text-[11px] text-gray-400 mb-1">Live preview</p>
          <pre className="text-xs text-yellow-300 whitespace-pre-wrap mb-2">{liveQuery}</pre>
          <p className="text-[11px] text-gray-400 mb-1">Executed query</p>
          <pre className="text-xs text-orange-300 whitespace-pre-wrap">{lastExecutedQuery || 'No execution yet.'}</pre>
        </div>
        <div className="bg-gray-900 border border-gray-700 rounded p-3">
          <h3 className="text-sm font-bold text-gray-200 mb-2">DB Result</h3>
          <pre className="text-xs text-cyan-300 whitespace-pre-wrap">{lastDbResult || 'No result yet.'}</pre>
        </div>
        <div className="bg-gray-900 border border-gray-700 rounded p-3">
          <h3 className="text-sm font-bold text-gray-200 mb-2">Explanation</h3>
          <p className="text-xs text-blue-200 whitespace-pre-wrap">
            {lastExplanation || 'Run an attempt to see why the query worked or failed.'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default BrokenAuthAttackPage;