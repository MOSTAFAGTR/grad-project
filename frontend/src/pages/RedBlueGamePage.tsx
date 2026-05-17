import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../lib/api';

const CHALLENGE_TITLES: Record<number, string> = {
  1: 'SQL Injection',
  2: 'XSS',
  3: 'CSRF',
  4: 'Command Injection',
  5: 'Broken Authentication',
  6: 'Security Misconfiguration',
  7: 'Insecure Storage',
  8: 'Directory Traversal',
  9: 'XXE',
  10: 'Unvalidated Redirect',
};

interface AttackRow {
  id: number;
  challenge_id: number;
  payload_used: string;
  timestamp: string;
  impact_description: string;
  status?: string;
}

interface BlueFixRow {
  id: number;
  challenge_id: number;
  fixed: boolean;
  timestamp: string;
  submitted_code: string;
}

const RedBlueGamePage: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const gid = Number(gameId);

  const [gameData, setGameData] = useState<any>(null);
  const [attacks, setAttacks] = useState<AttackRow[]>([]);
  const lastSeenRef = useRef(0);
  const [pollingActive, setPollingActive] = useState(true);
  const [fixCode, setFixCode] = useState('');
  const [fixSubmitting, setFixSubmitting] = useState(false);
  const [fixResult, setFixResult] = useState<{ fixed: boolean; message: string } | null>(null);
  const [gameLoading, setGameLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [endLoading, setEndLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [endResult, setEndResult] = useState<{ red: number; blue: number } | null>(null);
  const [attackPayload, setAttackPayload] = useState('');
  const [attackImpact, setAttackImpact] = useState('');
  const [attackSubmitting, setAttackSubmitting] = useState(false);
  const [codeLoading, setCodeLoading] = useState(false);
  const [originalVulnerableCode, setOriginalVulnerableCode] = useState('');
  const [challengeCodeName, setChallengeCodeName] = useState('');
  const [attackHint, setAttackHint] = useState('');
  const [attackFeedback, setAttackFeedback] = useState<{
    kind: 'success' | 'fail';
    message: string;
    hint?: string;
    preview?: string;
  } | null>(null);
  const [bluePanelToast, setBluePanelToast] = useState<string | null>(null);
  const [redPulse, setRedPulse] = useState(false);
  const [bluePulse, setBluePulse] = useState(false);

  const prevRedRef = useRef<number | null>(null);
  const prevBlueRef = useRef<number | null>(null);
  const isBlueTeamRef = useRef(false);

  const role = sessionStorage.getItem('role');
  const myUserId = Number(sessionStorage.getItem('user_id') || '0');
  const isInstructor = role === 'instructor' || role === 'admin';

  const loadGame = useCallback(async () => {
    if (!gameId || Number.isNaN(gid)) return;
    setGameLoading(true);
    setLoadError(null);
    try {
      const res = await api.get(`/api/redblue/game/${gid}`);
      const d = res.data;
      setGameData(d);
      const initial: AttackRow[] = (d.red_actions || []).map((a: any) => ({
        id: a.id,
        challenge_id: a.challenge_id,
        payload_used: a.payload_used || '',
        timestamp: a.timestamp,
        impact_description: a.impact_description || '',
        status: a.status || 'confirmed',
      }));
      setAttacks(initial);
      const maxId = initial.reduce((m, a) => Math.max(m, a.id), 0);
      lastSeenRef.current = maxId;
      if (d.status === 'completed') {
        setPollingActive(false);
      }
    } catch (e: any) {
      setLoadError(e?.response?.data?.detail || e?.message || 'Failed to load game');
    } finally {
      setGameLoading(false);
    }
  }, [gameId, gid]);

  useEffect(() => {
    loadGame();
  }, [loadGame]);

  useEffect(() => {
    if (!gameData) return;
    const r = gameData.red_team?.score ?? 0;
    const b = gameData.blue_team?.score ?? 0;
    if (prevRedRef.current !== null && prevRedRef.current !== r) {
      setRedPulse(true);
      window.setTimeout(() => setRedPulse(false), 400);
    }
    if (prevBlueRef.current !== null && prevBlueRef.current !== b) {
      setBluePulse(true);
      window.setTimeout(() => setBluePulse(false), 400);
    }
    prevRedRef.current = r;
    prevBlueRef.current = b;
  }, [gameData?.red_team?.score, gameData?.blue_team?.score, gameData]);

  useEffect(() => {
    if (!gameData) {
      isBlueTeamRef.current = false;
      return;
    }
    isBlueTeamRef.current = (gameData.blue_team?.members || []).some(
      (m: { user_id: number }) => m.user_id === myUserId,
    );
  }, [gameData, myUserId]);

  useEffect(() => {
    if (!pollingActive || !gameId || Number.isNaN(gid)) return;
    const tick = async () => {
      try {
        const res = await api.get(`/api/redblue/game/${gid}/attacks`, {
          params: { since_id: lastSeenRef.current },
        });
        const newOnes: AttackRow[] = (res.data.attacks || []).map((a: any) => ({
          id: a.id,
          challenge_id: a.challenge_id,
          payload_used: a.payload_used || '',
          timestamp: a.timestamp,
          impact_description: a.impact_description || '',
          status: a.status || 'confirmed',
        }));
        if (newOnes.length) {
          for (const a of newOnes) {
            if (isBlueTeamRef.current && a.status === 'failed') {
              setBluePanelToast('🛡 Attack blocked! +1 defensive point');
              window.setTimeout(() => setBluePanelToast(null), 2000);
            }
          }
          const ordered = [...newOnes].reverse();
          setAttacks((prev) => {
            const seen = new Set(prev.map((p) => p.id));
            const merged = [...ordered.filter((a) => !seen.has(a.id)), ...prev];
            return merged;
          });
          const maxNew = Math.max(...newOnes.map((a) => a.id));
          lastSeenRef.current = Math.max(lastSeenRef.current, maxNew);
        }
      } catch {
        /* ignore poll errors */
      }
    };
    const id = setInterval(tick, 5000);
    return () => clearInterval(id);
  }, [pollingActive, gid, gameId]);

  useEffect(() => {
    if (!gameData) return;
    setCodeLoading(true);
    api
      .get(`/api/redblue/game/${gid}/challenge-code`)
      .then((res) => {
        setOriginalVulnerableCode(res.data.vulnerable_code);
        setFixCode(res.data.vulnerable_code);
        setChallengeCodeName(res.data.challenge_name || '');
        setAttackHint(res.data.attack_hint || '');
        setCodeLoading(false);
      })
      .catch(() => {
        setFixCode("# Could not load challenge source.\n# Please ask your instructor.");
        setCodeLoading(false);
      });
  }, [gameData?.game_id, gid]);

  const formatTime = (iso: string) => {
    try {
      const d = new Date(iso.replace(/Z$/, ''));
      return d.toLocaleTimeString(undefined, { hour12: false });
    } catch {
      return iso;
    }
  };

  const truncatePayload = (s: string) => {
    if (s.length <= 100) return s;
    return `${s.slice(0, 100)}...`;
  };

  const challengeName =
    challengeCodeName ||
    (gameData?.challenge_id != null ? CHALLENGE_TITLES[gameData.challenge_id] || 'Challenge' : 'Challenge');
  const status = gameData?.status || '';
  const isRedTeam = (gameData?.red_team?.members || []).some((m: { user_id: number }) => m.user_id === myUserId);
  const isBlueTeam = (gameData?.blue_team?.members || []).some((m: { user_id: number }) => m.user_id === myUserId);
  const redInstr = gameData?.challenge_instructions?.red_team || '';
  const blueInstr = gameData?.challenge_instructions?.blue_team || '';
  const totalAttempts = gameData?.total_red_attempts ?? null;

  const submitFix = async () => {
    if (!gameData) return;
    setFixSubmitting(true);
    setFixResult(null);
    try {
      const res = await api.post(`/api/redblue/game/${gid}/fix`, {
        challenge_id: gameData.challenge_id,
        submitted_code: fixCode,
      });
      setFixResult({ fixed: !!res.data.fixed, message: res.data.message || '' });
      await loadGame();
    } catch (e: any) {
      const d = e?.response?.data?.detail;
      setFixResult({ fixed: false, message: typeof d === 'string' ? d : 'Request failed' });
    } finally {
      setFixSubmitting(false);
    }
  };

  const submitAttack = async () => {
    if (!gameData || !attackPayload.trim()) return;
    setAttackSubmitting(true);
    setAttackFeedback(null);
    try {
      const res = await api.post(`/api/redblue/game/${gid}/attack`, {
        challenge_id: gameData.challenge_id,
        payload_used: attackPayload,
        impact_description: attackImpact,
      });
      const data = res.data;
      if (data.confirmed === true) {
        setAttackFeedback({
          kind: 'success',
          message:
            '✓ Attack confirmed! Your payload exploited the vulnerability. +1 point for Red Team.',
          preview: data.response_preview,
        });
        setAttackPayload('');
        setAttackImpact('');
      } else {
        setAttackFeedback({
          kind: 'fail',
          message: data.patched_by_blue
            ? '🛡 Blocked — the blue team has patched this vulnerability. Your payload was rejected.'
            : '✗ Attack failed. The payload did not work.',
          hint: data.hint,
          preview: data.response_preview,
        });
      }
      await loadGame();
    } catch (e: any) {
      const d = e?.response?.data?.detail;
      alert(typeof d === 'string' ? d : 'Could not log attack');
    } finally {
      setAttackSubmitting(false);
    }
  };

  const endGame = async () => {
    setEndLoading(true);
    try {
      const res = await api.post(`/api/redblue/game/${gid}/end`);
      setEndResult({ red: res.data.final_red_score, blue: res.data.final_blue_score });
      setPollingActive(false);
      await loadGame();
    } catch (e: any) {
      const d = e?.response?.data?.detail;
      alert(typeof d === 'string' ? d : 'Failed to end game');
    } finally {
      setEndLoading(false);
    }
  };

  const deleteGame = async () => {
    if (
      !window.confirm(
        'Permanently delete this game? All attacks, fixes, scores, and team assignments for this session will be removed. This cannot be undone.',
      )
    ) {
      return;
    }
    setDeleteLoading(true);
    try {
      await api.post(`/api/redblue/game/${gid}/delete`);
      navigate('/instructor/dashboard');
    } catch (e: any) {
      const d = e?.response?.data?.detail;
      alert(typeof d === 'string' ? d : 'Failed to delete game');
    } finally {
      setDeleteLoading(false);
    }
  };

  if (gameLoading && !gameData) {
    return <div className="p-8 text-white bg-gray-900 min-h-screen">Loading game…</div>;
  }
  if (loadError) {
    return <div className="p-8 text-red-400 bg-gray-900 min-h-screen">{loadError}</div>;
  }
  if (!gameData) return null;

  const redScore = gameData.red_team?.score ?? 0;
  const blueScore = gameData.blue_team?.score ?? 0;
  const lineCount = fixCode.split('\n').length;
  const showAttackPanel = isRedTeam || isInstructor;
  const vulnerabilityPatched: boolean = gameData?.vulnerability_patched === true;

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4">
      <div className="max-w-6xl mx-auto">
        <header className="flex flex-wrap items-center justify-between gap-4 mb-6 p-4 bg-gray-800 rounded-lg border border-gray-700">
          <div className="flex items-center gap-2">
            <span className="text-gray-400">Red Team:</span>
            <span className="font-semibold">{gameData.red_team?.name}</span>
            <span
              className={`px-2 py-0.5 rounded bg-red-700 text-sm font-bold transition-transform duration-200 ${redPulse ? 'scale-125' : 'scale-100'}`}
              style={redPulse ? { boxShadow: '0 0 12px rgba(248, 113, 113, 0.6)' } : undefined}
            >
              {redScore}
            </span>
          </div>
          <div className="text-center flex-1 min-w-[200px]">
            <span
              className={`inline-block px-3 py-1 rounded text-sm font-bold mr-2 ${
                status === 'active' ? 'bg-green-700' : 'bg-gray-600'
              }`}
            >
              {status === 'active' ? 'ACTIVE' : status === 'completed' ? 'COMPLETED' : status.toUpperCase()}
            </span>
            <span className="text-gray-300">{challengeName}</span>
            {totalAttempts != null && (
              <span className="block text-xs text-gray-500 mt-1">
                Red attempts: {totalAttempts} · Hits: {redScore}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-400">Blue Team:</span>
            <span className="font-semibold">{gameData.blue_team?.name}</span>
            <span
              title={
                gameData.blue_score_breakdown
                  ? `${gameData.blue_score_breakdown.real_fixes} fixes + ${gameData.blue_score_breakdown.defensive_blocks} blocks`
                  : undefined
              }
              className={`px-2 py-0.5 rounded bg-blue-700 text-sm font-bold transition-transform duration-200 ${bluePulse ? 'scale-125' : 'scale-100'}`}
              style={bluePulse ? { boxShadow: '0 0 12px rgba(96, 165, 250, 0.7)' } : undefined}
            >
              {blueScore} pts
            </span>
            {gameData.blue_score_breakdown && (
              <span className="text-[10px] text-blue-300/90 max-w-[120px] leading-tight hidden sm:inline">
                {gameData.blue_score_breakdown.real_fixes} fixes + {gameData.blue_score_breakdown.defensive_blocks}{' '}
                blocks
              </span>
            )}
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 flex flex-col min-h-[400px]">
            <h2 className="text-lg font-bold mb-1 flex items-center gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              Live Attack Feed
            </h2>
            {redInstr && (
              <p className="text-xs text-red-200/90 mb-3 border-b border-red-900/50 pb-2">{redInstr}</p>
            )}
            {attackFeedback && attackFeedback.kind === 'success' && (
              <div className="mb-3 p-3 rounded border border-green-600 bg-green-900/30 text-green-100 text-sm">
                {attackFeedback.message}
                {attackFeedback.preview != null && (
                  <span className="block mt-2 font-mono text-xs opacity-90">
                    Response preview: {attackFeedback.preview}
                  </span>
                )}
              </div>
            )}
            {attackFeedback && attackFeedback.kind === 'fail' && (
              <div className="mb-3 p-3 rounded border border-red-600 bg-red-900/30 text-red-100 text-sm">
                {attackFeedback.message}
                {attackFeedback.hint && (
                  <span className="block mt-2">Hint: {attackFeedback.hint}</span>
                )}
                {attackFeedback.preview != null && (
                  <span className="block mt-2 font-mono text-xs opacity-90">
                    Response: {attackFeedback.preview}
                  </span>
                )}
              </div>
            )}
            {/* Patched banner — shown to red team and instructors */}
            {vulnerabilityPatched && showAttackPanel && (
              <div className="mb-4 p-3 rounded-lg border border-green-500 bg-green-950/60 flex items-start gap-2">
                <span className="text-green-400 text-lg mt-0.5">🛡</span>
                <div>
                  <p className="text-green-300 font-semibold text-sm">Vulnerability Patched</p>
                  <p className="text-green-200/80 text-xs mt-0.5">
                    The blue team has submitted a working fix. All further attack payloads will be
                    automatically rejected.
                  </p>
                </div>
              </div>
            )}

            {showAttackPanel && status === 'active' && (
              <div className={`mb-4 p-3 bg-gray-900/80 border rounded-lg space-y-2 ${vulnerabilityPatched ? 'border-gray-600 opacity-50 pointer-events-none select-none' : 'border-red-800'}`}>
                <p className="text-sm font-semibold text-red-300">
                  Submit Attack Payload
                  {vulnerabilityPatched && (
                    <span className="ml-2 text-xs text-gray-400 font-normal">(disabled — vulnerability patched)</span>
                  )}
                </p>
                <textarea
                  className="w-full font-mono text-xs border border-gray-600 rounded p-2 min-h-[100px]"
                  style={{ background: '#0d1117', color: '#e6edf3' }}
                  placeholder="Enter your attack payload here…"
                  value={attackPayload}
                  onChange={(e) => setAttackPayload(e.target.value)}
                  disabled={vulnerabilityPatched}
                />
                <textarea
                  className="w-full text-xs bg-black/50 border border-gray-600 rounded p-2 text-gray-200"
                  rows={2}
                  placeholder="Impact description (optional)"
                  value={attackImpact}
                  onChange={(e) => setAttackImpact(e.target.value)}
                  disabled={vulnerabilityPatched}
                />
                {attackHint && (
                  <p className="text-xs text-amber-200/90">Hint: {attackHint}</p>
                )}
                <button
                  type="button"
                  disabled={attackSubmitting || vulnerabilityPatched}
                  onClick={submitAttack}
                  className="w-full py-2 rounded bg-red-700 hover:bg-red-600 text-sm font-semibold disabled:opacity-50"
                >
                  {attackSubmitting ? 'Submitting…' : 'Submit Payload'}
                </button>
              </div>
            )}
            <div className="flex-1 overflow-y-auto space-y-3 max-h-[500px] pr-1">
              {attacks.length === 0 && <p className="text-gray-500 text-sm">No attacks yet.</p>}
              {attacks.map((a) => (
                <div
                  key={a.id}
                  className={`rounded p-3 text-sm border ${
                    a.status === 'failed'
                      ? 'bg-blue-950/40 border-blue-600/80'
                      : 'bg-gray-900 border border-gray-700'
                  }`}
                >
                  <div className="text-gray-500 text-xs mb-1 flex flex-wrap items-center gap-2">
                    <span>
                      {formatTime(a.timestamp)} · {challengeName}
                    </span>
                    {a.status === 'failed' ? (
                      <span className="text-blue-400 font-semibold">✗ BLOCKED</span>
                    ) : (
                      <span className="text-red-400 font-semibold">⚡ ✓ HIT</span>
                    )}
                  </div>
                  <pre
                    className={`text-xs font-mono whitespace-pre-wrap break-all mb-2 p-2 rounded ${
                      a.status === 'failed' ? 'bg-blue-950/50 text-blue-100' : 'text-green-300 bg-black/40'
                    }`}
                  >
                    {truncatePayload(a.payload_used)}
                  </pre>
                  <p className={a.status === 'failed' ? 'text-blue-200 text-sm' : 'text-red-200/90 text-sm'}>
                    {a.status === 'failed'
                      ? 'Payload rejected — Blue team +1'
                      : 'Exploit confirmed — Red team +1'}
                  </p>
                  {a.impact_description ? (
                    <p className="text-gray-400 text-xs mt-1">{a.impact_description}</p>
                  ) : null}
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 flex flex-col">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
              <h2 className="text-lg font-bold">
                Defense Console — {challengeName}
              </h2>
              {!codeLoading &&
                originalVulnerableCode !== '' &&
                fixCode !== originalVulnerableCode && (
                  <button
                    type="button"
                    onClick={() => setFixCode(originalVulnerableCode)}
                    className="text-xs px-3 py-1 rounded bg-gray-700 hover:bg-gray-600 border border-gray-600"
                  >
                    Reset to Original
                  </button>
                )}
            </div>
            {blueInstr && (
              <p className="text-xs text-blue-200/90 mb-3 border-b border-blue-900/50 pb-2">{blueInstr}</p>
            )}
            {bluePanelToast && (
              <div className="mb-3 p-3 rounded border border-green-600 bg-green-900/50 text-green-100 text-sm font-semibold animate-pulse">
                {bluePanelToast}
              </div>
            )}
            {/* Patch-is-holding banner — shown to blue team after a successful fix */}
            {vulnerabilityPatched && (
              <div className="mb-3 p-3 rounded-lg border border-green-500 bg-green-950/60 flex items-start gap-2">
                <span className="text-green-400 text-lg mt-0.5">✅</span>
                <div>
                  <p className="text-green-300 font-semibold text-sm">Patch Is Holding!</p>
                  <p className="text-green-200/80 text-xs mt-0.5">
                    Your fix passed all sandbox tests. Red team attacks are now blocked. You can still
                    improve your solution.
                  </p>
                </div>
              </div>
            )}
            {!vulnerabilityPatched && !codeLoading && originalVulnerableCode !== '' && fixCode !== '# Could not load challenge source.\n# Please ask your instructor.' && (
              <div className="mb-3 p-3 rounded border border-red-800 bg-red-950/40 text-red-100 text-sm">
                ⚠ This is the vulnerable version of app.py for {challengeName}. The red team is exploiting it.
                Fix the vulnerability and submit to score a defensive point.
              </div>
            )}
            {codeLoading ? (
              <div className="py-16 text-center text-gray-400">Loading challenge source…</div>
            ) : (
              <>
                <textarea
                  className="w-full rounded box-border"
                  style={{
                    minHeight: 400,
                    width: '100%',
                    fontFamily: 'monospace',
                    fontSize: 13,
                    background: '#0d1117',
                    color: '#e6edf3',
                    border: '1px solid #30363d',
                    padding: 16,
                    tabSize: 4,
                  }}
                  value={fixCode}
                  onChange={(e) => setFixCode(e.target.value)}
                  placeholder="Paste fixed code here…"
                  disabled={!isBlueTeam || status !== 'active'}
                />
                <p className="text-xs text-gray-500 mt-1">{lineCount} lines</p>
              </>
            )}
            <button
              type="button"
              disabled={fixSubmitting || !isBlueTeam || status !== 'active'}
              onClick={submitFix}
              className="mt-3 py-2 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 font-semibold"
            >
              {fixSubmitting ? 'Submitting…' : 'Submit Fix'}
            </button>
            {fixResult && (
              <div
                className={`mt-3 p-3 rounded text-sm ${
                  fixResult.fixed ? 'bg-green-900/50 border border-green-700' : 'bg-red-900/50 border border-red-700'
                }`}
              >
                {fixResult.fixed
                  ? 'Fix accepted! +1 point for Blue Team'
                  : fixResult.message || 'Fix did not pass tests. Try again.'}
              </div>
            )}
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-gray-400 mb-2">Fix history</h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {(gameData.blue_fixes || []).map((f: BlueFixRow) => (
                  <div key={f.id} className="flex justify-between text-xs bg-gray-900 p-2 rounded border border-gray-700">
                    <span className="text-gray-500">{formatTime(f.timestamp)}</span>
                    <span className={f.fixed ? 'text-green-400 font-bold' : 'text-red-400 font-bold'}>
                      {f.fixed ? 'PASSED' : 'FAILED'}
                    </span>
                    <span className="font-mono text-gray-400 truncate max-w-[50%]">
                      {(f.submitted_code || '').slice(0, 50)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {isInstructor && (
          <div className="border-t border-gray-700 pt-6">
            {endResult && (
              <p className="text-center text-green-400 mb-4">
                Game ended. Final — Red: {endResult.red}, Blue: {endResult.blue}
              </p>
            )}
            <div className="flex flex-wrap justify-center gap-3">
              <button
                type="button"
                disabled={endLoading || status === 'completed'}
                onClick={endGame}
                className="px-6 py-3 rounded bg-amber-700 hover:bg-amber-600 disabled:opacity-40 font-semibold"
              >
                {endLoading ? 'Ending…' : 'End Game'}
              </button>
              <button
                type="button"
                disabled={deleteLoading}
                onClick={deleteGame}
                className="px-6 py-3 rounded bg-red-900 hover:bg-red-800 border border-red-700 disabled:opacity-40 font-semibold"
              >
                {deleteLoading ? 'Deleting…' : 'Delete Game'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RedBlueGamePage;
