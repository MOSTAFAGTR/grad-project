import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Account {
  username: string;
  balance: number;
}

const CsrfAttackPage: React.FC = () => {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [payload, setPayload] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  const fetchAccounts = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/challenges/csrf/accounts');
      setAccounts(res.data);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    axios.post('http://localhost:8000/api/challenges/csrf/reset')
      .then(fetchAccounts);
  }, []);

  const handleExecute = () => {
    setMessage('Executing malicious page...');

    const iframe = document.createElement('iframe');
    iframe.style.display = 'none';
    document.body.appendChild(iframe);

    const doc = iframe.contentDocument || iframe.contentWindow?.document;
    if (!doc) return;

    doc.open();
    doc.write(payload);
    doc.close();

    setTimeout(() => {
      fetchAccounts();

      // VERY BASIC DETECTION: did Alice lose money?
      const alice = accounts.find(a => a.username === 'Alice');
      if (alice && alice.balance < 1000) {
        const token = sessionStorage.getItem('token');
        if (token) {
          axios.post(`${API_URL}/api/challenges/mark-attack-complete?challenge_type=csrf`, {}, { headers: { Authorization: `Bearer ${token}` } }).catch(() => {});
        }
        navigate('/challenges/attack-success?type=csrf');
      } else {
        setMessage('Exploit did not work. Try again.');
      }

      document.body.removeChild(iframe);
    }, 1500);
  };

  return (
    <div className="text-white p-6 max-w-5xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">CSRF Attack Challenge</h1>
      <p className="text-gray-400 mb-4">
        Write a malicious HTML page that transfers money from Alice to Bob.
      </p>

      {/* Bank State */}
      <div className="bg-gray-800 p-4 rounded-lg mb-6 border border-gray-700">
        <h2 className="text-lg font-bold mb-2 text-blue-400">Bank Database</h2>
        <div className="grid grid-cols-2 gap-4">
          {accounts.map(acc => (
            <div key={acc.username} className="bg-gray-700 p-3 rounded flex justify-between">
              <span>{acc.username}</span>
              <span className={acc.username === 'Alice' ? 'text-green-400' : 'text-red-400'}>
                ${acc.balance}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Exploit Builder */}
      <div className="bg-gray-900 p-6 rounded-lg border border-gray-700 mb-6">
        <h2 className="text-xl font-bold mb-2">Malicious HTML Payload</h2>
        <p className="text-sm text-gray-400 mb-2">
          Try something like:
          <code className="block mt-1 text-xs text-yellow-400">
{`<form action="http://localhost:8000/api/challenges/csrf/transfer" method="POST">
  <input name="to_user" value="Bob">
  <input name="amount" value="100">
</form>
<script>document.forms[0].submit()</script>`}
          </code>
        </p>

        <textarea
          value={payload}
          onChange={(e) => setPayload(e.target.value)}
          className="w-full h-48 bg-black text-green-400 font-mono text-sm p-3 rounded border border-gray-600"
          placeholder="Write your malicious HTML here..."
        />
      </div>

      <div className="flex gap-4">
        <button
          onClick={handleExecute}
          className="bg-red-600 hover:bg-red-700 px-6 py-3 rounded font-bold"
        >
          Execute Payload
        </button>

        <Link to="/challenges" className="bg-gray-600 hover:bg-gray-700 px-6 py-3 rounded font-bold">
          Cancel
        </Link>
      </div>

      {message && <p className="mt-4 text-yellow-400">{message}</p>}
    </div>
  );
};

export default CsrfAttackPage;
