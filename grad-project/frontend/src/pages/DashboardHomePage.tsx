import React, { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { FaShieldAlt, FaBug, FaTrophy, FaArrowRight, FaClipboardList } from 'react-icons/fa';
import { api } from '../lib/api';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ProgressItem {
  challenge_id: string;
}

interface QuizAttempt {
  id: number;
  title: string;
  score: number;
  total: number;
  time_seconds: number;
  completed_at: string;
}

interface ChallengeDetailRow {
  slug: string;
  label: string;
  category: string;
  color: string;
  completed: boolean;
  value: number;
}

interface LearningProgress {
  vulnerabilities_solved: number;
  total_challenges?: number;
  failed_attempts: number;
  accuracy: number;
  avg_time: number;
  strongest_category: string;
  weakest_category: string;
  level: string;
  streak_days: number;
  learning_speed: number;
  retention_score: number;
  skills?: Record<string, number>;
  skills_radar?: Array<{ subject: string; value: number }>;
  recommendations: string[];
  challenge_detail?: ChallengeDetailRow[];
}

const TOTAL_CHALLENGES = 10;

function categoryBadgeClass(cat: string): string {
  const m: Record<string, string> = {
    Injection: 'bg-red-600/90 text-white',
    'Client-Side': 'bg-orange-600/90 text-white',
    Auth: 'bg-purple-600/90 text-white',
    Config: 'bg-cyan-600/90 text-white',
    Storage: 'bg-green-600/90 text-white',
    Path: 'bg-blue-600/90 text-white',
    Validation: 'bg-lime-600/90 text-gray-900',
  };
  return m[cat] || 'bg-gray-600 text-white';
}

const DashboardHomePage: React.FC = () => {
  const navigate = useNavigate();
  const [userEmail, setUserEmail] = useState('');
  const [progressCount, setProgressCount] = useState(0);
  const [quizAttempts, setQuizAttempts] = useState<QuizAttempt[]>([]);
  const [learning, setLearning] = useState<LearningProgress | null>(null);
  const [challengeDetail, setChallengeDetail] = useState<ChallengeDetailRow[]>([]);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [reportError, setReportError] = useState('');
  const [aiFeaturesActive, setAiFeaturesActive] = useState(false);
  const [deletingSlug, setDeletingSlug] = useState<string | null>(null);
  const [deleteFlash, setDeleteFlash] = useState<string | null>(null);
  const [activeRbGames, setActiveRbGames] = useState<
    Array<{
      game_id: number;
      challenge_name: string;
      my_team_name: string;
      my_team: string;
    }>
  >([]);

  useEffect(() => {
    const email = sessionStorage.getItem('user_email') || sessionStorage.getItem('role') || 'Student';
    setUserEmail(email);
    const token = sessionStorage.getItem('token');
    if (token) {
      axios
        .get(`${API_URL}/api/challenges/progress`, { headers: { Authorization: `Bearer ${token}` } })
        .then((res) => {
          const items = res.data as ProgressItem[];
          setProgressCount(new Set(items.map((item) => item.challenge_id)).size);
        })
        .catch(() => {});
      axios
        .get(`${API_URL}/api/quizzes/attempts`, { headers: { Authorization: `Bearer ${token}` } })
        .then((res) => setQuizAttempts(res.data as QuizAttempt[]))
        .catch(() => {});
      axios
        .get(`${API_URL}/api/stats/progress/me`, { headers: { Authorization: `Bearer ${token}` } })
        .then((res) => {
          const data = res.data as LearningProgress;
          setLearning(data);
          setChallengeDetail(data.challenge_detail || []);
        })
        .catch(() => {});
      api
        .get('/api/ai/status')
        .then((res) => {
          if (res.data?.ai_available) setAiFeaturesActive(true);
        })
        .catch(() => {});
    }
  }, []);

  useEffect(() => {
    const role = sessionStorage.getItem('role');
    if (role !== 'user') return;
    api
      .get('/api/redblue/my-games')
      .then((res) => {
        const games = (res.data?.games || []).filter((g: { status?: string }) => g.status === 'active');
        setActiveRbGames(games);
      })
      .catch(() => {});
  }, []);

  const totalLabs = learning?.total_challenges ?? TOTAL_CHALLENGES;
  const solvedLabs = learning?.vulnerabilities_solved ?? progressCount;
  const progressPercent = Math.min(100, Math.round((solvedLabs / totalLabs) * 100));
  const activeRemaining = Math.max(0, totalLabs - solvedLabs);

  const latestQuiz = quizAttempts[0];
  const avgScorePercent = quizAttempts.length > 0
    ? Math.round(
        quizAttempts.reduce((sum, attempt) => sum + (attempt.score / attempt.total) * 100, 0) /
          quizAttempts.length
      )
    : 0;
  const currentXp = solvedLabs * 100 + (quizAttempts.length ? avgScorePercent : 0);
  const avgTimeSeconds = quizAttempts.length > 0
    ? Math.round(quizAttempts.reduce((s, a) => s + a.time_seconds, 0) / quizAttempts.length)
    : 0;
  const formatTime = (s: number) => (s >= 60 ? `${Math.floor(s / 60)}m ${s % 60}s` : `${s}s`);

  const completedCount = challengeDetail.filter((c) => c.completed).length;
  const remainingCount = totalLabs - completedCount;

  const categorySummary = useMemo(() => {
    const map = new Map<string, { done: number; total: number }>();
    for (const c of challengeDetail) {
      const g = map.get(c.category) || { done: 0, total: 0 };
      g.total += 1;
      if (c.completed) g.done += 1;
      map.set(c.category, g);
    }
    return Array.from(map.entries());
  }, [challengeDetail]);

  const handleResetChallenge = async (slug: string, label: string) => {
    if (
      !window.confirm(
        `Are you sure you want to reset your progress for ${label}? This will remove your completion record and reset your attempt history.`,
      )
    ) {
      return;
    }
    setDeletingSlug(slug);
    try {
      await api.delete(`/api/challenges/progress/${encodeURIComponent(slug)}`);
      const token = sessionStorage.getItem('token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const [progRes, learnRes] = await Promise.all([
        axios.get<ProgressItem[]>(`${API_URL}/api/challenges/progress`, { headers }),
        axios.get<LearningProgress>(`${API_URL}/api/stats/progress/me`, { headers }),
      ]);
      setProgressCount(new Set(progRes.data.map((p) => p.challenge_id)).size);
      setLearning(learnRes.data);
      setChallengeDetail(learnRes.data.challenge_detail || []);
      setDeleteFlash(slug);
      window.setTimeout(() => setDeleteFlash(null), 4000);
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { detail?: string } } };
      alert(ax.response?.data?.detail || 'Failed to reset progress');
    } finally {
      setDeletingSlug(null);
    }
  };

  const handleDownloadReport = async () => {
    setIsGeneratingReport(true);
    setReportError('');
    try {
      const response = await api.get('/api/report/pdf', { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const href = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = href;
      anchor.download = 'pentest_report.pdf';
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      URL.revokeObjectURL(href);
    } catch {
      setReportError('No scan found. Please scan a project before generating a report.');
      window.setTimeout(() => setReportError(''), 4000);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  return (
    <div className="relative min-h-screen text-white bg-gray-900 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-12">
          <h1 className="text-5xl font-extrabold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
            Welcome back, {userEmail}
          </h1>
          <p className="text-xl text-gray-300">
            Your secure coding journey continues. You have{' '}
            <span className="text-yellow-400 font-bold">
              {activeRemaining} challenge{activeRemaining === 1 ? '' : 's'}
            </span>{' '}
            left in the core lab set ({totalLabs} total).
          </p>
        </div>

        {activeRbGames.map((g) => (
          <div
            key={g.game_id}
            className="rounded-xl px-5 py-3 mb-4 flex flex-wrap items-center justify-between gap-3"
            style={{ backgroundColor: '#fbbf24', color: '#1f2937' }}
          >
            <p className="text-sm font-medium flex-1 min-w-[200px]">
              You have an active Red vs Blue game! Challenge: {g.challenge_name} — Team: {g.my_team_name} (
              {g.my_team === 'red' ? 'RED' : 'BLUE'} team)
            </p>
            <button
              type="button"
              onClick={() => navigate(`/redblue/game/${g.game_id}`)}
              className="px-4 py-2 rounded-lg font-semibold bg-gray-900 text-amber-100 hover:bg-gray-800 shrink-0"
            >
              Go to Game →
            </button>
          </div>
        ))}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-xl hover:border-blue-500 transition duration-300">
            <div className="flex items-center gap-4 mb-2">
              <div className="p-3 bg-blue-900/50 rounded-lg text-blue-400">
                <FaShieldAlt size={24} />
              </div>
              <h3 className="text-xl font-bold">Defense Level</h3>
            </div>
            <p className="text-3xl font-bold">{learning?.level || 'Beginner'}</p>
            <p className="text-sm text-gray-400 mt-1">Keep fixing to rank up</p>
          </div>

          <Link
            to="/challenges"
            className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-xl hover:border-purple-500 transition duration-300 cursor-pointer block"
          >
            <div className="flex items-center gap-4 mb-2">
              <div className="p-3 bg-purple-900/50 rounded-lg text-purple-400">
                <FaBug size={24} />
              </div>
              <h3 className="text-xl font-bold">Vulnerabilities</h3>
            </div>
            <p className="text-3xl font-bold">
              {solvedLabs}/{totalLabs}
            </p>
            <p className="text-sm text-gray-400 mt-1">Patched successfully · Click to view Labs &amp; Attacks</p>
          </Link>

          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-xl hover:border-yellow-500 transition duration-300">
            <div className="flex items-center gap-4 mb-2">
              <div className="p-3 bg-yellow-900/50 rounded-lg text-yellow-400">
                <FaTrophy size={24} />
              </div>
              <h3 className="text-xl font-bold">Current Score</h3>
            </div>
            <p className="text-3xl font-bold">{currentXp} XP</p>
            <p className="text-sm text-gray-400 mt-1">Challenges + quiz scores</p>
          </div>

          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-xl hover:border-teal-500 transition duration-300">
            <div className="flex items-center gap-4 mb-2">
              <div className="p-3 bg-teal-900/50 rounded-lg text-teal-400">
                <FaClipboardList size={24} />
              </div>
              <h3 className="text-xl font-bold">Quiz Results</h3>
            </div>
            <p className="text-3xl font-bold">
              {latestQuiz ? `${Math.round((latestQuiz.score / latestQuiz.total) * 100)}%` : '—'}
            </p>
            <p className="text-sm text-gray-400 mt-1">
              {quizAttempts.length > 0
                ? `Overall average: ${avgScorePercent}% · Avg time: ${formatTime(avgTimeSeconds)}`
                : 'No quizzes yet'}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-gray-800/50 p-8 rounded-xl border border-gray-700">
            <h2 className="text-2xl font-bold mb-6">Continue Learning</h2>

            <div className="space-y-4">
              <div className="group relative bg-gray-800 p-4 rounded-lg hover:bg-gray-700 transition cursor-pointer border-l-4 border-blue-500">
                <Link to="/challenges/1/tutorial" className="flex justify-between items-center">
                  <div>
                    <h4 className="font-bold text-lg">SQL Injection (SQLi)</h4>
                    <p className="text-sm text-gray-400">Phase: Tutorial & Attack</p>
                  </div>
                  <FaArrowRight className="text-blue-400 group-hover:translate-x-1 transition" />
                </Link>
              </div>

              <div className="group relative bg-gray-800 p-4 rounded-lg hover:bg-gray-700 transition cursor-pointer border-l-4 border-purple-500">
                <Link to="/challenges/2/tutorial" className="flex justify-between items-center">
                  <div>
                    <h4 className="font-bold text-lg">Cross-Site Scripting (XSS)</h4>
                    <p className="text-sm text-gray-400">Phase: Code Fix</p>
                  </div>
                  <FaArrowRight className="text-purple-400 group-hover:translate-x-1 transition" />
                </Link>
              </div>
            </div>
          </div>

          <div className="bg-gray-800/50 p-8 rounded-xl border border-gray-700 flex flex-col justify-center">
            <h2 className="text-2xl font-bold mb-4">Overall Progress</h2>
            <div className="relative pt-1">
              <div className="flex mb-2 items-center justify-between">
                <div className="text-right">
                  <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-blue-600 bg-blue-200">
                    In Progress
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-xs font-semibold inline-block text-blue-600">{progressPercent}%</span>
                </div>
              </div>
              <div className="overflow-hidden h-4 mb-4 text-xs flex rounded bg-blue-200/20">
                <div
                  style={{ width: `${progressPercent}%` }}
                  className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-blue-500 transition-all duration-1000 ease-out"
                />
              </div>
            </div>
            <p className="text-gray-300 text-sm">
              Accuracy: <span className="text-blue-300">{learning?.accuracy ?? 0}%</span>
            </p>
            <p className="text-gray-300 text-sm mt-1">
              Streak: <span className="text-green-300">{learning?.streak_days ?? 0} days</span>
            </p>
            <p className="text-gray-300 text-sm mt-1">
              Learning speed: <span className="text-cyan-300">{learning?.learning_speed ?? 0}</span>
            </p>
            <p className="text-gray-400 text-sm mt-4">
              Weakest area: <span className="text-amber-300">{learning?.weakest_category || 'N/A'}</span>
            </p>
            <p className="text-gray-400 text-sm mt-1">
              Strongest area: <span className="text-green-300">{learning?.strongest_category || 'N/A'}</span>
            </p>
            <p className="text-gray-400 text-sm mt-1">
              Avg quiz time: <span className="text-blue-300">{Math.round(learning?.avg_time || 0)}s</span>
            </p>
            {learning?.recommendations?.[0] && (
              <p className="text-gray-300 text-sm mt-3 bg-gray-800 p-2 rounded border border-gray-700">
                Recommendation: {learning.recommendations[0]}
              </p>
            )}
          </div>

          <div className="lg:col-span-2 bg-gray-800/50 p-6 rounded-xl border border-gray-700">
            <h2 className="text-xl font-bold mb-3">Penetration Test Report</h2>
            <p className="text-gray-400 text-sm mb-4">
              Export your latest scan and remediation progress as a professional PDF report.
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={handleDownloadReport}
                disabled={isGeneratingReport}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed px-6 py-3 rounded font-bold transition"
              >
                {isGeneratingReport ? 'Generating...' : 'Download Pentest Report'}
              </button>
              {aiFeaturesActive && (
                <span className="text-xs px-2 py-1 rounded-full bg-emerald-900/60 text-emerald-300 border border-emerald-700">
                  AI Features Active
                </span>
              )}
            </div>
            {reportError && <p className="text-red-400 text-sm mt-3">{reportError}</p>}
          </div>

          <div className="lg:col-span-2 bg-gray-800/50 p-8 rounded-xl border border-gray-700">
            <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
              <FaClipboardList className="text-teal-400" />
              Recent Quiz Attempts
            </h2>
            {quizAttempts.length === 0 ? (
              <p className="text-gray-500">
                No quiz attempts yet.{' '}
                <Link to="/quiz" className="text-teal-400 hover:underline">
                  Take a quiz
                </Link>{' '}
                to get started.
              </p>
            ) : (
              <div className="space-y-3">
                {quizAttempts.slice(0, 5).map((a) => (
                  <div
                    key={a.id}
                    className="bg-gray-800 p-4 rounded-lg border border-gray-700 flex justify-between items-center"
                  >
                    <span className="font-medium truncate flex-1 mr-4">{a.title}</span>
                    <span className="text-teal-400 font-bold shrink-0">{Math.round((a.score / a.total) * 100)}%</span>
                    <span className="text-gray-500 text-sm shrink-0 ml-2">{formatTime(a.time_seconds)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="lg:col-span-2 bg-gray-800/50 p-8 rounded-xl border border-gray-700">
            <h2 className="text-2xl font-bold mb-1">Challenge Mastery</h2>
            <p className="text-gray-400 text-sm mb-6">Your progress across all 10 vulnerability types</p>

            <div className="flex flex-wrap gap-3 mb-8">
              <span
                className={`px-4 py-2 rounded-full text-sm font-semibold ${
                  completedCount > 0 ? 'bg-emerald-900/50 text-emerald-300 border border-emerald-700' : 'bg-gray-800 text-gray-400 border border-gray-600'
                }`}
              >
                {completedCount} / 10 Completed
              </span>
              <span
                className={`px-4 py-2 rounded-full text-sm font-semibold ${
                  remainingCount > 0 ? 'bg-amber-900/40 text-amber-200 border border-amber-700' : 'bg-emerald-900/50 text-emerald-300 border border-emerald-700'
                }`}
              >
                {remainingCount} Remaining
              </span>
            </div>

            <div className="space-y-4 mb-10">
              {challengeDetail.map((ch) => (
                <div key={ch.slug} className="flex items-center gap-3 flex-wrap sm:flex-nowrap">
                  <span
                    className={`text-[10px] uppercase font-bold px-2 py-1 rounded shrink-0 ${categoryBadgeClass(ch.category)}`}
                  >
                    {ch.category}
                  </span>
                  <span
                    className="text-[13px] text-gray-200 w-[140px] shrink-0 text-right truncate"
                    title={ch.label}
                  >
                    {ch.label}
                  </span>
                  <div className="flex-1 min-w-[120px] h-3 rounded-md bg-[#1f2937] overflow-hidden">
                    <div
                      className="h-full transition-all duration-[600ms] ease-out rounded-md"
                      style={{
                        width: ch.completed ? '100%' : '0%',
                        backgroundColor: ch.color,
                        opacity: 0.85,
                      }}
                    />
                  </div>
                  <span className="w-[72px] text-right text-sm shrink-0">
                    {ch.completed ? <span className="text-emerald-400">✓ Done</span> : <span className="text-gray-500">Pending</span>}
                  </span>
                  {ch.completed && (
                    <button
                      type="button"
                      disabled={deletingSlug === ch.slug}
                      onClick={() => handleResetChallenge(ch.slug, ch.label)}
                      className="text-xs px-2 py-1 rounded border border-red-600 text-red-400 hover:bg-red-950/50 disabled:opacity-50 shrink-0"
                    >
                      {deletingSlug === ch.slug ? '…' : 'Reset'}
                    </button>
                  )}
                </div>
              ))}
            </div>

            {deleteFlash && (
              <p className="text-emerald-400 text-sm mb-4">
                Progress reset for {challengeDetail.find((c) => c.slug === deleteFlash)?.label || deleteFlash}.
              </p>
            )}

            <h3 className="text-sm font-bold text-gray-300 mb-3">By category</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {categorySummary.map(([cat, { done, total }]) => (
                <div key={cat} className="bg-gray-900/60 border border-gray-700 rounded-lg p-3">
                  <p className="font-bold text-gray-100">{cat}</p>
                  <p className="text-sm text-gray-400 mb-2">
                    {done} / {total} completed
                  </p>
                  <div className="h-2 rounded-md bg-[#1f2937] overflow-hidden">
                    <div
                      className="h-full rounded-md transition-all duration-500"
                      style={{
                        width: total ? `${(done / total) * 100}%` : '0%',
                        backgroundColor: '#60a5fa',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>

            <p className="text-gray-400 text-sm mt-6">
              Retention score: <span className="text-blue-300">{learning?.retention_score ?? 0}</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardHomePage;
