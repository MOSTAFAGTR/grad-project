import React, { useState } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

type HintState = {
  hint: string;
  level: number;
  penalty: number;
  remaining_levels: number;
  recommendation: string;
  attempts?: number;
  time_spent?: number;
};

interface Props {
  challengeId: string;
}

const ChallengeHintPanel: React.FC<Props> = ({ challengeId }) => {
  const [items, setItems] = useState<HintState[]>([]);
  const [completed, setCompleted] = useState(false);
  const [loading, setLoading] = useState(false);

  const getHint = async () => {
    const token = sessionStorage.getItem('token');
    if (!token || loading || completed) return;
    setLoading(true);
    try {
      const res = await axios.post(
        `${API_URL}/api/challenge/hint`,
        { challenge_id: challengeId, time_spent_delta: 5 },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      if (res.data?.hint || res.data?.hint_text) {
        setItems((prev) => [
          ...prev,
          {
            hint: res.data.hint_text || res.data.hint,
            level: res.data.level,
            penalty: res.data.penalty,
            remaining_levels: res.data.remaining_levels,
            recommendation: res.data.next_recommendation || res.data.recommendation,
            attempts: res.data.attempts,
            time_spent: res.data.time_spent,
          },
        ]);
      }
      setCompleted(Boolean(res.data?.completed) || Number(res.data?.remaining_levels || 0) <= 0);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-4 bg-gray-800 border border-gray-700 rounded p-3">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-bold text-blue-300">Hint Progression</h3>
        <button
          onClick={getHint}
          disabled={completed || loading}
          className="text-xs px-2 py-1 rounded bg-blue-600 hover:bg-blue-700 disabled:opacity-50 font-semibold"
        >
          {completed ? 'Max level reached' : loading ? 'Loading...' : 'Get Hint'}
        </button>
      </div>

      {items.length === 0 && <p className="text-xs text-gray-500">No hints used yet.</p>}
      <div className="space-y-2">
        {items.map((h, idx) => (
          <div key={`${h.level}-${idx}`} className="text-xs border border-gray-700 rounded p-2 bg-gray-900/60">
            <div className="flex justify-between items-center mb-1">
              <span className="text-blue-200 font-semibold">Hint Level {h.level}</span>
              <span className="text-amber-300">Penalty: -{h.penalty}</span>
            </div>
            <p className="text-gray-200">{h.hint}</p>
            <p className="text-gray-400 mt-1">Recommendation: {h.recommendation}</p>
            <p className="text-gray-500 mt-1">Remaining levels: {h.remaining_levels}</p>
            <p className="text-gray-500 mt-1">Attempts: {h.attempts ?? '-'} | Time tracked: {h.time_spent ?? '-'}s</p>
          </div>
        ))}
      </div>
      {!completed && (
        <p className="text-[11px] text-red-300 mt-2">
          Warning: higher hint levels reduce score/XP and can affect learning accuracy.
        </p>
      )}
    </div>
  );
};

export default ChallengeHintPanel;

