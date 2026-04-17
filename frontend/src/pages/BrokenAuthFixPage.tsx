import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import axios from 'axios';
import ResultModal from '../components/ResultModal';
import ChallengeHintPanel from '../components/ChallengeHintPanel';
import { API_BASE_URL } from '../lib/api';

const VULNERABLE_CODE = `from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# Mock DB
users = {"admin": "complex_password_123"}

# TODO: Use this dictionary to track failed attempts
failed_attempts = {} 

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    # --- FIX START ---
    # 1. Check if the user is locked out (e.g., more than 3 failures)
    # 2. If login fails, increment the counter.
    # 3. If login succeeds, reset the counter.
    # -----------------

    if username in users and users[username] == password:
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
`;

const BrokenAuthFixPage: React.FC = () => {
  const [code, setCode] = useState(VULNERABLE_CODE);
  const [isLoading, setIsLoading] = useState(false);
  const [modalState, setModalState] = useState({ isOpen: false, isSuccess: false, logs: '' });

  const handleSubmit = async () => {
    setIsLoading(true);
    try {
      const token = sessionStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE_URL}/api/challenges/submit-fix-auth`,
        { code }, 
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setModalState({
        isOpen: true,
        isSuccess: response.data.success,
        logs: response.data.logs
      });
    } catch (error: any) {
      setModalState({
        isOpen: true,
        isSuccess: false,
        logs: error.response?.data?.detail || "System Error"
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="text-white h-full flex flex-col">
      <h1 className="text-3xl font-bold mb-4">Broken Authentication: Fix Challenge</h1>
      <p className="text-gray-400 mb-6">
        Implement <b>Rate Limiting</b>. Block the user after 3 failed attempts to prevent brute force.
      </p>
      
      <div className="flex-grow mb-6 border-2 border-gray-700 rounded-lg overflow-hidden shadow-lg">
        <Editor height="60vh" language="python" theme="vs-dark" value={code} onChange={(v) => setCode(v || '')} />
      </div>

      <button onClick={handleSubmit} disabled={isLoading} className="bg-green-600 px-8 py-3 rounded font-bold hover:bg-green-700 transition flex items-center gap-2 w-fit">
        {isLoading ? <span className="animate-spin">↻</span> : 'Submit Fix'}
      </button>

      <div className="mt-6">
        <ChallengeHintPanel challengeId="broken-auth" />
      </div>

      <ResultModal 
        isOpen={modalState.isOpen} 
        isSuccess={modalState.isSuccess} 
        logs={modalState.logs} 
        onClose={() => setModalState({ ...modalState, isOpen: false })} 
      />
    </div>
  );
};

export default BrokenAuthFixPage;