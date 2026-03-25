import * as React from 'react';
import { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_BASE = `${API_URL}/api/challenges`;

const RedirectAttackPage: React.FC = () => {
  // These start empty so the lab does not reveal a ready-made payload.
  const [targetDomain, setTargetDomain] = useState('');
  const [targetPath, setTargetPath] = useState('');
  const [queryString, setQueryString] = useState('');
  const [previewUrl, setPreviewUrl] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const [verified, setVerified] = useState<'pending' | 'success' | 'failed'>('pending');
  const [error, setError] = useState('');
  const iframeRef = useRef<HTMLIFrameElement | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const doneRef = useRef(false);
  const navigate = useNavigate();

  const attackerTarget = React.useMemo(() => {
    const base = `${targetDomain.replace(/\/+$/, '')}${targetPath.startsWith('/') ? targetPath : `/${targetPath}`}`;
    return queryString.trim() ? `${base}?${queryString.trim()}` : base;
  }, [targetDomain, targetPath, queryString]);

  const craftedLink = attackerTarget
    ? `${API_BASE}/redirect?url=${encodeURIComponent(attackerTarget)}`
    : '';

  const appendLog = (line: string) => setLogs(prev => [...prev, line]);

  const handleVerify = () => {
    setError('');
    setVerified('pending');
    setPreviewUrl(attackerTarget);
    if (!attackerTarget.trim()) {
      setError('Please build a target URL for the victim.');
      return;
    }
    if (!craftedLink) return;
    doneRef.current = false;

    appendLog(`Crafted attack URL: ${craftedLink}`);
    appendLog('Launching hidden victim browser (iframe) against vulnerable redirect...');

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
        appendLog(`Victim final location: ${href || '[unavailable]'}`);

        if (href.includes('attack-success') && href.includes('type=redirect')) {
          setVerified('success');
          appendLog('Exploit successful: victim was redirected to the attack-success page.');
          const token = sessionStorage.getItem('token');
          if (token) {
            axios
              .post(
                `${API_BASE}/mark-attack-complete?challenge_type=redirect`,
                {},
                { headers: { Authorization: `Bearer ${token}` } },
              )
              .catch(() => {});
          }
          navigate('/challenges/attack-success?type=redirect');
        } else if (href && !href.startsWith(API_BASE)) {
          // Any external redirect also counts as success from an attacker POV
          setVerified('success');
          appendLog('Exploit successful: victim was redirected away from the trusted origin.');
          const token = sessionStorage.getItem('token');
          if (token) {
            axios
              .post(
                `${API_BASE}/mark-attack-complete?challenge_type=redirect`,
                {},
                { headers: { Authorization: `Bearer ${token}` } },
              )
              .catch(() => {});
          }
          navigate('/challenges/attack-success?type=redirect');
        } else {
          setVerified('failed');
          appendLog('Exploit failed: redirect stayed within the trusted app or did not occur.');
        }
      } catch {
        setVerified('failed');
        appendLog('Unable to inspect victim location (cross-origin).');
      }
      try {
        document.body.removeChild(iframe);
      } catch {
        /* already removed */
      }
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
    <div className="text-white p-6 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">Unvalidated Redirect Attack</h1>
      <p className="text-gray-400 mb-6">
        The app exposes a redirect endpoint that trusts a user-controlled <code>url</code> parameter. Your task is to discover a target
        destination and build a link that sends a victim from the trusted origin to that destination.
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Left: Victim view */}
        <div className="bg-gray-900 rounded-lg border border-gray-700 p-4">
          <h2 className="text-lg font-bold text-teal-400 mb-2">Trusted Application (Victim View)</h2>
          <p className="text-xs text-gray-400 mb-3">
            This is how the link appears to the victim. It starts with the trusted domain and then silently redirects to your
            destination.
          </p>
          <div className="bg-gray-800 rounded p-3 text-xs font-mono break-all mb-3">
            <span className="text-gray-400">Trusted link:</span>
            <br />
            <span className="text-teal-300">{craftedLink || `${API_BASE}/redirect?url=<your_target_here>`}</span>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-inner text-gray-800">
            <div className="text-sm font-medium text-gray-600 mb-2">Dashboard</div>
            <p className="text-gray-500 text-sm mb-3">
              Return to your destination after login. This link is supposed to send users back to <code>/dashboard</code>, but the
              backend never validates the target.
            </p>
            <button
              onClick={handleOpenLink}
              disabled={!craftedLink}
              className="px-4 py-2 bg-gray-900 hover:bg-gray-800 disabled:opacity-50 text-white font-semibold rounded text-sm"
            >
              Open trusted link in new tab
            </button>
          </div>
        </div>

        {/* Right: Attacker builder */}
        <div className="bg-gray-900 rounded-lg border border-gray-700 p-4">
          <h2 className="text-lg font-bold text-red-400 mb-2">Attacker Link Builder</h2>
          <p className="text-xs text-gray-400 mb-3">
            Build the destination URL you control (phishing page, malicious site, or in this lab the attack-success page). The redirect
            endpoint will send the victim there without validation.
          </p>

          <div className="space-y-2 text-sm">
            <div>
              <label className="block text-xs text-gray-300 mb-1">Target domain (attacker-controlled)</label>
              <input
                type="text"
                value={targetDomain}
                onChange={e => setTargetDomain(e.target.value)}
                className="w-full px-2 py-1 rounded bg-gray-800 border border-gray-700 text-xs"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-300 mb-1">Path</label>
              <input
                type="text"
                value={targetPath}
                onChange={e => setTargetPath(e.target.value)}
                className="w-full px-2 py-1 rounded bg-gray-800 border border-gray-700 text-xs"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-300 mb-1">Query string</label>
              <input
                type="text"
                value={queryString}
                onChange={e => setQueryString(e.target.value)}
                className="w-full px-2 py-1 rounded bg-gray-800 border border-gray-700 text-xs"
                placeholder="type=redirect"
              />
            </div>
          </div>

          <div className="mt-3 bg-black border border-gray-800 rounded p-3 font-mono text-xs break-all">
            <div className="text-gray-400 mb-1">Victim destination (attacker-controlled):</div>
            <div className="text-yellow-300">
              {attackerTarget || '// Fill in target domain, path, and (optionally) query string to build this URL'}
            </div>
          </div>

          <div className="mt-4 flex gap-3">
            <button
              onClick={handleVerify}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold rounded text-sm"
            >
              Launch Redirect Attack
            </button>
          </div>
        </div>
      </div>

      {/* Attack logs */}
      <div className="bg-black border border-green-800 rounded-lg p-4 font-mono text-xs h-40 overflow-y-auto mb-4">
        <div className="text-green-500 mb-1 border-b border-green-800 pb-1">
          Attack Logs — Unvalidated Redirect
        </div>
        {logs.length === 0 && <div className="text-gray-600">No attacks executed yet.</div>}
        {logs.map((line, idx) => (
          <div key={idx} className="text-green-400">
            {line}
          </div>
        ))}
      </div>

      {verified === 'success' && (
        <div className="bg-green-900/50 border border-green-500 text-green-200 p-4 rounded mb-4">
          ✓ <strong>Redirect successful!</strong> The victim was sent to an attacker-controlled destination.
        </div>
      )}
      {verified === 'failed' && (
        <div className="bg-amber-900/50 border border-amber-500 text-amber-200 p-4 rounded mb-4">
          ✗ <strong>Redirect not verified.</strong> The redirect stayed internal or could not be confirmed. Adjust your target and try
          again.
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
