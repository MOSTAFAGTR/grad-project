import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import axios from 'axios';
import ResultModal from '../components/ResultModal';

const VULNERABLE_CODE = `from flask import Flask, request, render_template_string
import html

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    comments = [] 
    if request.method == 'POST':
        content = request.form.get('content', '')
        comments.append(content)

    comments_html = ""
    for c in comments:
        # !!! VULNERABLE CODE !!!
        comments_html += f"<div class='comment'>{c}</div>"

    template = f"""
    <!doctype html>
    <html><body><h1>Comments</h1><div>{comments_html}</div></body></html>
    """
    return render_template_string(template)
`;

const XssFixPage: React.FC = () => {
  const [code, setCode] = useState(VULNERABLE_CODE);
  const [isLoading, setIsLoading] = useState(false);
  const [modalState, setModalState] = useState({ isOpen: false, isSuccess: false, logs: '' });

  const handleSubmit = async () => {
    setIsLoading(true);
    try {
      const token = sessionStorage.getItem('token');
      if (!token) { alert("Please login."); setIsLoading(false); return; }

      const response = await axios.post(
        'http://localhost:8000/api/challenges/submit-fix-xss',
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
        logs: error.response?.data?.detail || "System Error."
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="text-white">
      <h1 className="text-3xl font-bold mb-4">XSS: Fix Challenge</h1>
      <p className="text-gray-400 mb-6">Fix this code by using <code>html.escape()</code>.</p>

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

export default XssFixPage;