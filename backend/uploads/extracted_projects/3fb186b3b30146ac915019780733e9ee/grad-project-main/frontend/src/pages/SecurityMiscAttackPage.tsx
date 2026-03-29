import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import ChallengeHintPanel from '../components/ChallengeHintPanel';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const SecurityMiscAttackPage: React.FC = () => {
  const [principal, setPrincipal] = useState('5000');
  const [rate, setRate] = useState('5');
  const [years, setYears] = useState('2');
  const [calculated, setCalculated] = useState<number | null>(null);

  const [path, setPath] = useState('/admin/config');
  const [responseBody, setResponseBody] = useState<any>(null);
  const [responseStatus, setResponseStatus] = useState<number | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [isSending, setIsSending] = useState(false);

  const navigate = useNavigate();

  const appendLog = (line: string) => setLogs(prev => [...prev, line]);

  const handleCalc = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = sessionStorage.getItem('token');
      if (!token) return;
      const form = new FormData();
      form.append('principal', principal);
      form.append('interestRate', rate);
      form.append('years', years);
      const res = await axios.post<{ amount: number }>(`${API_URL}/api/calc/interest`, form, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setCalculated(res.data.amount);
    } catch (err: any) {
      appendLog(`Interest calc error: ${err.response?.data?.detail || 'Unknown error'}`);
    }
  };

  const handleSendRequest = async () => {
    setIsSending(true);
    setResponseBody(null);
    setResponseStatus(null);
    const token = sessionStorage.getItem('token');
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    // Always route through the API prefix for this mini-app
    const targetPath = cleanPath.startsWith('/api') ? cleanPath : `/api${cleanPath}`;
    const url = `${API_URL}${targetPath}`;
    appendLog(`Sending GET ${targetPath} ...`);
    try {
      const res = await axios.get(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });
      setResponseStatus(res.status);
      setResponseBody(res.data);
      appendLog(`Response ${res.status}.`);

      // If we hit the exposed admin config, mark challenge complete
      if (targetPath === '/api/admin/config') {
        appendLog('Exposed admin configuration discovered. Challenge complete.');
        if (token) {
          try {
            await axios.post(
              `${API_URL}/api/challenges/mark-attack-complete`,
              {},
              {
                params: { challenge_type: 'security-misc' },
                headers: { Authorization: `Bearer ${token}` },
              },
            );
            await axios.post(
              `${API_URL}/api/challenges/state/update`,
              {
                challenge_id: 'security-misc',
                current_stage: 'admin-config-exposed',
                attempt_delta: 1,
              },
              { headers: { Authorization: `Bearer ${token}` } },
            );
          } catch {
            // ignore
          }
        }
        setTimeout(() => navigate('/challenges/attack-success?type=security-misc'), 1500);
      }
    } catch (err: any) {
      const status = err.response?.status ?? 0;
      setResponseStatus(status);
      setResponseBody(err.response?.data ?? err.message);
      appendLog(`Request failed with status ${status}.`);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="text-white p-6 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Security Misconfiguration Challenge</h1>
          <p className="text-gray-400">
            Use a harmless-looking Bank Interest Calculator to discover exposed admin configuration endpoints.
          </p>
        </div>
        <Link to="/challenges" className="bg-gray-700 px-4 py-2 rounded text-sm hover:bg-gray-600">
          Back
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Bank Interest Calculator */}
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
          <h2 className="text-xl font-bold text-blue-400 mb-4">Bank Interest Calculator</h2>
          <form onSubmit={handleCalc} className="space-y-3">
            <div>
              <label className="block text-sm mb-1">Principal</label>
              <input
                type="number"
                value={principal}
                onChange={e => setPrincipal(e.target.value)}
                className="w-full p-2 bg-gray-800 rounded border border-gray-600"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm mb-1">Interest Rate (%)</label>
                <input
                  type="number"
                  value={rate}
                  onChange={e => setRate(e.target.value)}
                  className="w-full p-2 bg-gray-800 rounded border border-gray-600"
                />
              </div>
              <div>
                <label className="block text-sm mb-1">Years</label>
                <input
                  type="number"
                  value={years}
                  onChange={e => setYears(e.target.value)}
                  className="w-full p-2 bg-gray-800 rounded border border-gray-600"
                />
              </div>
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 p-2 rounded font-bold"
            >
              Calculate Interest
            </button>
          </form>

          {calculated !== null && (
            <div className="mt-4 bg-gray-800 p-3 rounded text-sm">
              <span className="font-semibold">Future value:</span>{' '}
              <span className="text-green-400">${calculated}</span>
            </div>
          )}

          <ChallengeHintPanel challengeId="security-misc" />
        </div>

        {/* Network explorer */}
        <div className="bg-gray-900 border border-red-700 rounded-lg p-4 flex flex-col">
          <h2 className="text-xl font-bold text-red-400 mb-3">Internal Admin API Explorer</h2>
          <p className="text-xs text-gray-400 mb-3">
            The calculator service is deployed with debug and admin endpoints still exposed. Try probing for hidden URLs like{' '}
            <code>/admin/config</code>, <code>/debug</code>, or <code>/.env</code>.
          </p>
          <div className="flex mb-3">
            <span className="px-2 py-1 bg-gray-800 border border-gray-700 rounded-l text-xs text-gray-400 font-mono">
              GET
            </span>
            <input
              type="text"
              value={path}
              onChange={e => setPath(e.target.value)}
              className="flex-1 p-2 bg-gray-800 border-t border-b border-gray-700 text-sm font-mono"
            />
            <button
              onClick={handleSendRequest}
              disabled={isSending}
              className="px-4 bg-red-600 hover:bg-red-700 border border-red-700 rounded-r text-sm font-bold"
            >
              {isSending ? 'SENDING...' : 'SEND'}
            </button>
          </div>

          <div className="flex-1 bg-black border border-gray-800 rounded p-3 font-mono text-xs overflow-y-auto mb-3">
            <div className="text-gray-500 mb-1">Response status: {responseStatus ?? '—'}</div>
            <pre className="text-green-300 whitespace-pre-wrap">
              {responseBody ? JSON.stringify(responseBody, null, 2) : '// No response yet.'}
            </pre>
          </div>

          <div className="bg-black border border-green-800 rounded p-3 font-mono text-xs h-32 overflow-y-auto">
            <div className="text-green-500 mb-1 border-b border-green-800 pb-1">
              Attack Logs — Security Misconfiguration
            </div>
            {logs.length === 0 && <div className="text-gray-600">No probes sent yet.</div>}
            {logs.map((line, idx) => (
              <div key={idx} className="text-green-400">
                {line}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SecurityMiscAttackPage;
