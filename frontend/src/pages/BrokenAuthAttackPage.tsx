import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const commonPasswords = ["123456", "password", "qwerty", "admin123", "complex_password_123"];

const BrokenAuthAttackPage: React.FC = () => {
  const [logs, setLogs] = useState<string[]>([]);
  const [isAttacking, setIsAttacking] = useState(false);
  const navigate = useNavigate();

  const startBruteForce = async () => {
    setIsAttacking(true);
    setLogs(["Starting Brute Force Attack on user: admin..."]);

    for (const pwd of commonPasswords) {
      setLogs(prev => [...prev, `Trying password: ${pwd}...`]);
      try {
        // We hit the vulnerable login endpoint (simulate one that has no lockout)
        const res = await axios.post('http://localhost:8000/api/challenges/vulnerable-login', {
          username: 'admin',
          password: pwd
        });

        if (res.status === 200) {
          setLogs(prev => [...prev, `✅ SUCCESS! Password found: ${pwd}`]);
          setTimeout(() => navigate('/challenges/attack-success'), 1500);
          return;
        }
      } catch (err) {
        setLogs(prev => [...prev, `❌ Failed: ${pwd}`]);
      }
      // Artificial delay to make it look like a real console
      await new Promise(r => setTimeout(r, 600));
    }
    setIsAttacking(false);
  };

  return (
    <div className="text-white p-6">
      <h1 className="text-3xl font-bold mb-4">Broken Authentication: Brute Force</h1>
      <p className="text-gray-400 mb-6">Attacker script is attempting to guess the admin password because there is no rate limiting.</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-gray-900 p-6 rounded-lg border border-gray-700">
          <h2 className="text-xl mb-4 text-blue-400">Target: Admin Login</h2>
          <div className="space-y-4 opacity-50 pointer-events-none">
            <input className="w-full p-2 bg-gray-800 rounded border border-gray-600" value="admin" readOnly />
            <input className="w-full p-2 bg-gray-800 rounded border border-gray-600" value="********" readOnly />
            <button className="w-full bg-blue-600 p-2 rounded font-bold">Login</button>
          </div>
          <button 
            onClick={startBruteForce}
            disabled={isAttacking}
            className="mt-8 w-full bg-red-600 hover:bg-red-700 p-3 rounded font-bold transition animate-pulse"
          >
            {isAttacking ? "RUNNING SCRIPT..." : "LAUNCH BRUTE FORCE SCRIPT"}
          </button>
        </div>

        <div className="bg-black p-4 rounded-lg border border-green-900 font-mono text-sm h-80 overflow-y-auto">
          <div className="text-green-500 mb-2 border-b border-green-900 pb-1">kali-linux@attacker:~/exploit$</div>
          {logs.map((log, i) => (
            <div key={i} className="text-green-400">{log}</div>
          ))}
          {isAttacking && <div className="animate-ping inline-block w-2 h-2 bg-green-500 rounded-full ml-1"></div>}
        </div>
      </div>
    </div>
  );
};

export default BrokenAuthAttackPage;