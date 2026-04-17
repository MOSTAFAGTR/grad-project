import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';

const CHALLENGES: { id: number; label: string }[] = [
  { id: 1, label: 'SQL Injection' },
  { id: 2, label: 'XSS' },
  { id: 3, label: 'CSRF' },
  { id: 4, label: 'Command Injection' },
  { id: 5, label: 'Broken Authentication' },
  { id: 6, label: 'Security Misconfiguration' },
  { id: 7, label: 'Insecure Storage' },
  { id: 8, label: 'Directory Traversal' },
  { id: 9, label: 'XXE' },
  { id: 10, label: 'Unvalidated Redirect' },
];

const RedBlueCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const [challengeId, setChallengeId] = useState(1);
  const [redName, setRedName] = useState('');
  const [blueName, setBlueName] = useState('');
  const [users, setUsers] = useState<{ id: number; email: string }[]>([]);
  const [redIds, setRedIds] = useState<Set<number>>(new Set());
  const [blueIds, setBlueIds] = useState<Set<number>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        await api.get('/api/redblue/games');
      } catch {
        /* optional */
      }
      try {
        const res = await api.get('/api/auth/users');
        const list = (res.data || []).filter((u: any) => u.role === 'user');
        setUsers(list.map((u: any) => ({ id: u.id, email: u.email })));
      } catch {
        setError('Could not load users.');
      }
    };
    load();
  }, []);

  const toggleRed = (id: number) => {
    setRedIds((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
    setBlueIds((prev) => {
      const n = new Set(prev);
      n.delete(id);
      return n;
    });
  };

  const toggleBlue = (id: number) => {
    if (redIds.has(id)) return;
    setBlueIds((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  };

  const onCreate = async () => {
    setError(null);
    if (!redName.trim() || !blueName.trim()) {
      setError('Red team name and blue team name are required.');
      return;
    }
    if (redIds.size < 1 || blueIds.size < 1) {
      setError('Select at least one member for each team.');
      return;
    }
    const overlap = [...redIds].filter((id) => blueIds.has(id));
    if (overlap.length) {
      setError('A student cannot be on both teams.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post('/api/redblue/game/create', {
        challenge_id: challengeId,
        red_team_name: redName.trim(),
        blue_team_name: blueName.trim(),
        red_member_ids: [...redIds],
        blue_member_ids: [...blueIds],
      });
      navigate(`/redblue/game/${res.data.game_id}`);
    } catch (e: any) {
      const d = e?.response?.data?.detail;
      setError(typeof d === 'string' ? d : e?.message || 'Create failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-purple-300">Create Red vs Blue Game</h1>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Challenge</label>
          <select
            className="w-full bg-gray-800 border border-gray-600 rounded p-2"
            value={challengeId}
            onChange={(e) => setChallengeId(Number(e.target.value))}
          >
            {CHALLENGES.map((c) => (
              <option key={c.id} value={c.id}>
                {c.id} - {c.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Red Team Name</label>
          <input
            className="w-full bg-gray-800 border border-gray-600 rounded p-2"
            placeholder="e.g. Team Alpha"
            value={redName}
            onChange={(e) => setRedName(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Blue Team Name</label>
          <input
            className="w-full bg-gray-800 border border-gray-600 rounded p-2"
            placeholder="e.g. Team Beta"
            value={blueName}
            onChange={(e) => setBlueName(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Red Team Members</label>
          <div className="bg-gray-800 border border-gray-600 rounded p-3 max-h-48 overflow-y-auto space-y-2">
            {users.map((u) => (
              <label key={`r-${u.id}`} className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="checkbox" checked={redIds.has(u.id)} onChange={() => toggleRed(u.id)} />
                <span>{u.email}</span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Blue Team Members</label>
          <div className="bg-gray-800 border border-gray-600 rounded p-3 max-h-48 overflow-y-auto space-y-2">
            {users.map((u) => (
              <label
                key={`b-${u.id}`}
                className={`flex items-center gap-2 text-sm ${redIds.has(u.id) ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}`}
              >
                <input
                  type="checkbox"
                  disabled={redIds.has(u.id)}
                  checked={blueIds.has(u.id)}
                  onChange={() => toggleBlue(u.id)}
                />
                <span>{u.email}</span>
              </label>
            ))}
          </div>
        </div>

        {error && <div className="text-red-400 text-sm">{error}</div>}

        <div>
          <button
            type="button"
            onClick={onCreate}
            disabled={submitting}
            className="w-full py-3 rounded-lg bg-purple-600 hover:bg-purple-500 font-bold disabled:opacity-50"
          >
            {submitting ? 'Creating…' : 'Create Game'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default RedBlueCreatePage;
