import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import axios from 'axios';
import ResultModal from '../components/ResultModal';

const VULNERABLE_CODE = `import os
import mysql.connector
from flask import Flask, request, jsonify

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(host="challenge_db_sqli", user="user", password="password", database="testdb")

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # !!! VULNERABLE CODE !!!
    # Fix this query to prevent SQL Injection
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"

    try:
        cursor.execute(query)
        user = cursor.fetchone()
        if user: return jsonify({"message": "Login successful!"}), 200
        else: return jsonify({"message": "Invalid credentials"}), 401
    except Exception as e: return jsonify({"error": str(e)}), 500
    finally: cursor.close(); conn.close()
`;

const SqlInjectionFixPage: React.FC = () => {
  const [code, setCode] = useState(VULNERABLE_CODE);
  const [isLoading, setIsLoading] = useState(false);
  const [modalState, setModalState] = useState({ isOpen: false, isSuccess: false, logs: '' });

  const handleSubmit = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) { alert("Please login."); setIsLoading(false); return; }

      const response = await axios.post(
        'http://localhost:8000/api/challenges/submit-fix', 
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
        logs: error.response?.data?.detail || "System Error: Could not connect to sandbox."
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="text-white">
      <h1 className="text-3xl font-bold mb-4">SQL Injection: Fix Challenge</h1>
      <p className="text-gray-400 mb-6">Modify the code to use parameterized queries.</p>
      
      <div className="h-96 mb-6 border-2 border-gray-700 rounded-lg overflow-hidden shadow-lg">
        <Editor height="100%" language="python" theme="vs-dark" value={code} onChange={(v) => setCode(v || '')} />
      </div>

      <button onClick={handleSubmit} disabled={isLoading} className="bg-green-600 px-8 py-3 rounded font-bold hover:bg-green-700 transition flex items-center gap-2 disabled:opacity-50">
        {isLoading ? <span className="animate-spin">↻</span> : null}
        {isLoading ? 'Running Tests...' : 'Submit Fix'}
      </button>

      <ResultModal 
        isOpen={modalState.isOpen} 
        isSuccess={modalState.isSuccess} 
        logs={modalState.logs} 
        onClose={() => setModalState({ ...modalState, isOpen: false })} 
      />
    </div>
  );
};

export default SqlInjectionFixPage;