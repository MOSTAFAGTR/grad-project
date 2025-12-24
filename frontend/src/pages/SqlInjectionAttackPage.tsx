import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { FaEye, FaEyeSlash } from 'react-icons/fa';

const SqlInjectionAttackPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isPasswordVisible, setIsPasswordVisible] = useState(true);
  const navigate = useNavigate();

  const handleLogin = async () => {
    setError('');
    try {
      // DEBUG: Log what we are sending
      console.log("Sending Login:", { username, password });

      const response = await axios.post('http://localhost:8000/api/challenges/vulnerable-login', { 
        username, 
        password 
      });
      
      console.log("Response:", response);

      if (response.status === 200) {
        navigate('/challenges/attack-success');
      }
    } catch (err: any) {
      console.error("Full Error Object:", err);
      
      // --- ROBUST ERROR HANDLING ---
      if (err.response) {
        // The server returned a specific error (400, 401, 500)
        const data = err.response.data;
        if (data && data.detail) {
           setError(`Server Error: ${JSON.stringify(data.detail)}`);
        } else {
           setError(`Error ${err.response.status}: ${err.response.statusText}`);
        }
      } else if (err.request) {
        // The server did not respond (Network Error)
        setError("Network Error: Backend is not reachable.");
      } else {
        // Code error
        setError(`Client Error: ${err.message}`);
      }
    }
  };

  return (
    <div className="text-white">
      <h1 className="text-3xl font-bold mb-4">SQL Injection Attack</h1>
      <p className="text-gray-400 mb-6">You can log in with the real credentials or by using a SQL injection attack.</p>
      
      <div className="w-full max-w-sm p-6 bg-gray-900 rounded-lg border border-gray-700">
        
        {/* Error Display - RED BOX */}
        {error && (
          <div className="bg-red-900/50 border border-red-500 text-red-200 p-3 rounded mb-4 text-sm break-words">
            <strong>Debug Info:</strong> {error}
          </div>
        )}

        <div className="mb-4">
          <label className="block text-gray-300 text-sm font-bold mb-2">Username</label>
          <input
            className="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg block w-full p-2.5"
            type="text" 
            value={username} 
            onChange={(e) => setUsername(e.target.value)}
            placeholder="admin"
          />
        </div>
        <div className="mb-6 relative">
          <label className="block text-gray-300 text-sm font-bold mb-2">Password</label>
          <input
            className="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg block w-full p-2.5 pr-10"
            type={isPasswordVisible ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button
            type="button"
            onClick={() => setIsPasswordVisible(!isPasswordVisible)}
            className="absolute inset-y-0 right-0 top-7 flex items-center px-3 text-gray-400 hover:text-white"
          >
            {isPasswordVisible ? <FaEyeSlash /> : <FaEye />}
          </button>
        </div>
        <div className="flex items-center justify-between">
          <button onClick={handleLogin} className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
            Login
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