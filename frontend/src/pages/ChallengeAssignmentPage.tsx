import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../lib/api';

const CHALLENGE_CONTEXT: Record<string, string> = {
  'sql-injection':
    'Fix the SQL injection vulnerability in the login endpoint. Replace string interpolation with parameterized queries.',
  xss: 'Fix XSS by avoiding unsafe HTML rendering; use escaping or safe APIs so user content cannot run scripts.',
  csrf: 'Add CSRF protection on state-changing endpoints so cross-site requests cannot forge authenticated actions.',
  'command-injection':
    'Eliminate shell injection by avoiding shell=True and untrusted concatenation; use safe argument lists.',
  'broken-auth': 'Replace weak authentication with secure password verification (e.g. hashing) and proper session checks.',
  'security-misc':
    'Correct security misconfiguration: restrict debug/admin endpoints and avoid exposing sensitive configuration.',
  'insecure-storage':
    'Fix insecure storage by hashing secrets, avoiding plaintext credentials in dumps, and using durable secure storage.',
  'directory-traversal':
    'Normalize and constrain file paths so users cannot read files outside the intended directory.',
  xxe: 'Disable dangerous XML features such as external entities so XML parsing cannot disclose local files.',
  redirect: 'Validate redirect targets against an allowlist so open redirects cannot send users to attacker-controlled URLs.',
};

const JETBRAINS = "'JetBrains Mono', ui-monospace, monospace";

interface StatusPayload {
  assignment_id: number;
  title: string;
  challenge_slug: string;
  instructions: string | null;
  time_limit_minutes: number;
  due_date: string | null;
  status: string;
  started_at: string | null;
  submitted_at: string | null;
  score: number | null;
  sandbox_passed: boolean | null;
  time_used_seconds: number;
  time_remaining_seconds: number | null;
  is_expired: boolean;
  is_past_due: boolean;
}

