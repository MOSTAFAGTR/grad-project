import * as React from 'react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import ChallengeHintPanel from '../components/ChallengeHintPanel';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function xxeResponseLooksLikeLeak(data: Record<string, unknown> | null): boolean {
  if (!data) return false;
  const blob = [
    data.extracted_sensitive_data,
    data.sensitive_data,
    data.parsed_result,
    data.parsed_output,
  ]
    .filter(Boolean)
    .join('\n');
  return typeof blob === 'string' && (blob.includes('root:') || blob.includes('/bin/bash') || blob.includes('/bin/sh'));
}

const XxeAttackPage: React.FC = () => {
  const [xml, setXml] = useState('<root></root>');
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const execute = async () => {
    setError('');
    setResult(null);
    try {
      const res = await axios.post(`${API_URL}/api/challenges/xxe/parse`, { xml, secure: false });
      setResult(res.data);
      if (xxeResponseLooksLikeLeak(res.data)) {
        const token = sessionStorage.getItem('token');
        if (token) {
          axios.post(
            `${API_URL}/api/challenges/mark-attack-complete?challenge_type=xxe`,
            {},
            { headers: { Authorization: `Bearer ${token}` } },
          ).catch(() => {});
        }
        navigate('/challenges/attack-success?type=xxe');
      }
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Request failed');
    }
  };

  return (
    <div className="text-white p-6 max-w-5xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">XXE Attack</h1>
      <p className="text-gray-400 mb-6">Goal: extract sensitive system data via XML external entity injection.</p>

      <div className="bg-gray-900 border border-gray-700 rounded p-4 mb-4">
        <label className="block text-sm font-bold mb-2">XML Payload</label>
        <textarea value={xml} onChange={(e) => setXml(e.target.value)} className="w-full h-40 bg-black border border-gray-700 rounded p-2 font-mono text-xs text-green-300 mb-3" />
        <button onClick={execute} className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded font-bold">Execute Payload</button>
      </div>

      <ChallengeHintPanel challengeId="xxe" />
      {error && <div className="mt-4 bg-red-900/40 border border-red-700 rounded p-3 text-sm">{error}</div>}

      {result && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <div className="bg-gray-900 border border-gray-700 rounded p-3 text-xs">
            <h3 className="font-bold text-gray-200 mb-2">Request</h3>
            <pre className="text-green-300 whitespace-pre-wrap">{JSON.stringify({ xml }, null, 2)}</pre>
          </div>
          <div className="bg-gray-900 border border-gray-700 rounded p-3 text-xs">
            <h3 className="font-bold text-gray-200 mb-2">Execution</h3>
            <p className="text-gray-300">Parser mode: vulnerable XML parse</p>
          </div>
          <div className="bg-gray-900 border border-gray-700 rounded p-3 text-xs">
            <h3 className="font-bold text-gray-200 mb-2">Result</h3>
            <p className={xxeResponseLooksLikeLeak(result) ? 'text-red-300' : 'text-green-300'}>
              {xxeResponseLooksLikeLeak(result) ? 'Response contains data resembling a leaked system file' : 'No obvious system-file fingerprint in parser output'}
            </p>
            <pre className="text-yellow-300 whitespace-pre-wrap">{result.sensitive_data || result.extracted_sensitive_data || 'None'}</pre>
          </div>
          <div className="bg-gray-900 border border-gray-700 rounded p-3 text-xs">
            <h3 className="font-bold text-gray-200 mb-2">Explanation</h3>
            <p className="text-gray-300">
              {xxeResponseLooksLikeLeak(result)
                ? 'Compare parser output to your goal: external resolution often surfaces raw file bytes in the response.'
                : 'Inspect parsed output and entity expansion results above.'}
            </p>
          </div>
        </div>
      )}

      <div className="flex gap-3 mt-6">
        <Link to="/challenges/9/fix" className="bg-green-600 hover:bg-green-700 px-5 py-2 rounded font-bold">Go to Fix</Link>
        <Link to="/challenges" className="bg-gray-600 hover:bg-gray-700 px-5 py-2 rounded font-bold">Back</Link>
      </div>
    </div>
  );
};

export default XxeAttackPage;
