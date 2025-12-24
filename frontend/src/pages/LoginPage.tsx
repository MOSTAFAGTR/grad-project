import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { FaEye, FaEyeSlash } from 'react-icons/fa';

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      // NOTE: Backend Schema expects 'username', but we treat it as email.
      // We must send the keys exactly as { username, password }
      const response = await axios.post('http://localhost:8000/api/auth/login', {
        username: email, 
        password: password
      });

      console.log("Login Response:", response.data);

      // --- CRITICAL FIX ---
      // The Backend returns 'access_token', NOT 'token'.
      const token = response.data.access_token;
      
      if (token) {
        // Save to storage
        localStorage.setItem('token', token);
        
        // Optional: Save user info if your backend sends it
        if (response.data.user_id) {
            localStorage.setItem('user_id', response.data.user_id);
        }
        
        // Redirect
        navigate('/dashboard');
      } else {
        setError('Login failed: No token received from server.');
      }

    } catch (err: any) {
      console.error("Login Error:", err);
      
      // Prevent Crash on Error
      if (err.response) {
        // Backend returned an error (401, 422, etc)
        const detail = err.response.data.detail;
        if (typeof detail === 'string') {
            setError(detail);
        } else if (Array.isArray(detail)) {
            // Pydantic validation error array
            setError(detail[0].msg);
        } else {
            setError('Invalid credentials');
        }
      } else if (err.request) {
        setError('Server not responding. Is Backend running?');
      } else {
        setError('An unexpected error occurred.');
      }
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-900 text-white">
      <div className="w-full max-w-md p-8 space-y-6 bg-gray-800 rounded-lg shadow-lg border border-gray-700">
        <h2 className="text-3xl font-bold text-center text-blue-400">Login</h2>
        
        {error && (
          <div className="p-3 text-sm text-red-200 bg-red-900/50 border border-red-500 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block mb-1 text-sm font-medium text-gray-300">Email Address</label>
            <input
              type="email"
              className="w-full p-2.5 bg-gray-700 border border-gray-600 rounded text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="admin@example.com"
            />
          </div>

          <div className="relative">
            <label className="block mb-1 text-sm font-medium text-gray-300">Password</label>
            <input
              type={isPasswordVisible ? "text" : "password"}
              className="w-full p-2.5 bg-gray-700 border border-gray-600 rounded text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none pr-10"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 pt-6 pr-3 flex items-center text-gray-400 hover:text-white"
              onClick={() => setIsPasswordVisible(!isPasswordVisible)}
            >
              {isPasswordVisible ? <FaEyeSlash /> : <FaEye />}
            </button>
          </div>

          <button
            type="submit"
            className="w-full py-2.5 font-bold text-white bg-blue-600 rounded hover:bg-blue-700 transition duration-200"
          >
            Sign In
          </button>
        </form>

        <p className="text-sm text-center text-gray-400">
          Don't have an account?{' '}
          <Link to="/register" className="text-blue-400 hover:underline">
            Register here
          </Link>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;