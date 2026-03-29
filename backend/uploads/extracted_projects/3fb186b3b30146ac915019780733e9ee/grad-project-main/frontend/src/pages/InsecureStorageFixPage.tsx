import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import axios from 'axios';
import ResultModal from '../components/ResultModal';
import { API_BASE_URL } from '../lib/api';

const VULNERABLE_CODE = `import hashlib
from flask import Flask, jsonify, request

app = Flask(__name__)
USERS = {}

@app.route("/register", methods=["POST"])
def register():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    if not username or not password:
        return jsonify({"error": "username/password required"}), 400

    # VULNERABLE: plaintext password storage
    USERS[username] = {"password": password}
    return jsonify({"ok": True, "username": username}), 200

@app.route("/dump")
def dump_users():
    return jsonify({"users": USERS}), 200
`;

const InsecureStorageFixPage: React.FC = () => {
  const [code, setCode] = useState(VULNERABLE_CODE);
  const [isLoading, setIsLoading] = useState(false);
  const [modalState, setModalState] = useState({
    isOpen: false,
    isSuccess: false,
    logs: '',
    verification: null as null | { before_vulnerabilities?: number; after_vulnerabilities?: number; improvement_score?: number },
  });

  const handleSubmit = async () => {
    setIsLoading(true);
    try {
      const token = sessionStorage.getItem('token');
      if (!token) return;
      const response = await axios.post(
        `${API_BASE_URL}/api/challenges/submit-fix-storage`,
        { code },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      setModalState({
        isOpen: true,
        isSuccess: response.data.success,
        logs: response.data.logs,
        verification: {
          before_vulnerabilities: response.data.before_vulnerabilities,
          after_vulnerabilities: response.data.after_vulnerabilities,
          improvement_score: response.data.improvement_score,
        },
      });
    } catch (error: any) {
      setModalState({
        isOpen: true,
        isSuccess: false,
        logs: error.response?.data?.detail || 'System Error',
        verification: null,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="text-white">
      <h1 className="text-3xl font-bold mb-4">Insecure Storage: Fix Challenge</h1>
      <p className="text-gray-400 mb-6">Replace plaintext password storage with hashing.</p>
      <div className="h-96 mb-6 border-2 border-gray-700 rounded-lg overflow-hidden shadow-lg">
        <Editor height="100%" language="python" theme="vs-dark" value={code} onChange={(v) => setCode(v || '')} />
      </div>
      <button onClick={handleSubmit} disabled={isLoading} className="bg-green-600 px-8 py-3 rounded font-bold hover:bg-green-700 transition disabled:opacity-50">
        {isLoading ? 'Running Tests...' : 'Submit Fix'}
      </button>
      <ResultModal
        isOpen={modalState.isOpen}
        isSuccess={modalState.isSuccess}
        logs={modalState.logs}
        verification={modalState.verification}
        onClose={() => setModalState({ ...modalState, isOpen: false })}
      />
    </div>
  );
};

export default InsecureStorageFixPage;
