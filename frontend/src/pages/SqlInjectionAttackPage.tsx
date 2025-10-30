import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';

const SqlInjectionAttackPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async () => {
    setError('');
    try {
      const response = await axios.post('http://localhost:8000/api/challenges/vulnerable-login', {
        username,
        password
      });

      if (response.status === 200) {
        navigate('/challenges/attack-success');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An unknown error occurred.');
    }
  };

  return (
    <div className="text-white">
      <h1 className="text-3xl font-bold mb-4">SQL Injection Attack</h1>
      <p className="text-gray-400 mb-6">
        You can log in with the real credentials or by using a SQL injection attack.
      </p>
      
      <div className="w-full max-w-sm p-6 bg-gray-900 rounded-lg border border-gray-700">
        {error && <p className="text-red-500 text-center mb-4">{error}</p>}
        <div className="mb-4">
          <label className="block text-gray-300 text-sm font-bold mb-2" htmlFor="username">
            Username
          </label>
          <input
            className="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg block w-full p-2.5"
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div className="mb-6">
          <label className="block text-gray-300 text-sm font-bold mb-2" htmlFor="password">
            Password
          </label>
          <input
            className="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg block w-full p-2.5"
            id="password"
            // --- THIS IS THE CHANGE ---
            type="text" // Changed from "password" to "text"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <div className="flex items-center justify-between">
          <button
            onClick={handleLogin}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            Ok
          </button>
          <Link to="/challenges" className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded">
            Cancel
          </Link>
        </div>
      </div>
    </div>
  );
};

export default SqlInjectionAttackPage;