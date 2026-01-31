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
      const response = await axios.post('http://localhost:8000/api/auth/login', {
        username: email, 
        password: password
      });

      const { access_token, role, user_id } = response.data;
      
      if (access_token) {
        // --- FIX: USE SESSION STORAGE FOR TAB ISOLATION ---
        sessionStorage.setItem('token', access_token);
        sessionStorage.setItem('role', role);
        sessionStorage.setItem('user_id', user_id);
        
        // Dynamic Redirection
        if (role === 'admin') {
          navigate('/admin/stats');
        } else if (role === 'instructor') {
          navigate('/instructor/dashboard');
        } else {
          navigate('/home');
        }

      } else {
        setError('Login failed: No token received.');
      }

    } catch (err: any) {
      if (err.response) {
        setError(err.response.data.detail || 'Invalid credentials');
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
              className="w-full p-2.5 bg-gray-700 border border-gray-600 rounded text-white focus:border-blue-500 outline-none"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="user@example.com"
            />
          </div>

          <div className="relative">
            <label className="block mb-1 text-sm font-medium text-gray-300">Password</label>
            <input
              type={isPasswordVisible ? "text" : "password"}
              className="w-full p-2.5 bg-gray-700 border border-gray-600 rounded text-white focus:border-blue-500 outline-none pr-10"
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