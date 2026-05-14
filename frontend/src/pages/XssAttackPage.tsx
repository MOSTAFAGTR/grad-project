import * as React from 'react';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { Link, useNavigate } from 'react-router-dom';
import ChallengeHintPanel from '../components/ChallengeHintPanel';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Comment {
  id: number;
  author: string;
  content: string;
}

declare global {
  interface Window {
    __xssChallengeDetected?: boolean;
  }
}

const XssAttackPage: React.FC = () => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [author, setAuthor] = useState('Guest');
  const [message, setMessage] = useState('');
  const [isNavigating, setIsNavigating] = useState(false);
  
  const navigate = useNavigate();

  const markAttackSuccess = async () => {
    if (isNavigating || window.__xssChallengeDetected) return;
    window.__xssChallengeDetected = true;
    setIsNavigating(true);
    const token = sessionStorage.getItem('token');
    if (token) {
      await axios
        .post(
          `${API_URL}/api/challenges/mark-attack-complete?challenge_type=xss`,
          {},
          { headers: { Authorization: `Bearer ${token}` } },
        )
        .catch(() => {});
    }
    navigate('/challenges/attack-success?type=xss');
  };

  const fetchComments = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/challenges/xss/comments`);
      setComments(res.data);
    } catch (err) {
      console.error("Failed to load comments");
    }
  };

  useEffect(() => {
    window.__xssChallengeDetected = false;
    fetchComments();
    const onMessage = (event: MessageEvent) => {
      if (event.data && typeof event.data === 'object' && event.data.type === 'xss-executed') {
        markAttackSuccess().catch(() => {});
      }
    };
    window.addEventListener('message', onMessage);
    return () => {
      window.removeEventListener('message', onMessage);
      window.__xssChallengeDetected = false;
    };
  }, []);

  const handlePost = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/api/challenges/xss/comments`, {
        author: author,
        content: newComment
      });
      setNewComment('');
      fetchComments();
      setMessage('Comment posted. If payload executes in the sandbox view, challenge will auto-complete.');
    } catch (err) {
      setMessage('Error posting comment.');
    }
  };

  const handleClear = async () => {
    await axios.delete(`${API_URL}/api/challenges/xss/comments`);
    fetchComments();
    setMessage('Comments cleared.');
  };

  const escapeHtml = (raw: string): string =>
    raw
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');

  const iframeDoc = `<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    body { background:#111827; color:#e5e7eb; font-family: ui-sans-serif, system-ui; margin:0; padding:16px; }
    .comment { background:#1f2937; border:1px solid #374151; border-radius:8px; padding:12px; margin-bottom:10px; }
    .author { color:#93c5fd; font-weight:700; margin-bottom:6px; font-size:12px; }
  </style>
</head>
<body>
  ${comments
    .map(
      (c) => `<div class="comment">
  <div class="author">${escapeHtml(c.author)} says:</div>
  <div>${c.content}</div>
</div>`,
    )
    .join('')}
  <script>
    (function() {
      const notify = (source, detail) => {
        try { parent.postMessage({ type: 'xss-executed', source, detail }, '*'); } catch (e) {}
      };
      const originalAlert = window.alert;
      window.alert = function(msg) {
        notify('alert', String(msg || ''));
        if (typeof originalAlert === 'function') { try { originalAlert(msg); } catch (e) {} }
      };
      window.__xssChallengeSuccess = function(detail) {
        notify('callback', String(detail || ''));
      };
      window.onerror = function(message) {
        notify('onerror', String(message || ''));
        return false;
      };
    })();
  </script>
</body>
</html>`;

  return (
    <div className="text-white p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">Reflected/Stored XSS Challenge</h1>
      <p className="text-gray-400 mb-6">
        This blog post has no security. If you post a script tag, it will execute.
      </p>

      {/* Fake Blog Post */}
      <div className="bg-gray-800 p-6 rounded-lg mb-8 border border-gray-700">
        <h2 className="text-2xl font-bold text-blue-400">Welcome to the Community!</h2>
        <p className="mt-2 text-gray-300">
          We are excited to announce the launch of our new platform. Please leave your feedback below!
        </p>
      </div>

      {/* Comment Form */}
      <div className="bg-gray-900 p-6 rounded-lg border border-gray-700 mb-8">
        <h3 className="text-xl font-bold mb-4">Leave a Comment</h3>
        <form onSubmit={handlePost}>
          <div className="mb-4">
             <label className="block text-sm font-bold mb-2">Name</label>
             <input 
                type="text" 
                value={author} 
                onChange={(e) => setAuthor(e.target.value)}
                className="bg-gray-700 border border-gray-600 text-white rounded w-full p-2"
             />
          </div>
          <div className="mb-4">
            <label className="block text-sm font-bold mb-2">Comment</label>
            <div className="text-xs text-gray-500 mb-2">Try: <code>&lt;img src=x onerror=&quot;window.__xssChallengeSuccess('owned')&quot;&gt;</code></div>
            <textarea
              className="bg-gray-700 border border-gray-600 text-white rounded w-full p-2 h-24 font-mono text-sm"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Enter your message..."
            />
          </div>
          <div className="flex justify-between items-center">
            <button type="submit" className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded font-bold">
              Post Comment
            </button>
            <button type="button" onClick={handleClear} className="text-red-400 hover:text-red-300 text-sm">
              Reset/Clear All
            </button>
          </div>
        </form>
        {message && <p className="mt-2 text-sm text-green-400">{message}</p>}
      </div>

      {/* Vulnerable Comments Section */}
      <div className="space-y-4">
        <h3 className="text-2xl font-bold">Sandboxed Vulnerable Render ({comments.length})</h3>
        <p className="text-gray-400 text-sm">
          Comments are rendered unsafely inside a sandboxed iframe. Payload execution is real, but isolated from platform session storage.
        </p>
        <iframe
          title="xss-sandbox"
          sandbox="allow-scripts allow-forms"
          srcDoc={iframeDoc}
          className="w-full h-80 rounded border border-gray-700 bg-gray-900"
        />
      </div>
      <ChallengeHintPanel challengeId="xss" />
      
      <div className="mt-8">
         <Link to="/challenges" className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded">
            Back to Challenges
         </Link>
      </div>
    </div>
  );
};

export default XssAttackPage;