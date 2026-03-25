import * as React from 'react';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Account {
  username: string;
  balance: number;
}

interface HintEntry {
  id: number;
  text: string;
  unlocked: boolean;
}

const CsrfAttackPage: React.FC = () => {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [payload, setPayload] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const [message, setMessage] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [hints, setHints] = useState<HintEntry[]>([]);
  const navigate = useNavigate();

  const fetchAccounts = async () => {
    try {
      const res = await axios.get<Account[]>(`${API_URL}/api/challenges/csrf/accounts`);
      setAccounts(res.data);
    } catch (error) {
      console.error(error);
    }
  };

  const loadHints = async () => {
    try {
      const token = sessionStorage.getItem('token');
      if (!token) return;
      const res = await axios.get<HintEntry[]>(`${API_URL}/api/challenges/hints`, {
        params: { challenge_id: 'csrf' },
        headers: { Authorization: `Bearer ${token}` },
      });
      setHints(res.data);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    axios.post(`${API_URL}/api/challenges/csrf/reset`).then(fetchAccounts);
    loadHints();
  }, []);

  const appendLog = (line: string) => {
    setLogs(prev => [...prev, line]);
  };

  const handleExecute = async () => {
    setIsExecuting(true);
    setMessage('');
    appendLog('Sending payload into malicious iframe...');

    const beforeAlice = accounts.find(a => a.username === 'Alice');
    const beforeBalance = beforeAlice?.balance ?? 0;

    const iframe = document.createElement('iframe');
    iframe.style.display = 'none';
    document.body.appendChild(iframe);

    const doc = iframe.contentDocument || iframe.contentWindow?.document;
    if (!doc) {
      appendLog('Failed to obtain iframe document.');
      setIsExecuting(false);
      return;
    }

    doc.open();
    doc.write(payload);
    doc.close();
    appendLog('Payload written. Waiting for CSRF request to fire...');

    setTimeout(async () => {
      // Fetch fresh account data and also update local state
      try {
        const res = await axios.get<Account[]>(`${API_URL}/api/challenges/csrf/accounts`);
        setAccounts(res.data);
        const freshAlice = res.data.find(a => a.username === 'Alice');
        const afterBalance = freshAlice?.balance ?? beforeBalance;

        appendLog(`Before balance: $${beforeBalance}. After balance: $${afterBalance}.`);

        if (afterBalance < beforeBalance) {
          appendLog('Exploit successful. Balance decreased via CSRF.');
          const token = sessionStorage.getItem('token');
          if (token) {
            try {
              await axios.post(
                `${API_URL}/api/challenges/mark-attack-complete`,
                {},
                {
                  params: { challenge_type: 'csrf' },
                  headers: { Authorization: `Bearer ${token}` },
                },
              );
              await axios.post(
                `${API_URL}/api/challenges/state/update`,
                {
                  challenge_id: 'csrf',
                  current_stage: 'attack-complete',
                  attempt_delta: 1,
                },
                { headers: { Authorization: `Bearer ${token}` } },
              );
            } catch {
              // ignore
            }
          }
          document.body.removeChild(iframe);
          navigate('/challenges/attack-success?type=csrf');
        } else {
          appendLog('Exploit failed. No change in victim balance.');
          setMessage('Exploit did not work. Try again with a different payload.');
          setIsExecuting(false);
          document.body.removeChild(iframe);
        }
      } catch {
        appendLog('Error fetching updated account balances.');
        setIsExecuting(false);
        document.body.removeChild(iframe);
      }
    }, 1500);
  };

  const handleUseHint = async () => {
    try {
      const token = sessionStorage.getItem('token');
      if (!token) return;
      // Use next locked hint (or last)
      const locked = hints.find(h => !h.unlocked);
      const target = locked ?? hints[hints.length - 1];
      if (!target) return;
      await axios.post(
        `${API_URL}/api/challenges/hints/use`,
        { challenge_id: 'csrf', hint_id: target.id },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      loadHints();
    } catch {
      // ignore
    }
  };

  const alice = accounts.find(a => a.username === 'Alice');

  return (
    <div className="text-white p-6 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">CSRF Bank Transfer Challenge</h1>
      <p className="text-gray-400 mb-6">
        Use Cross-Site Request Forgery to drain funds from the victim&apos;s account by abusing the vulnerable transfer endpoint.
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Victim Bank */}
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-xl font-bold text-blue-400">Victim Online Banking</h2>
              <p className="text-xs text-gray-500">Authenticated session (John Doe)</p>
            </div>
            <Link to="/challenges" className="text-xs text-gray-400 hover:text-gray-200">
              Back to challenges
            </Link>
          </div>

          <div className="bg-gray-800 p-4 rounded mb-4">
            <p className="text-sm text-gray-300 mb-1">
              <span className="font-semibold">Account Holder:</span> John Doe
            </p>
            <p className="text-sm text-gray-300 mb-1">
              <span className="font-semibold">Account Number:</span> 44739211
            </p>
            <p className="text-lg font-semibold mt-2">
              Balance:{' '}
              <span className="text-green-400">
                ${alice?.balance ?? 5000}
              </span>
            </p>
          </div>

          <div className="bg-gray-800 p-4 rounded">
            <h3 className="text-sm font-bold text-blue-300 mb-2">Accounts Database</h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              {accounts.map(acc => (
                <div key={acc.username} className="bg-gray-900 p-2 rounded flex justify-between">
                  <span>{acc.username}</span>
                  <span className={acc.username === 'Alice' ? 'text-green-400' : 'text-red-400'}>
                    ${acc.balance}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Malicious Site */}
        <div className="bg-gray-900 border border-red-700 rounded-lg p-4">
          <h2 className="text-xl font-bold text-red-400 mb-2">Malicious Promo Site</h2>
          <p className="text-xs text-gray-400 mb-4">
            The victim visits this page while logged in to the bank. Your payload must silently submit a request to the bank&apos;s
            <code className="ml-1">/api/challenges/csrf/transfer</code> endpoint.
          </p>

          <div className="bg-red-900/30 border border-red-700 rounded mb-4 p-4 text-center">
            <div className="text-2xl font-extrabold mb-2">YOU WON $1000!</div>
            <button
              className="px-6 py-2 rounded bg-yellow-400 text-black font-bold shadow hover:bg-yellow-300"
              onClick={handleExecute}
              disabled={isExecuting}
            >
              {isExecuting ? 'RUNNING ATTACK...' : 'CLICK TO CLAIM'}
            </button>
          </div>

          <div className="mb-3">
            <h3 className="text-sm font-bold text-gray-200 mb-1">Exploit HTML / JS Payload</h3>
            <p className="text-xs text-gray-400 mb-2">
              Example:
              <code className="block mt-1 text-[10px] text-yellow-300 whitespace-pre-wrap">
{`<form action="${API_URL}/api/challenges/csrf/transfer" method="POST">
  <input type="hidden" name="to_user" value="Bob">
  <input type="hidden" name="amount" value="1000">
</form>
<script>document.forms[0].submit()</script>`}
              </code>
            </p>
            <textarea
              value={payload}
              onChange={e => setPayload(e.target.value)}
              className="w-full h-40 bg-black text-green-400 font-mono text-xs p-3 rounded border border-gray-600"
              placeholder="Write your malicious HTML/JS here..."
            />
          </div>

          {/* Hints */}
          <div className="mt-3 bg-gray-800 border border-gray-700 rounded p-3">
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
      </div>

      {/* Attack logs */}
      <div className="bg-black border border-green-800 rounded-lg p-4 font-mono text-xs h-40 overflow-y-auto">
        <div className="text-green-500 mb-1 border-b border-green-800 pb-1">
          Attack Logs — CSRF Bank Transfer
        </div>
        {logs.length === 0 && <div className="text-gray-600">No attacks executed yet.</div>}
        {logs.map((line, idx) => (
          <div key={idx} className="text-green-400">
            {line}
          </div>
        ))}
      </div>

      {message && <p className="mt-3 text-yellow-400 text-sm">{message}</p>}
    </div>
  );
};

export default CsrfAttackPage;
