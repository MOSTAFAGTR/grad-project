import * as React from 'react';
import { useState } from 'react';
import Editor from '@monaco-editor/react';
import axios from 'axios';
import ResultModal from '../components/ResultModal';
import { Link } from 'react-router-dom';
import { API_BASE_URL } from '../lib/api';

const VULNERABLE_CODE = `from flask import Flask, request, redirect

app = Flask(__name__)

# Allowed relative paths (you must restrict redirects to this allowlist)
ALLOWED_PATHS = ['/dashboard', '/profile', '/settings', '/home']

@app.route('/go')
def go():
    """
    Redirects the user based on 'next' or 'url' query parameter.
    VULNERABILITY: No validation - any URL is accepted (open redirect).
    FIX: Validate the target URL against an allowlist (e.g. same-origin relative paths only).
    """
    target = request.args.get('next') or request.args.get('url') or '/'
    # !!! VULNERABLE: redirecting to user-controlled URL without validation !!!
    # TODO: Allow only relative paths that are in ALLOWED_PATHS. Reject absolute URLs and unknown paths with 400.
    return redirect(target, code=302)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
`;

const RedirectFixPage: React.FC = () => {
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
        `${API_BASE_URL}/api/challenges/submit-fix-redirect`,
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
        logs: error.response?.data?.detail || 'System Error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="text-white h-full flex flex-col">
      <h1 className="text-3xl font-bold mb-4">Unvalidated Redirect: Fix Challenge</h1>
      <p className="text-gray-400 mb-4">
        Restrict the <code>/go</code> endpoint so it only redirects to <strong>relative paths</strong> listed in <code>ALLOWED_PATHS</code>.
        Reject absolute URLs (e.g. <code>https://evil.com</code>) and protocol-relative URLs (e.g. <code>//evil.com</code>) with <code>400</code> or <code>403</code>.
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
          className="bg-teal-600 w-48 py-3 rounded font-bold hover:bg-teal-700 transition flex justify-center items-center gap-2"
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

export default RedirectFixPage;
