import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import axios from 'axios';
import ResultModal from '../components/ResultModal';
import { API_BASE_URL } from '../lib/api';

const VULNERABLE_CODE = `from pathlib import Path
from flask import Flask, request, jsonify

app = Flask(__name__)
BASE_DIR = Path("files")

@app.route("/file")
def read_file():
    filename = request.args.get("name", "")
    if not filename:
        return jsonify({"error": "name is required"}), 400

    # VULNERABLE: traversal possible
    file_path = BASE_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        return jsonify({"error": "file not found"}), 404

    content = file_path.read_text(encoding="utf-8", errors="ignore")
    return jsonify({"content": content}), 200
`;

const DirectoryTraversalFixPage: React.FC = () => {
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
        `${API_BASE_URL}/api/challenges/submit-fix-traversal`,
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
      <h1 className="text-3xl font-bold mb-4">Directory Traversal: Fix Challenge</h1>
      <p className="text-gray-400 mb-6">Block path traversal using normalization and path validation.</p>
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

export default DirectoryTraversalFixPage;
