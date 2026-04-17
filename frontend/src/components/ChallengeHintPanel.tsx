import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { FaBrain } from 'react-icons/fa';
import AttackReplayVisualizer from './AttackReplayVisualizer';
import { api } from '../lib/api';

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
  const [showReplay, setShowReplay] = useState(false);
  const [mentorQuestion, setMentorQuestion] = useState('');
  const [mentorLoading, setMentorLoading] = useState(false);
  const [mentorReply, setMentorReply] = useState<string | null>(null);
  const [mentorFallback, setMentorFallback] = useState(false);
  const [mentorError, setMentorError] = useState<string | null>(null);

  useEffect(() => {
    setMentorQuestion('');
    setMentorReply(null);
    setMentorFallback(false);
    setMentorError(null);
  }, [challengeId]);

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

  const askMentor = async () => {
    const q = mentorQuestion.trim();
    if (!q) return;
    setMentorLoading(true);
    setMentorError(null);
    setMentorReply(null);
    try {
      const res = await api.post('/api/ai/mentor-chat', {
        challenge_id: challengeId,
        question: q,
        context: 'hint_panel',
      });
      const data = res.data as { response?: string; fallback?: boolean };
      setMentorFallback(Boolean(data.fallback));
      setMentorReply(data.response || '');
    } catch {
      setMentorError('AI mentor is temporarily unavailable.');
    } finally {
      setMentorLoading(false);
    }
  };

  return (
    <div style={{ position: 'relative' }}>
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
              <p className="text-gray-500 mt-1">
                Attempts: {h.attempts ?? '-'} | Time tracked: {h.time_spent ?? '-'}s
              </p>
            </div>
          ))}
        </div>
        {!completed && (
          <p className="text-[11px] text-red-300 mt-2">
            Warning: higher hint levels reduce score/XP and can affect learning accuracy.
          </p>
        )}

        <div className="mt-4 pt-3 border-t border-gray-700">
          <p className="text-xs font-semibold text-amber-200 mb-2">Still stuck? Watch the attack replay</p>
          <button
            type="button"
            onClick={() => setShowReplay(true)}
            className="text-xs px-3 py-2 rounded bg-gray-700 hover:bg-gray-600 text-gray-200"
          >
            Show Sample Replay
          </button>
        </div>

        <div className="mt-6 pt-4 border-t border-gray-700">
          <h3 className="text-sm font-bold text-indigo-300 mb-2 flex items-center gap-2">
            <FaBrain className="text-indigo-400" /> AI Mentor
          </h3>
          <textarea
            value={mentorQuestion}
            onChange={(e) => setMentorQuestion(e.target.value)}
            placeholder="Ask the AI mentor about this challenge... e.g. 'Why isn't my payload working?'"
            className="w-full min-h-[80px] bg-gray-950 border border-gray-600 rounded p-2 text-sm font-mono text-gray-200 placeholder:text-gray-500"
          />
          <button
            type="button"
            disabled={!mentorQuestion.trim() || mentorLoading}
            onClick={askMentor}
            className="mt-2 w-full py-2 rounded bg-indigo-700 hover:bg-indigo-600 disabled:opacity-40 text-sm font-semibold"
          >
            {mentorLoading ? 'Thinking...' : 'Ask AI Mentor'}
          </button>
          {mentorError && <p className="text-red-400 text-xs mt-2">{mentorError}</p>}
          {mentorReply !== null && mentorFallback && (
            <p className="text-amber-300 text-sm mt-3 border border-amber-800/60 bg-amber-950/30 p-2 rounded">
              AI mentor not configured: {mentorReply}
            </p>
          )}
          {mentorReply !== null && !mentorFallback && (
            <div className="mt-3 p-3 rounded-lg bg-gray-950 border border-gray-600 text-gray-100">
              <p className="text-xs font-semibold text-gray-400 mb-1">AI Mentor says:</p>
              <p className="text-sm italic whitespace-pre-wrap">{mentorReply}</p>
            </div>
          )}
        </div>
      </div>

      {showReplay && (
        <AttackReplayVisualizer challengeSlug={challengeId} isSample onClose={() => setShowReplay(false)} />
      )}
    </div>
  );
};

export default ChallengeHintPanel;
