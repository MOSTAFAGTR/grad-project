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
  const navigate = useNavigate();

  const register = async () => {
    setError('');
    try {
      const res = await axios.post(`${API_URL}/api/challenges/storage/register`, { username, password, secure: false });
      setRegisterResult(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Register failed');
    }
  };

  const dump = async () => {
    setError('');
    try {
      const res = await axios.get(`${API_URL}/api/challenges/storage/dump`, { params: { secure: false } });
      setDumpResult(res.data);
      const hasPlaintext = (res.data?.users || []).some((u: any) => typeof u.password === 'string');
      if (hasPlaintext) {
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

      <div className="bg-gray-900 border border-gray-700 rounded p-4 mb-4">
        <label className="block text-sm font-bold mb-2">Register Payload</label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-3">
          <input value={username} onChange={(e) => setUsername(e.target.value)} className="bg-gray-800 border border-gray-700 rounded p-2 text-sm" />
          <input value={password} onChange={(e) => setPassword(e.target.value)} className="bg-gray-800 border border-gray-700 rounded p-2 text-sm" />
        </div>
        <div className="flex gap-2">
          <button onClick={register} className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded font-bold">Register</button>
          <button onClick={dump} className="bg-red-700 hover:bg-red-600 px-4 py-2 rounded font-bold">Dump Storage</button>
        </div>
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