const ChallengeAssignmentPage: React.FC = () => {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const aid = Number(assignmentId);
  const navigate = useNavigate();

  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [code, setCode] = useState('');
  const [lineCount, setLineCount] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [submitBanner, setSubmitBanner] = useState<{ ok: boolean; msg: string } | null>(null);
  const [timesUp, setTimesUp] = useState(false);
  const [starting, setStarting] = useState(false);
  const [remainingSec, setRemainingSec] = useState<number | null>(null);

  const codeRef = useRef(code);
  const autoSubmittedRef = useRef(false);

  useEffect(() => {
    codeRef.current = code;
  }, [code]);

  useEffect(() => {
    setLineCount(code.split('\n').length);
  }, [code]);

  const studentLabel = sessionStorage.getItem('user_email') || 'Student';

  const endTimeRef = useRef<number | null>(null);

  const fetchStatus = useCallback(async () => {
    if (!assignmentId || Number.isNaN(aid)) return;
    const res = await api.get<StatusPayload>(`/api/challenge-assignments/${aid}/status`);
    setStatus(res.data);
    if (res.data.status === 'in_progress' && res.data.time_remaining_seconds != null) {
      endTimeRef.current = Date.now() + res.data.time_remaining_seconds * 1000;
      setRemainingSec(res.data.time_remaining_seconds);
    } else if (res.data.status === 'assigned') {
      setRemainingSec(null);
      endTimeRef.current = null;
    }
  }, [aid, assignmentId]);

  useEffect(() => {
    if (!assignmentId || Number.isNaN(aid)) return;
    setLoadError(null);
    endTimeRef.current = null;
    setTimesUp(false);
    autoSubmittedRef.current = false;
    api
      .get<StatusPayload>(`/api/challenge-assignments/${aid}/status`)
      .then((res) => {
        setStatus(res.data);
        if (res.data.status === 'in_progress' && res.data.time_remaining_seconds != null) {
          endTimeRef.current = Date.now() + res.data.time_remaining_seconds * 1000;
          setRemainingSec(res.data.time_remaining_seconds);
        } else {
          setRemainingSec(null);
        }
        const slug = res.data.challenge_slug;
        return api.get<{ vulnerable_code: string }>(`/api/challenges/source/${encodeURIComponent(slug)}`);
      })
      .then((r) => setCode(r.data.vulnerable_code || ''))
      .catch((e: { response?: { data?: { detail?: string } } }) => {
        setLoadError(e?.response?.data?.detail || 'Failed to load assignment');
      });
  }, [aid, assignmentId]);

  useEffect(() => {
    if (!status || status.status !== 'in_progress' || endTimeRef.current === null) return;
    const tick = () => {
      const left = Math.max(0, Math.floor((endTimeRef.current! - Date.now()) / 1000));
      setRemainingSec(left);
      if (left <= 0) setTimesUp(true);
    };
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, [status?.status, status?.assignment_id]);

  const submitCode = async (submitted: string, fromTimer = false) => {
    if (!assignmentId || Number.isNaN(aid)) return;
    if (autoSubmittedRef.current && fromTimer) return;
    if (fromTimer) autoSubmittedRef.current = true;
    setSubmitting(true);
    setSubmitBanner(null);
    try {
      const res = await api.post(`/api/challenge-assignments/${aid}/submit-fix`, {
        submitted_code: submitted,
      });
      setSubmitBanner({
        ok: !!res.data?.passed,
        msg: res.data?.passed
          ? '✓ Passed! Score: 100/100'
          : '✗ Tests failed. Score: 0/100',
      });
      await fetchStatus();
    } catch (e: unknown) {
      const ax = e as { response?: { status?: number; data?: { detail?: string } } };
      if (ax.response?.status === 403) {
        setSubmitBanner({ ok: false, msg: ax.response?.data?.detail || 'Time or due date expired.' });
        await fetchStatus();
      } else {
        setSubmitBanner({ ok: false, msg: ax.response?.data?.detail || 'Submit failed' });
      }
    } finally {
      setSubmitting(false);
    }
  };

  useEffect(() => {
    if (!timesUp || autoSubmittedRef.current) return;
    void submitCode(codeRef.current, true);
  }, [timesUp]);

  const handleStart = async () => {
    if (!assignmentId || Number.isNaN(aid)) return;
    setStarting(true);
    try {
      const res = await api.post(`/api/challenge-assignments/${aid}/start`);
      const limit = Number(res.data?.time_limit_seconds ?? 0);
      endTimeRef.current = Date.now() + limit * 1000;
      setRemainingSec(limit);
      setTimesUp(false);
      autoSubmittedRef.current = false;
      await fetchStatus();
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { detail?: string } } };
      alert(ax.response?.data?.detail || 'Could not start assignment');
    } finally {
      setStarting(false);
    }
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const t = e.currentTarget;
      const start = t.selectionStart;
      const end = t.selectionEnd;
      const next = `${code.slice(0, start)}    ${code.slice(end)}`;
      setCode(next);
      window.requestAnimationFrame(() => {
        t.selectionStart = t.selectionEnd = start + 4;
      });
    }
  };

  if (loadError) {
    return (
      <div className="min-h-screen bg-gray-900 text-red-300 flex items-center justify-center p-6">
        {loadError}
      </div>
    );
  }
  if (!status) {
    return <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">Loading…</div>;
  }

  const slug = status.challenge_slug;
  const ctx = CHALLENGE_CONTEXT[slug] || 'Complete the secure coding fix for this lab in app.py.';
  const pastDue =
    Boolean(status.is_past_due) ||
    (Boolean(status.due_date) && new Date(status.due_date as string) < new Date());
  const locked =
    pastDue ||
    ['passed', 'failed', 'expired'].includes(status.status) ||
    (timesUp && (remainingSec !== null && remainingSec <= 0));

  const mm = remainingSec != null ? String(Math.floor(remainingSec / 60)).padStart(2, '0') : '--';
  const ss = remainingSec != null ? String(remainingSec % 60).padStart(2, '0') : '--';
  let timerColor = '#10b981';
  let timerClass = '';
  if (remainingSec != null) {
    if (remainingSec < 120) {
      timerColor = '#ef4444';
      timerClass = 'animate-pulse';
    } else if (remainingSec < 300) {
      timerColor = '#f59e0b';
      timerClass = 'animate-pulse';
    }
  }

  const showOverlay =
    pastDue ||
    status.status === 'passed' ||
    status.status === 'failed' ||
    status.status === 'expired' ||
    (timesUp && remainingSec === 0);

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 flex flex-col relative">
      <header
        className="h-[60px] shrink-0 flex items-center justify-between px-4 border-b border-gray-700 bg-black/40"
        style={{ minHeight: 60 }}
      >
        <div className="text-sm max-w-[28%] truncate">
          <div className="font-bold text-white">{status.title}</div>
          <div className="text-gray-400 text-xs">{slug.replace(/-/g, ' ')}</div>
        </div>
        <div className="flex-1 flex justify-center items-center">
          {status.status === 'assigned' ? (
            <button
              type="button"
              disabled={starting || pastDue}
              onClick={handleStart}
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 font-semibold text-white disabled:opacity-40"
            >
              {starting ? 'Starting…' : 'Start Assignment (Timer begins immediately)'}
            </button>
          ) : (
            <div
              className={`text-[28px] font-bold tabular-nums ${timerClass}`}
              style={{ fontFamily: JETBRAINS, color: timerColor }}
            >
              {timesUp && remainingSec === 0 ? (
                <span style={{ color: '#ef4444' }}>TIME&apos;S UP</span>
              ) : (
                `${mm}:${ss}`
              )}
            </div>
          )}
        </div>
        <div className="max-w-[28%] text-right text-sm flex flex-col items-end gap-1">
          <span className="text-gray-300 truncate w-full">{studentLabel}</span>
          <button
            type="button"
            disabled={locked || submitting || status.status !== 'in_progress' || pastDue}
            onClick={() => submitCode(codeRef.current, false)}
            className="px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-xs font-semibold disabled:opacity-40"
          >
            Submit Assignment
          </button>
        </div>
      </header>

      {pastDue && (
        <div className="absolute inset-0 z-50 bg-black/75 flex flex-col items-center justify-center p-6">
          <p className="text-2xl font-bold text-red-400 mb-4">ASSIGNMENT EXPIRED</p>
          <p className="text-gray-300 mb-6 text-center">The due date for this assignment has passed.</p>
          <button
            type="button"
            onClick={() => navigate('/home')}
            className="px-6 py-2 rounded bg-gray-700 hover:bg-gray-600"
          >
            Return to Dashboard
          </button>
        </div>
      )}

      {!pastDue && showOverlay && (
        <div className="absolute inset-0 z-50 bg-black/70 flex flex-col items-center justify-center p-6">
          {status.status === 'passed' && (
            <>
              <div className="text-6xl text-green-400 mb-2">✓</div>
              <p className="text-2xl font-bold text-green-400 mb-2">Assignment Passed!</p>
              <p className="text-gray-300">Score: {status.score ?? 100}/100</p>
            </>
          )}
          {status.status === 'failed' && (
            <>
              <p className="text-2xl font-bold text-amber-200 mb-2">Assignment Submitted</p>
              <p className="text-gray-300">Score: {status.score ?? 0}/100</p>
            </>
          )}
          {status.status === 'expired' && (
            <>
              <p className="text-2xl font-bold text-red-400 mb-2">Time Expired</p>
              <p className="text-gray-300">Score: {status.score ?? '—'}</p>
            </>
          )}
          {timesUp && remainingSec === 0 && status.status === 'in_progress' && (
            <p className="text-red-400 font-bold mt-4">Submitting your work…</p>
          )}
          {['passed', 'failed', 'expired'].includes(status.status) && (
            <button
              type="button"
              onClick={() => navigate('/home')}
              className="mt-8 px-6 py-2 rounded bg-gray-700 hover:bg-gray-600"
            >
              Return to Dashboard
            </button>
          )}
        </div>
      )}

      <div className="flex-1 flex flex-col lg:flex-row gap-4 p-4">
        <div className="lg:w-[40%] space-y-4">
          <div className="bg-gray-800/80 border border-gray-700 rounded-lg p-4">
            <h2 className="font-bold text-teal-300 mb-2">Assignment Details</h2>
            <p className="text-sm">
              <span className="text-gray-400">Time limit:</span> {status.time_limit_minutes} min
            </p>
            {status.due_date && (
              <p className="text-sm">
                <span className="text-gray-400">Due:</span>{' '}
                <span className={pastDue ? 'text-red-400' : 'text-gray-200'}>
                  {new Date(status.due_date).toLocaleString()}
                </span>
              </p>
            )}
            {status.instructions && <p className="text-sm mt-2 text-gray-300">{status.instructions}</p>}
            <p className="mt-2 text-xs">
              Status:{' '}
              <span className="font-semibold uppercase text-amber-200">{status.status}</span>
            </p>
          </div>
          <div
            className="bg-gray-800/80 border border-amber-900/40 rounded-lg p-4"
            style={{ background: 'rgba(245, 158, 11, 0.05)' }}
          >
            <h2 className="font-bold text-gray-200 mb-2">Challenge Context</h2>
            <p className="text-sm text-gray-300">{ctx}</p>
            <p className="text-xs text-amber-200/90 mt-3">
              ℹ Hints and AI Mentor are disabled during assigned challenges.
            </p>
          </div>
          <div className="bg-gray-800/80 border border-gray-700 rounded-lg p-4">
            <h2 className="font-bold text-gray-200 mb-2">Submission</h2>
            {status.submitted_at ? (
              <p className="text-sm">
                {status.status === 'passed' ? 'Passed' : status.status === 'failed' ? 'Failed' : status.status} — Score:{' '}
                {status.score ?? '—'} — Time used: {status.time_used_seconds}s
              </p>
            ) : (
              <p className="text-sm text-gray-500">No submission yet.</p>
            )}
          </div>
        </div>
        <div className="lg:w-[60%] flex flex-col min-h-0">
          <h2 className="font-bold mb-2 text-gray-200">
            Your Solution — {slug}/app.py
          </h2>
          <textarea
            className="flex-1 w-full rounded border border-gray-600 p-4 outline-none focus:border-blue-500 disabled:opacity-50"
            style={{
              minHeight: 500,
              fontFamily: JETBRAINS,
              fontSize: 13,
              background: '#0d1117',
              color: '#e6edf3',
            }}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            onKeyDown={onKeyDown}
            disabled={locked || status.status !== 'in_progress' || pastDue}
          />
          <p className="text-xs text-gray-500 mt-1">{lineCount} lines</p>
          {submitBanner && (
            <div
              className={`mt-2 p-3 rounded text-sm ${
                submitBanner.ok ? 'bg-green-900/40 border border-green-600' : 'bg-red-900/40 border border-red-600'
              }`}
            >
              {submitBanner.msg}
            </div>
          )}
          <button
            type="button"
            disabled={locked || submitting || status.status !== 'in_progress' || pastDue}
            onClick={() => submitCode(code, false)}
            className="mt-3 w-full py-3 rounded-lg bg-green-600 hover:bg-green-500 font-bold disabled:opacity-40"
          >
            {submitting ? 'Submitting…' : 'Submit Fix'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChallengeAssignmentPage;
