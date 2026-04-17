import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import axios from 'axios';
import ResultModal from '../components/ResultModal';
import ChallengeHintPanel from '../components/ChallengeHintPanel';
import { API_BASE_URL } from '../lib/api';

const VULNERABLE_CODE = `from flask import Flask, request, jsonify

app = Flask(__name__)

# !!! VULNERABILITY 1: Debug Mode Leaks Info !!!
# Change this to False for production
app.config['DEBUG'] = True

# !!! VULNERABILITY 2: Default Credentials !!!
# Change the password to something secure
ADMIN_PASS = "admin"

@app.route('/login', methods=['POST'])
def login():
    p = request.json.get('password')
    if p == ADMIN_PASS:
        return jsonify({"message": "Welcome Admin"}), 200
    return jsonify({"error": "Bad creds"}), 401

@app.route('/crash')
def trigger_error():
    return 1 / 0

if __name__ == '__main__':
    # Ensure debug is disabled here too
    app.run(host='0.0.0.0', port=5000, debug=True)
`;

const SecurityMiscFixPage: React.FC = () => {
  const [code, setCode] = useState(VULNERABLE_CODE);
  const [isLoading, setIsLoading] = useState(false);
  const [modalState, setModalState] = useState({ isOpen: false, isSuccess: false, logs: '' });

  const handleSubmit = async () => {
    setIsLoading(true);
    try {
      const token = sessionStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE_URL}/api/challenges/submit-fix-misc`,
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
      <h1 className="text-3xl font-bold mb-4">Security Misconfiguration: Fix Challenge</h1>
      <p className="text-gray-400 mb-6">
        Secure the app by disabling <b>Debug Mode</b> and changing the <b>Default Password</b>.
      </p>
      
      <div className="flex-grow mb-6 border-2 border-gray-700 rounded-lg overflow-hidden shadow-lg">
        <Editor height="60vh" language="python" theme="vs-dark" value={code} onChange={(v) => setCode(v || '')} />
      </div>

      <button onClick={handleSubmit} disabled={isLoading} className="bg-green-600 px-8 py-3 rounded font-bold hover:bg-green-700 transition flex items-center gap-2 w-fit">
        {isLoading ? <span className="animate-spin">↻</span> : 'Submit Fix'}
      </button>

      <div className="mt-6">
        <ChallengeHintPanel challengeId="security-misc" />
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

export default SecurityMiscFixPage;