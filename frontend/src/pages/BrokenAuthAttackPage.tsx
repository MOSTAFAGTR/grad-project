import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface HintEntry {
  id: number;
  text: string;
  unlocked: boolean;
}

const BrokenAuthAttackPage: React.FC = () => {
  const [username, setUsername] = useState('admin@scale.edu');
  const [password, setPassword] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [hints, setHints] = useState<HintEntry[]>([]);
  const [showAdmin, setShowAdmin] = useState(false);
  const navigate = useNavigate();

  const appendLog = (line: string) => setLogs(prev => [...prev, line]);

  const loadHints = async () => {
    try {
      const token = sessionStorage.getItem('token');
      if (!token) return;
      const res = await axios.get<HintEntry[]>(`${API_URL}/api/challenges/hints`, {
        params: { challenge_id: 'broken-auth' },
        headers: { Authorization: `Bearer ${token}` },
      });
      setHints(res.data);
    } catch {
      // ignore
    }
  };

  React.useEffect(() => {
    loadHints();
  }, []);

  const handleUseHint = async () => {
    try {
      const token = sessionStorage.getItem('token');
      if (!token) return;
      const locked = hints.find(h => !h.unlocked);
      const target = locked ?? hints[hints.length - 1];
      if (!target) return;
      await axios.post(
        `${API_URL}/api/challenges/hints/use`,
        { challenge_id: 'broken-auth', hint_id: target.id },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      loadHints();
    } catch {
      // ignore
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    appendLog(`Attempting login for ${username} ...`);
    try {
      const res = await axios.post(
        `${API_URL}/api/auth/login`,
        { username, password },
        { params: { challenge: 'broken-auth' } },
      );
      appendLog(`Server response: ${res.data.message || 'Login successful.'}`);

      if (res.data.broken_auth && res.data.role === 'admin') {
        appendLog('Broken auth bypass succeeded. Admin session obtained.');
        sessionStorage.setItem('token', res.data.access_token);
        sessionStorage.setItem('role', 'admin');
        sessionStorage.setItem('user_id', String(res.data.user_id ?? ''));
        sessionStorage.setItem('user_email', res.data.email ?? username);

        const token = res.data.access_token;
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
        appendLog('Login did not grant admin access. Try a different payload.');
      }
    } catch (err: any) {
      appendLog(`Login failed: ${err.response?.data?.detail || 'Unknown error'}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="text-white p-6 max-w-5xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">Broken Authentication Challenge</h1>
      <p className="text-gray-400 mb-6">
        Bypass the login protection and obtain an <span className="font-semibold">admin</span> session using a crafted input.
      </p>

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

          {/* Hints */}
          <div className="mt-6 bg-gray-800 border border-gray-700 rounded p-3">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-sm font-bold text-blue-300">Hints</h3>
              <button
                onClick={handleUseHint}
                className="text-xs px-2 py-1 rounded bg-blue-600 hover:bg-blue-700 font-semibold"
              >
                Unlock next hint
              </button>
            </div>
            {hints.length === 0 && <p className="text-xs text-gray-500">No hints available.</p>}
            <ul className="text-xs list-disc list-inside space-y-1">
              {hints.map(h => (
                <li key={h.id} className={h.unlocked ? 'text-gray-200' : 'text-gray-500 italic'}>
                  {h.text}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Attack console / Admin dashboard preview */}
        <div className="bg-gray-900 p-4 rounded-lg border border-green-900 flex flex-col h-80">
          <div className="text-green-500 mb-2 border-b border-green-900 pb-1 font-mono text-xs">
            attacker@lab:~$ broken-auth
          </div>
          <div className="flex-1 overflow-y-auto font-mono text-xs mb-3">
            {logs.length === 0 && <div className="text-gray-600">No login attempts yet.</div>}
            {logs.map((log, i) => (
              <div key={i} className="text-green-400">
                {log}
              </div>
            ))}
          </div>
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
    </div>
  );
};

export default BrokenAuthAttackPage;