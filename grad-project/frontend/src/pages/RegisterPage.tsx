import * as React from 'react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function getApiErrorMessage(err: unknown): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const res = (err as { response?: { data?: { detail?: unknown } } }).response;
    const detail = res?.data?.detail;
    if (Array.isArray(detail)) {
      return detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join(' ');
    }
    if (typeof detail === 'string') return detail;
    if (detail != null) return String(detail);
  }
  if (err && typeof err === 'object' && 'request' in err) return 'Server not responding. Is the backend running on ' + API_URL + '?';
  return 'Registration failed.';
}

const RegisterPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('user');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email?.trim() || !password || !confirmPassword) return setError('Please fill in all fields.');
    if (password !== confirmPassword) return setError('Passwords do not match.');

    try {
      await axios.post(`${API_URL}/api/auth/register`, {
        email: email.trim(),
        password,
        role
      });
      if (role === 'instructor') {
        alert('Registration successful! Your account is PENDING approval. You cannot log in until an Admin approves it.');
      } else {
        alert('Registration successful! You can log in now.');
      }
      navigate('/login');
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white">
      <div className="bg-gray-800 p-8 rounded-lg shadow-lg border border-gray-700 w-full max-w-md">
        <h2 className="text-3xl font-bold text-center mb-6 text-blue-400">Join SCALE</h2>
        
        {error && <div className="bg-red-900/50 border border-red-500 text-red-200 p-3 rounded mb-4 text-sm">{error}</div>}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
            <input className="w-full bg-gray-700 border border-gray-600 rounded p-2 focus:border-blue-500 outline-none" 
              type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Password</label>
            <input className="w-full bg-gray-700 border border-gray-600 rounded p-2 focus:border-blue-500 outline-none" 
              type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Confirm Password</label>
            <input className="w-full bg-gray-700 border border-gray-600 rounded p-2 focus:border-blue-500 outline-none" 
              type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Register as</label>
            <select className="w-full bg-gray-700 border border-gray-600 rounded p-2 focus:border-blue-500 outline-none"
              value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="user">Student (Instant Access)</option>
              <option value="instructor">Instructor (Requires Approval)</option>
            </select>
          </div>

          <button className="w-full bg-blue-600 hover:bg-blue-700 font-bold py-2 rounded transition" type="submit">
            Create Account
          </button>
        </form>

        <p className="text-center mt-4 text-gray-400 text-sm">
          Already have an account? <Link to="/login" className="text-blue-400 hover:underline">Login</Link>
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;