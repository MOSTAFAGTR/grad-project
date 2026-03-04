import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';

const SecurityMiscAttackPage: React.FC = () => {
  const [payload, setPayload] = useState('');
  const [leakedData, setLeakedData] = useState<any>(null);
  const [showErrorPage, setShowErrorPage] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const navigate = useNavigate();

  const handleExploit = async () => {
    setIsLoading(true);
    setErrorMessage('');
    try {
      const res = await axios.get(
        'http://localhost:8000/api/challenges/debug-leak',
        { params: { input: payload } }
      );

      // If backend leaks env/config → exploit success
      if (res.data && res.data.leak) {
        setLeakedData(res.data.leak);
        setShowErrorPage(true);
      } else {
        setErrorMessage('Server responded safely. Try a different payload.');
      }
    } catch (err: any) {
      if (err.response?.data?.detail?.leak) {
        setLeakedData(err.response.data.detail.leak);
        setShowErrorPage(true);
      } else {
        setErrorMessage('No sensitive data leaked. Try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleFinishAttack = async () => {
    try {
      const token = sessionStorage.getItem('token');
      await axios.post(
        'http://localhost:8000/api/challenges/mark-attack-complete?challenge_type=security-misc',
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
    } catch {}
    navigate('/challenges/attack-success');
  };

  if (showErrorPage) {
    return (
      <div className="bg-[#f0f0f0] text-[#333] min-h-screen font-sans p-8 overflow-auto">
        <div className="max-w-5xl mx-auto border-t-8 border-red-600 bg-white shadow-xl p-8 rounded">
          <h1 className="text-4xl font-bold text-red-700 mb-2">ZeroDivisionError</h1>
          <p className="text-xl text-gray-700 mb-6 italic">division by zero</p>

          <div className="bg-gray-100 p-4 border border-gray-300 rounded font-mono text-sm mb-8">
            <p className="font-bold text-blue-800">Traceback (most recent call last):</p>
            <p className="ml-4">File "/usr/local/lib/python3.9/site-packages/flask/app.py", line 2213, in __call__</p>
            <p className="ml-4 text-red-700 font-bold bg-yellow-100 underline">File "/app/app.py", line 42, in trigger_error</p>
            <p className="ml-8 text-red-700">return 1 / 0</p>
          </div>

          <h2 className="text-2xl font-bold border-b-2 border-gray-200 pb-2 mb-4">Environment Variables (Leaked)</h2>
          <div className="grid grid-cols-1 gap-2 mb-8">
            {leakedData && Object.entries(leakedData).map(([key, value]) => (
              <div key={key} className="flex border-b border-gray-100 py-1">
                <span className="font-mono font-bold w-64 text-green-700">{key}:</span>
                <span className="font-mono text-gray-600 truncate">
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </span>
              </div>
            ))}
          </div>

          <div className="flex gap-4">
            <button
              onClick={handleFinishAttack}
              className="bg-red-600 text-white px-6 py-3 rounded font-bold hover:bg-red-700 transition shadow-lg"
            >
              Collect Sensitive Info & End Attack
            </button>
            <button
              onClick={() => setShowErrorPage(false)}
              className="bg-gray-200 text-gray-700 px-6 py-3 rounded font-bold hover:bg-gray-300 transition"
            >
              Go Back
            </button>
          </div>
        </div>

        <p className="text-center mt-6 text-gray-500 italic text-sm">
          Powered by Flask Debugger (Insecure Configuration Detected)
        </p>
      </div>
    );
  }

  return (
    <div className="text-white p-6 max-w-5xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Security Misconfiguration</h1>
          <p className="text-gray-400">Trigger a server error to leak sensitive debug data.</p>
        </div>
        <Link to="/challenges" className="bg-gray-700 px-4 py-2 rounded text-sm hover:bg-gray-600">Back</Link>
      </div>

      <div className="bg-gray-900 border border-gray-700 rounded-lg overflow-hidden mb-8">
        <div className="bg-gray-800 px-4 py-2 border-b border-gray-700 flex gap-2 items-center">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
          <span className="ml-4 font-mono text-xs text-gray-400 italic">
            http://admin-panel.internal/debug
          </span>
        </div>

        <div className="p-12 text-center">
          <h2 className="text-2xl font-bold mb-4">Production Management Console</h2>
          <p className="text-gray-500 mb-6 max-w-md mx-auto">
            Enter malformed input to test error handling. If debug mode is enabled,
            sensitive info will be exposed.
          </p>

          <input
            type="text"
            value={payload}
            onChange={(e) => setPayload(e.target.value)}
            placeholder="Try: 1/0"
            className="bg-gray-700 border border-gray-600 text-white rounded w-full max-w-md p-3 mb-4 font-mono"
          />

          <button
            onClick={handleExploit}
            disabled={isLoading}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded shadow-xl transition transform hover:scale-105 active:scale-95 disabled:opacity-50"
          >
            {isLoading ? 'SENDING...' : 'SEND PAYLOAD'}
          </button>

          {errorMessage && (
            <p className="mt-4 text-red-400 font-bold">{errorMessage}</p>
          )}
        </div>
      </div>

      <div className="bg-blue-900/10 border border-blue-800/50 p-6 rounded-lg text-blue-200">
        <h3 className="font-bold mb-2 text-blue-400">Attack Strategy</h3>
        <p className="text-sm">
          Servers running in <b>debug mode</b> reveal stack traces and environment variables.
          Triggering an exception can expose secrets like <code>SECRET_KEY</code> or <code>DB_PASSWORD</code>.
        </p>
      </div>
    </div>
  );
};

export default SecurityMiscAttackPage;
