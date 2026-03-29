import * as React from 'react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import ChallengeHintPanel from '../components/ChallengeHintPanel';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function looksLikeSensitiveFileLeak(content: string): boolean {
  if (!content || typeof content !== 'string') return false;
  return content.includes('root:') || content.includes('/bin/bash') || content.includes('/bin/sh');
}

const DirectoryTraversalAttackPage: React.FC = () => {
  const [payload, setPayload] = useState('');
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const runAttack = async () => {
    setError('');
    setResult(null);
    try {
      const res = await axios.get(`${API_URL}/api/challenges/traversal/read`, {
        params: { file: payload, secure: false },
      });
      setResult(res.data);
      if (looksLikeSensitiveFileLeak(res.data?.content || '')) {
        const token = sessionStorage.getItem('token');
        if (token) {
          axios.post(
            `${API_URL}/api/challenges/mark-attack-complete?challenge_type=directory-traversal`,
            {},
            { headers: { Authorization: `Bearer ${token}` } },
          ).catch(() => {});
        }
        navigate('/challenges/attack-success?type=directory-traversal');
      }
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Request failed');
    }
  };

  return (
    <div className="text-white p-6 max-w-5xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">Directory Traversal Attack</h1>
      <p className="text-gray-400 mb-6">Goal: read a restricted file by escaping the intended folder.</p>

      <div className="bg-gray-900 border border-gray-700 rounded p-4 mb-4">
        <label className="block text-sm font-bold mb-2">Payload</label>
        <input value={payload} onChange={(e) => setPayload(e.target.value)} placeholder="e.g. relative path under the server files root" className="w-full bg-gray-800 border border-gray-700 rounded p-2 font-mono text-sm mb-3" />
        <button onClick={runAttack} className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded font-bold">Execute Payload</button>
      </div>

      <ChallengeHintPanel challengeId="directory-traversal" />
      {error && <div className="mt-4 bg-red-900/40 border border-red-700 rounded p-3 text-sm">{error}</div>}

      {result && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <div className="bg-gray-900 border border-gray-700 rounded p-3 text-xs">
            <h3 className="font-bold text-gray-200 mb-2">Request</h3>
            <pre className="text-green-300 whitespace-pre-wrap">{JSON.stringify({ file: payload }, null, 2)}</pre>
          </div>
          <div className="bg-gray-900 border border-gray-700 rounded p-3 text-xs">
            <h3 className="font-bold text-gray-200 mb-2">Execution</h3>
            <p className="text-gray-300">Resolved path: <span className="font-mono text-cyan-300">{result.accessed_path || result.resolved_path}</span></p>
          </div>
          <div className="bg-gray-900 border border-gray-700 rounded p-3 text-xs">
            <h3 className="font-bold text-gray-200 mb-2">Result</h3>
            <p className={looksLikeSensitiveFileLeak(result.content || '') ? 'text-red-300' : 'text-green-300'}>
              {looksLikeSensitiveFileLeak(result.content || '') ? 'Response resembles leaked system file content' : 'No obvious system-file fingerprint in response body'}
            </p>
            <pre className="text-yellow-300 whitespace-pre-wrap max-h-40 overflow-y-auto">{result.content || ''}</pre>
          </div>
          <div className="bg-gray-900 border border-gray-700 rounded p-3 text-xs">
            <h3 className="font-bold text-gray-200 mb-2">Explanation</h3>
            <p className="text-gray-300">
              {looksLikeSensitiveFileLeak(result.content || '')
                ? 'Interpret the response: typical passwd-like markers suggest path traversal reached unintended files.'
                : 'Review the raw content above; success is when the response matches your exploitation goal.'}
            </p>
          </div>
        </div>
      )}

      <div className="flex gap-3 mt-6">
        <Link to="/challenges/8/fix" className="bg-green-600 hover:bg-green-700 px-5 py-2 rounded font-bold">Go to Fix</Link>
        <Link to="/challenges" className="bg-gray-600 hover:bg-gray-700 px-5 py-2 rounded font-bold">Back</Link>
      </div>
    </div>
  );
};

export default DirectoryTraversalAttackPage;
