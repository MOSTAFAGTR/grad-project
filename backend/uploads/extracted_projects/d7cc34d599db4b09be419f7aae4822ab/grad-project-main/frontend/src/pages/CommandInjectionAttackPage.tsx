import * as React from 'react';
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import ChallengeHintPanel from '../components/ChallengeHintPanel';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_BASE = `${API_URL}/api/challenges`;

const SUCCESS_MARKER = 'COMMAND_INJECTION_SUCCESS';

const CommandInjectionAttackPage: React.FC = () => {
  const [host, setHost] = useState('');
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [verified, setVerified] = useState<'pending' | 'success' | 'failed'>('pending');
  const navigate = useNavigate();

  const handlePing = async () => {
    setError('');
    setOutput('');
    setVerified('pending');
    if (!host.trim()) {
      setError('Please enter a host value.');
      return;
    }
    try {
      const res = await axios.post<{ output: string; success?: boolean }>(`${API_BASE}/ping`, { host: host.trim() });
      const out = res.data.output || '';
      setOutput(out);
      const executed = Boolean(res.data.success);
      setVerified(executed ? 'success' : 'failed');
      if (executed) {
        const token = sessionStorage.getItem('token');
        if (token) {
          axios.post(`${API_BASE}/mark-attack-complete?challenge_type=command-injection`, {}, { headers: { Authorization: `Bearer ${token}` } }).catch(() => {});
        }
        navigate('/challenges/attack-success?type=command-injection');
      }
    } catch (err: unknown) {
      setVerified('failed');
      const ax = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(ax.response?.data?.detail || ax.message || 'Request failed.');
    }
  };

  return (
    <div className="text-white p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">Command Injection Attack</h1>
      <p className="text-gray-400 mb-6">
        The app runs a <code>ping</code> command with the host you supply. Your goal: inject an extra shell command so the string <code>{SUCCESS_MARKER}</code> appears in the output.
      </p>

      <div className="bg-gray-800 p-6 rounded-lg mb-6 border border-gray-700">
        <h2 className="text-lg font-bold mb-2 text-purple-400">How to inject</h2>
        <ul className="text-gray-300 text-sm space-y-1 list-disc list-inside">
          <li>Use <code>;</code> or <code>&amp;&amp;</code> to run a second command after the ping.</li>
          <li>Use <code>echo {SUCCESS_MARKER}</code> so the output contains that exact string.</li>
          <li>Your input is passed directly to the shell — no validation is done.</li>
        </ul>
      </div>

      <div className="bg-gray-800 p-6 rounded-lg mb-6 border border-gray-700">
        <h2 className="text-lg font-bold mb-2 text-purple-400">Vulnerable endpoint</h2>
        <code className="text-sm text-gray-300">POST {API_BASE}/ping</code>
        <p className="text-sm text-gray-500 mt-2">Body: <code>{`{ "host": "<your input>" }`}</code></p>
      </div>

      {/* Simulated vulnerable app — search bar UI */}
      <div className="bg-gray-900 p-6 rounded-lg border-2 border-purple-500/50 mb-6">
        <p className="text-purple-300 text-xs font-semibold mb-3 uppercase tracking-wide">Simulated vulnerable app</p>
        <div className="bg-white rounded-lg p-4 shadow-inner max-w-xl">
          <div className="flex items-center gap-2 text-gray-800">
            <span className="text-lg font-medium text-gray-500">Ping Checker</span>
          </div>
          <p className="text-gray-500 text-sm mt-1 mb-3">Enter a host to check connectivity</p>
          <div className="flex gap-2">
            <input
              type="text"
              value={host}
              onChange={(e) => setHost(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handlePing()}
              className="flex-1 px-4 py-2.5 bg-gray-100 border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="e.g. 8.8.8.8 or google.com"
            />
            <button
              onClick={handlePing}
              className="px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-lg"
            >
              Ping
            </button>
          </div>
          {host && (
            <p className="mt-2 text-xs text-gray-500 font-mono break-all">
              You are typing: <span className="text-purple-600">{host || '(empty)'}</span>
            </p>
          )}
        </div>
      </div>

      <ChallengeHintPanel challengeId="command-injection" />

      {verified === 'success' && (
        <div className="bg-green-900/50 border border-green-500 text-green-200 p-4 rounded mb-4">
          ✓ <strong>Injection successful!</strong> The string <code>{SUCCESS_MARKER}</code> was found in the output.
        </div>
      )}
      {verified === 'failed' && output && (
        <div className="bg-amber-900/50 border border-amber-500 text-amber-200 p-4 rounded mb-4">
          ✗ <strong>Injection not executed.</strong> The output does not contain <code>{SUCCESS_MARKER}</code>. Try a different payload.
        </div>
      )}

      {output && (
        <div className="bg-black text-green-400 font-mono text-sm p-4 rounded border border-gray-700 mb-4 whitespace-pre-wrap">
          <strong className="text-gray-400">Output:</strong><br />
          {output}
        </div>
      )}
      {error && (
        <div className="bg-red-900/50 border border-red-500 text-red-200 p-3 rounded mb-4 text-sm">
          {error}
        </div>
      )}

      <div className="flex gap-4">
        <Link to="/challenges/4/fix" className="bg-purple-600 hover:bg-purple-700 px-6 py-3 rounded font-bold">
          Try the Fix
        </Link>
        <Link to="/challenges" className="bg-gray-600 hover:bg-gray-700 px-6 py-3 rounded font-bold">
          Back to Challenges
        </Link>
      </div>
    </div>
  );
};

export default CommandInjectionAttackPage;
