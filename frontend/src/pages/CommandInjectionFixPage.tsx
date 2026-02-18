import * as React from 'react';
import { useState } from 'react';
import Editor from '@monaco-editor/react';
import axios from 'axios';
import ResultModal from '../components/ResultModal';
import { Link } from 'react-router-dom';

const VULNERABLE_CODE = `import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "8.8.8.8"]

@app.route('/ping', methods=['POST'])
def ping():
    data = request.get_json() or {}
    host = data.get("host", "").strip()
    if not host:
        return jsonify({"output": "Missing 'host'", "error": True}), 400

    # !!! VULNERABLE: user input passed to shell !!!
    # TODO: 1. Check host is in ALLOWED_HOSTS (else return 400)
    # TODO: 2. Run ping without shell: subprocess.run(["ping", "-c", "1", host], shell=False, ...)
    try:
        cmd = f"ping -c 1 {host}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        output = (result.stdout or "") + (result.stderr or "")
        return jsonify({"output": output})
    except subprocess.TimeoutExpired:
        return jsonify({"output": "Timeout", "error": True}), 400
    except Exception as e:
        return jsonify({"output": str(e), "error": True}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
`;

const CommandInjectionFixPage: React.FC = () => {
  const [code, setCode] = useState(VULNERABLE_CODE);
  const [isLoading, setIsLoading] = useState(false);
  const [modalState, setModalState] = useState({ isOpen: false, isSuccess: false, logs: '' });

  const handleSubmit = async () => {
    setIsLoading(true);
    try {
      const token = sessionStorage.getItem('token');
      if (!token) {
        alert('Please login.');
        setIsLoading(false);
        return;
      }
      const response = await axios.post(
        'http://localhost:8000/api/challenges/submit-fix-command-injection',
        { code },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setModalState({
        isOpen: true,
        isSuccess: response.data.success,
        logs: response.data.logs
      });
    } catch (error: unknown) {
      const ax = error as { response?: { data?: { detail?: string } } };
      setModalState({
        isOpen: true,
        isSuccess: false,
        logs: ax.response?.data?.detail || 'System Error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="text-white h-full flex flex-col">
      <h1 className="text-3xl font-bold mb-4">Command Injection: Fix Challenge</h1>
      <p className="text-gray-400 mb-4">
        Restrict <code>/ping</code> to <strong>allowlist</strong> <code>ALLOWED_HOSTS</code> and run <code>ping</code> with <strong>subprocess without shell</strong> (list of args, <code>shell=False</code>). Reject disallowed hosts with 400.
      </p>

      <div className="flex-grow mb-4 border-2 border-gray-700 rounded-lg overflow-hidden">
        <Editor
          height="60vh"
          language="python"
          theme="vs-dark"
          value={code}
          onChange={(v: string | undefined) => setCode(v || '')}
        />
      </div>

      <div className="flex gap-4 items-center">
        <button
          onClick={handleSubmit}
          disabled={isLoading}
          className="bg-purple-600 w-48 py-3 rounded font-bold hover:bg-purple-700 transition flex justify-center items-center gap-2"
        >
          {isLoading ? <span className="animate-spin">↻</span> : 'Submit Fix'}
        </button>
        <Link to="/challenges" className="bg-gray-600 hover:bg-gray-700 px-6 py-3 rounded font-bold">
          Back to Challenges
        </Link>
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

export default CommandInjectionFixPage;
