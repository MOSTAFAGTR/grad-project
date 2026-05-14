import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
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
  const [endResult, setEndResult] = useState<{ red: number; blue: number } | null>(null);
  const [attackPayload, setAttackPayload] = useState('');
  const [attackImpact, setAttackImpact] = useState('');
  const [attackSubmitting, setAttackSubmitting] = useState(false);

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
        }));
        if (newOnes.length) {
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

  const challengeName = gameData?.challenge_id != null ? CHALLENGE_TITLES[gameData.challenge_id] || 'Challenge' : 'Challenge';
  const status = gameData?.status || '';
  const isRedTeam = (gameData?.red_team?.members || []).some((m: { user_id: number }) => m.user_id === myUserId);
  const isBlueTeam = (gameData?.blue_team?.members || []).some((m: { user_id: number }) => m.user_id === myUserId);

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
    try {
      await api.post(`/api/redblue/game/${gid}/attack`, {
        challenge_id: gameData.challenge_id,
        payload_used: attackPayload,
        impact_description: attackImpact,
      });
      setAttackPayload('');
      setAttackImpact('');
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

  if (gameLoading && !gameData) {
    return <div className="p-8 text-white bg-gray-900 min-h-screen">Loading game…</div>;
  }
  if (loadError) {
    return <div className="p-8 text-red-400 bg-gray-900 min-h-screen">{loadError}</div>;
  }
  if (!gameData) return null;

  const redScore = gameData.red_team?.score ?? 0;
  const blueScore = gameData.blue_team?.score ?? 0;

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4">
      <div className="max-w-6xl mx-auto">
        <header className="flex flex-wrap items-center justify-between gap-4 mb-6 p-4 bg-gray-800 rounded-lg border border-gray-700">
          <div className="flex items-center gap-2">
            <span className="text-gray-400">Red Team:</span>
            <span className="font-semibold">{gameData.red_team?.name}</span>
            <span className="px-2 py-0.5 rounded bg-red-700 text-sm font-bold">{redScore}</span>
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
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-400">Blue Team:</span>
            <span className="font-semibold">{gameData.blue_team?.name}</span>
            <span className="px-2 py-0.5 rounded bg-blue-700 text-sm font-bold">{blueScore}</span>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 flex flex-col min-h-[400px]">
            <h2 className="text-lg font-bold mb-3 flex items-center gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              Live Attack Feed
            </h2>
            {isRedTeam && status === 'active' && (
              <div className="mb-4 p-3 bg-gray-900/80 border border-red-800 rounded-lg space-y-2">
                <p className="text-xs font-semibold text-red-300">Log attack (Red Team)</p>
                <textarea
                  className="w-full font-mono text-xs bg-black/50 border border-gray-600 rounded p-2 text-green-200"
                  rows={3}
                  placeholder="Payload used"
                  value={attackPayload}
                  onChange={(e) => setAttackPayload(e.target.value)}
                />
                <textarea
                  className="w-full text-xs bg-black/50 border border-gray-600 rounded p-2 text-gray-200"
                  rows={2}
                  placeholder="Impact description"
                  value={attackImpact}
                  onChange={(e) => setAttackImpact(e.target.value)}
                />
                <button
                  type="button"
                  disabled={attackSubmitting}
                  onClick={submitAttack}
                  className="w-full py-2 rounded bg-red-700 hover:bg-red-600 text-sm font-semibold disabled:opacity-50"
                >
                  {attackSubmitting ? 'Logging…' : 'Log Attack'}
                </button>
              </div>
            )}
            <div className="flex-1 overflow-y-auto space-y-3 max-h-[500px] pr-1">
              {attacks.length === 0 && <p className="text-gray-500 text-sm">No attacks yet.</p>}
              {attacks.map((a) => (
                <div key={a.id} className="bg-gray-900 border border-gray-700 rounded p-3 text-sm">
                  <div className="text-gray-500 text-xs mb-1">{formatTime(a.timestamp)} · {challengeName}</div>
                  <pre className="text-xs font-mono text-green-300 whitespace-pre-wrap break-all mb-2 bg-black/40 p-2 rounded">
                    {truncatePayload(a.payload_used)}
                  </pre>
                  <p className="text-gray-300">{a.impact_description}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 flex flex-col">
            <h2 className="text-lg font-bold mb-3">Defense Console</h2>
            <textarea
              className="w-full font-mono text-sm bg-gray-950 border border-gray-600 rounded p-3 text-green-200"
              style={{ minHeight: 300 }}
              value={fixCode}
              onChange={(e) => setFixCode(e.target.value)}
              placeholder="Paste fixed code here…"
              disabled={!isBlueTeam || status !== 'active'}
            />
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
            <div className="flex justify-center">
              <button
                type="button"
                disabled={endLoading || status === 'completed'}
                onClick={endGame}
                className="px-6 py-3 rounded bg-amber-700 hover:bg-amber-600 disabled:opacity-40 font-semibold"
              >
                {endLoading ? 'Ending…' : 'End Game'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RedBlueGamePage;
