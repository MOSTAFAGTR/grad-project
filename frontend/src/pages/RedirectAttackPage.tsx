import * as React from 'react';
import { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_BASE = `${API_URL}/api/challenges`;

const RedirectAttackPage: React.FC = () => {
  const [targetUrl, setTargetUrl] = useState('');
  const [verified, setVerified] = useState<'pending' | 'success' | 'failed'>('pending');
  const [error, setError] = useState('');
  const iframeRef = useRef<HTMLIFrameElement | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const doneRef = useRef(false);
  const navigate = useNavigate();

  const craftedLink = targetUrl.trim()
    ? `${API_BASE}/redirect?url=${encodeURIComponent(targetUrl.trim())}`
    : '';

  const handleVerify = () => {
    setError('');
    setVerified('pending');
    if (!targetUrl.trim()) {
      setError('Please enter a target URL.');
      return;
    }
    if (!craftedLink) return;
    doneRef.current = false;

    const iframe = document.createElement('iframe');
    iframe.style.cssText = 'position:absolute;width:1px;height:1px;border:none;opacity:0;pointer-events:none;';
    iframe.title = 'redirect-test';
    document.body.appendChild(iframe);
    iframeRef.current = iframe;

    const checkResult = () => {
      if (doneRef.current) return;
      doneRef.current = true;
      if (!iframe.parentNode) return;
      try {
        const href = iframe.contentWindow?.location?.href ?? '';
        if (href.includes('attack-success') && href.includes('type=redirect')) {
          setVerified('success');
          const token = sessionStorage.getItem('token');
          if (token) {
            axios.post(`${API_BASE}/mark-attack-complete?challenge_type=redirect`, {}, { headers: { Authorization: `Bearer ${token}` } }).catch(() => {});
          }
          navigate('/challenges/attack-success?type=redirect');
        } else if (href && !href.startsWith(API_BASE)) {
          setVerified('success');
          if (targetUrl.trim().includes('attack-success')) {
            const token = sessionStorage.getItem('token');
            if (token) {
              axios.post(`${API_BASE}/mark-attack-complete?challenge_type=redirect`, {}, { headers: { Authorization: `Bearer ${token}` } }).catch(() => {});
            }
            navigate('/challenges/attack-success?type=redirect');
          }
        } else {
          setVerified('failed');
        }
      } catch {
        setVerified('failed');
      }
      try {
        document.body.removeChild(iframe);
      } catch { /* already removed */ }
      iframeRef.current = null;
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };

    iframe.onload = () => {
      timeoutRef.current = setTimeout(checkResult, 300);
    };
    iframe.src = craftedLink;

    timeoutRef.current = setTimeout(checkResult, 4000);
  };

  const handleOpenLink = () => {
    if (craftedLink) window.open(craftedLink, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="text-white p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">Unvalidated Redirect Attack</h1>
      <p className="text-gray-400 mb-6">
        The app has a redirect endpoint that sends users to any URL in the <code>url</code> parameter.
        Your goal: craft a link that redirects the victim to the Attack Success page.
      </p>

      <div className="bg-gray-800 p-6 rounded-lg mb-6 border border-gray-700">
        <h2 className="text-lg font-bold mb-2 text-teal-400">How to exploit</h2>
        <ul className="text-gray-300 text-sm space-y-1 list-disc list-inside">
          <li>The trusted link format is <code>GET /redirect?url=&lt;target&gt;</code>.</li>
          <li>Replace <code>target</code> with the URL where you want the victim to land (e.g. this app&apos;s Attack Success page).</li>
          <li>The server does not validate the <code>url</code> — it redirects to whatever you supply.</li>
        </ul>
      </div>

      <div className="bg-gray-800 p-6 rounded-lg mb-6 border border-gray-700">
        <h2 className="text-lg font-bold mb-2 text-teal-400">Vulnerable endpoint</h2>
        <code className="text-sm text-gray-300 break-all">GET {API_BASE}/redirect?url=&lt;target_url&gt;</code>
      </div>

      {/* Simulated vulnerable app — trusted link UI */}
      <div className="bg-gray-900 p-6 rounded-lg border-2 border-teal-500/50 mb-6">
        <p className="text-teal-300 text-xs font-semibold mb-3 uppercase tracking-wide">Simulated vulnerable app</p>
        <div className="bg-white rounded-lg p-4 shadow-inner max-w-xl text-gray-800">
          <div className="text-sm font-medium text-gray-600 mb-2">Dashboard</div>
          <p className="text-gray-500 text-sm mb-3">Return to your destination after login.</p>
          <div className="flex gap-2 flex-wrap">
            <input
              type="text"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleVerify()}
              className="flex-1 min-w-[200px] px-3 py-2 bg-gray-100 border border-gray-300 rounded text-sm text-gray-900 placeholder-gray-400"
              placeholder={`${window.location.origin}/challenges/attack-success?type=redirect`}
            />
            <button
              onClick={handleVerify}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold rounded text-sm"
            >
              Verify Redirect
            </button>
            <button
              onClick={handleOpenLink}
              disabled={!craftedLink}
              className="px-4 py-2 bg-gray-500 hover:bg-gray-600 disabled:opacity-50 text-white font-semibold rounded text-sm"
            >
              Open in New Tab
            </button>
          </div>
          {targetUrl && (
            <p className="mt-2 text-xs text-gray-500 font-mono break-all">
              Crafted link: <span className="text-teal-600">{craftedLink}</span>
            </p>
          )}
        </div>
      </div>

      {verified === 'success' && (
        <div className="bg-green-900/50 border border-green-500 text-green-200 p-4 rounded mb-4">
          ✓ <strong>Redirect successful!</strong> The link redirects to your target URL. Victims would be sent there.
        </div>
      )}
      {verified === 'failed' && targetUrl && (
        <div className="bg-amber-900/50 border border-amber-500 text-amber-200 p-4 rounded mb-4">
          ✗ <strong>Redirect not verified.</strong> The server may have rejected the URL or returned a different redirect. Try again.
        </div>
      )}
      {error && (
        <div className="bg-red-900/50 border border-red-500 text-red-200 p-3 rounded mb-4 text-sm">
          {error}
        </div>
      )}

      <div className="flex gap-4">
        <Link to="/challenges/10/fix" className="bg-teal-600 hover:bg-teal-700 px-6 py-3 rounded font-bold">
          Try the Fix
        </Link>
        <Link to="/challenges" className="bg-gray-600 hover:bg-gray-700 px-6 py-3 rounded font-bold">
          Back to Challenges
        </Link>
      </div>
    </div>
  );
};

export default RedirectAttackPage;
