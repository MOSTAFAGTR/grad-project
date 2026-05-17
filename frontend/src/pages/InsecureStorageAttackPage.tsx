import * as React from 'react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import ChallengeHintPanel from '../components/ChallengeHintPanel';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const InsecureStorageAttackPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [registerResult, setRegisterResult] = useState<any>(null);
  const [dumpResult, setDumpResult] = useState<any>(null);
  const [error, setError] = useState('');
  // Track that the learner has registered at least one account this session.
  // Without this, the pre-seeded users (alice, bob, admin) would immediately
  // pass the challenge on the very first "Dump Storage" click.
  const [hasRegistered, setHasRegistered] = useState(false);
  const navigate = useNavigate();

  const register = async () => {
    setError('');
    if (!username.trim() || !password.trim()) {
      setError('Enter a username and password to register.');
      return;
    }
    try {
      const res = await axios.post(`${API_URL}/api/challenges/storage/register`, { username, password, secure: false });
      setRegisterResult(res.data);
      setHasRegistered(true);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Register failed');
    }
  };

  const dump = async () => {
    setError('');
    if (!hasRegistered) {
      setError('Register an account first — then dump storage to see your plaintext password exposed.');
      return;
    }
    try {
      const res = await axios.get(`${API_URL}/api/challenges/storage/dump`, { params: { secure: false } });
      setDumpResult(res.data);
      // Confirm that the user we just registered is in the dump with a plaintext password
      const registeredUser = (res.data?.users || []).find(
        (u: any) => u.username === username && typeof u.password === 'string',
      );
      if (registeredUser) {
        const token = sessionStorage.getItem('token');
        if (token) {
          axios.post(
            `${API_URL}/api/challenges/mark-attack-complete?challenge_type=insecure-storage`,
            {},
            { headers: { Authorization: `Bearer ${token}` } },
          ).catch(() => {});
        }
        navigate('/challenges/attack-success?type=insecure-storage');
      }
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Dump failed');
    }
  };

  return (
    <div className="text-white p-6 max-w-5xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">Insecure Storage Attack</h1>
      <p className="text-gray-400 mb-6">Goal: prove passwords are stored in plaintext and exposed via dump.</p>

      {/* Step 1 — Register */}
      <div className={`bg-gray-900 border rounded p-4 mb-4 ${hasRegistered ? 'border-green-600' : 'border-blue-600'}`}>
        <p className="text-xs font-semibold uppercase tracking-wide text-blue-400 mb-2">
          Step 1 — Register an account (stores password in plaintext)
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-3">
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Username (e.g. victim)"
            className="bg-gray-800 border border-gray-700 rounded p-2 text-sm placeholder-gray-500"
          />
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password (e.g. supersecret)"
            className="bg-gray-800 border border-gray-700 rounded p-2 text-sm placeholder-gray-500"
          />
        </div>
        <button onClick={register} className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded font-bold text-sm">
          Register
        </button>
        {hasRegistered && (
          <span className="ml-3 text-green-400 text-sm">✓ Account registered — proceed to Step 2</span>
        )}
      </div>

      {/* Step 2 — Dump */}
      <div className={`bg-gray-900 border rounded p-4 mb-4 ${!hasRegistered ? 'border-gray-700 opacity-60' : 'border-red-600'}`}>
        <p className="text-xs font-semibold uppercase tracking-wide text-red-400 mb-2">
          Step 2 — Dump storage and expose plaintext credentials
        </p>
        <button
          onClick={dump}
          disabled={!hasRegistered}
          className="bg-red-700 hover:bg-red-600 disabled:opacity-40 disabled:cursor-not-allowed px-4 py-2 rounded font-bold text-sm"
        >
          Dump Storage
        </button>
        {!hasRegistered && (
          <span className="ml-3 text-gray-500 text-xs">Complete Step 1 first</span>
        )}
      </div>

      <ChallengeHintPanel challengeId="insecure-storage" />
      {error && <div className="mt-4 bg-red-900/40 border border-red-700 rounded p-3 text-sm">{error}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        <div className="bg-gray-900 border border-gray-700 rounded p-3 text-xs">
          <h3 className="font-bold text-gray-200 mb-2">Request</h3>
          <pre className="text-green-300 whitespace-pre-wrap">{JSON.stringify({ username, password }, null, 2)}</pre>
        </div>
        <div className="bg-gray-900 border border-gray-700 rounded p-3 text-xs">
          <h3 className="font-bold text-gray-200 mb-2">Execution</h3>
          <p className="text-gray-300">Register endpoint then dump endpoint</p>
        </div>
        <div className="bg-gray-900 border border-gray-700 rounded p-3 text-xs">
          <h3 className="font-bold text-gray-200 mb-2">Result</h3>
          <pre className="text-yellow-300 whitespace-pre-wrap max-h-40 overflow-y-auto">{JSON.stringify(dumpResult?.users || registerResult || {}, null, 2)}</pre>
        </div>
        <div className="bg-gray-900 border border-gray-700 rounded p-3 text-xs">
          <h3 className="font-bold text-gray-200 mb-2">Explanation</h3>
          <p className="text-gray-300">
            {(dumpResult?.users || []).some((u: any) => typeof u.password === 'string')
              ? 'Attack succeeded: plaintext passwords are visible in storage dump.'
              : 'Attack not complete yet. Dump storage and verify plaintext credentials are exposed.'}
          </p>
        </div>
      </div>

      <div className="flex gap-3 mt-6">
        <Link to="/challenges/7/fix" className="bg-green-600 hover:bg-green-700 px-5 py-2 rounded font-bold">Go to Fix</Link>
        <Link to="/challenges" className="bg-gray-600 hover:bg-gray-700 px-5 py-2 rounded font-bold">Back</Link>
      </div>
    </div>
  );
};

export default InsecureStorageAttackPage;
