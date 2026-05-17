import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import { FaUserGraduate, FaChalkboardTeacher, FaClipboardCheck, FaSearch, FaTimes, FaChartPie } from 'react-icons/fa';
import { API_BASE_URL } from '../lib/api';

const RB_CHALLENGE_LABELS: Record<number, string> = {
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

const ASSIGNMENT_SLUGS: { value: string; label: string }[] = [
  { value: 'sql-injection', label: 'SQL Injection' },
  { value: 'xss', label: 'XSS' },
  { value: 'csrf', label: 'CSRF' },
  { value: 'command-injection', label: 'Command Injection' },
  { value: 'broken-auth', label: 'Broken Authentication' },
  { value: 'security-misc', label: 'Security Misconfiguration' },
  { value: 'insecure-storage', label: 'Insecure Storage' },
  { value: 'directory-traversal', label: 'Directory Traversal' },
  { value: 'xxe', label: 'XXE' },
  { value: 'redirect', label: 'Open Redirect' },
];

const InstructorDashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [stats, setStats] = useState<any>(null); // State for Real Stats

  const [selectedStudent, setSelectedStudent] = useState<any | null>(null);
  const [studentAnalytics, setStudentAnalytics] = useState<any | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [redBlueGames, setRedBlueGames] = useState<any[]>([]);
  const [rbLoading, setRbLoading] = useState(true);
  const [rbError, setRbError] = useState<string | null>(null);
  const [rbDeletingId, setRbDeletingId] = useState<number | null>(null);

  const [chAssignments, setChAssignments] = useState<any[]>([]);
  const [chLoadError, setChLoadError] = useState<string | null>(null);
  const [showChForm, setShowChForm] = useState(false);
  const [chFormTitle, setChFormTitle] = useState('');
  const [chFormSlug, setChFormSlug] = useState('sql-injection');
  const [chFormInstructions, setChFormInstructions] = useState('');
  const [chFormMinutes, setChFormMinutes] = useState(30);
  const [chFormDue, setChFormDue] = useState('');
  const [chStudentIds, setChStudentIds] = useState<Record<number, boolean>>({});
  const [chSubmitting, setChSubmitting] = useState(false);
  const [chBanner, setChBanner] = useState<string | null>(null);
  const [mistakesSendingFor, setMistakesSendingFor] = useState<number | null>(null);
  const [mistakesBanner, setMistakesBanner] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    const loadRb = async () => {
      try {
        const res = await api.get('/api/redblue/games');
        setRedBlueGames(res.data?.games || []);
        setRbError(null);
      } catch {
        setRedBlueGames([]);
        setRbError('Could not load games. Check server connection.');
      } finally {
        setRbLoading(false);
      }
    };
    loadRb();
  }, []);

  const deleteRedBlueGame = async (gameId: number) => {
    if (
      !window.confirm(
        'Delete this Red vs Blue game permanently? All attacks, fixes, scores, and team data will be removed.',
      )
    ) {
      return;
    }
    setRbDeletingId(Number(gameId));
    try {
      await api.post(`/api/redblue/game/${Number(gameId)}/delete`);
      setRedBlueGames((prev) => prev.filter((g) => Number(g.game_id) !== gameId));
    } catch (e) {
      let msg = 'Could not delete game.';
      if (axios.isAxiosError(e) && e.response) {
        const d = e.response.data as { detail?: string | unknown };
        const detail =
          typeof d?.detail === 'string'
            ? d.detail
            : Array.isArray(d?.detail)
              ? (d.detail as { msg?: string }[]).map((x) => x?.msg).filter(Boolean).join(', ')
              : '';
        msg = detail ? `${msg} (${e.response.status}): ${detail}` : `${msg} (HTTP ${e.response.status})`;
      }
      alert(msg);
    } finally {
      setRbDeletingId(null);
    }
  };

  const refreshChallengeAssignments = async () => {
    try {
      const res = await api.get('/api/challenge-assignments/instructor');
      setChAssignments(res.data || []);
      setChLoadError(null);
    } catch {
      setChAssignments([]);
      setChLoadError('Could not load challenge assignments.');
    }
  };

  useEffect(() => {
    refreshChallengeAssignments();
  }, []);

  useEffect(() => {
    if (!selectedStudent) {
      setStudentAnalytics(null);
      return;
    }
    const load = async () => {
      setAnalyticsLoading(true);
      try {
        const token = sessionStorage.getItem('token');
        const res = await axios.get(
          `${API_BASE_URL}/api/instructor/user/${selectedStudent.id}/analytics`,
          { headers: { Authorization: `Bearer ${token}` } },
        );
        setStudentAnalytics(res.data);
      } catch {
        setStudentAnalytics(null);
      } finally {
        setAnalyticsLoading(false);
      }
    };
    load();
  }, [selectedStudent]);

  const fetchData = async () => {
    try {
      const token = sessionStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      // 1. Fetch Students List
      const resUsers = await axios.get(`${API_BASE_URL}/api/auth/users`, { headers });
      setUsers(resUsers.data.filter((u: any) => u.role === 'user'));

      // 2. Fetch Instructor Stats (Real Data)
      const resStats = await axios.get(`${API_BASE_URL}/api/stats/instructor/dashboard`, { headers });
      setStats(resStats.data);

    } catch (err) { console.error(err); }
  };

  const filteredStudents = users.filter(u => u.email.toLowerCase().includes(searchTerm.toLowerCase()));
  const handleViewAnalytics = (student: any) => setSelectedStudent(student);

  const refreshStudentAnalytics = async () => {
    if (!selectedStudent) return;
    const token = sessionStorage.getItem('token');
    const res = await axios.get(
      `${API_BASE_URL}/api/instructor/user/${selectedStudent.id}/analytics`,
      { headers: { Authorization: `Bearer ${token}` } },
    );
    setStudentAnalytics(res.data);
  };

  const confirmResetProgress = async () => {
    if (!selectedStudent) return;
    setResetting(true);
    try {
      const token = sessionStorage.getItem('token');
      await axios.post(
        `${API_BASE_URL}/api/instructor/user/${selectedStudent.id}/reset-progress`,
        {},
        { headers: { Authorization: `Bearer ${token}` } },
      );
      setShowResetConfirm(false);
      await refreshStudentAnalytics();
    } catch {
      alert('Reset failed');
    } finally {
      setResetting(false);
    }
  };

  const sendMistakesToStudent = async (studentId: number, email: string) => {
    setMistakesSendingFor(studentId);
    setMistakesBanner(null);
    try {
      await api.post('/api/quizzes/assign-mistakes-quiz', { student_id: studentId, num_questions: 10 });
      setMistakesBanner(`Mistakes quiz assigned to ${email}.`);
      window.setTimeout(() => setMistakesBanner(null), 5000);
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { detail?: string } } };
      alert(ax.response?.data?.detail || 'Failed to assign mistakes quiz');
    } finally {
      setMistakesSendingFor(null);
    }
  };

  const submitChallengeAssignment = async () => {
    if (!chFormTitle.trim()) {
      alert('Title is required');
      return;
    }
    const ids = Object.entries(chStudentIds)
      .filter(([, v]) => v)
      .map(([k]) => Number(k));
    if (!ids.length) {
      alert('Select at least one student');
      return;
    }
    setChSubmitting(true);
    try {
      await api.post('/api/challenge-assignments/create', {
        challenge_slug: chFormSlug,
        title: chFormTitle.trim(),
        instructions: chFormInstructions.trim() || undefined,
        time_limit_minutes: chFormMinutes,
        due_date: chFormDue || undefined,
        student_ids: ids,
      });
      setShowChForm(false);
      setChFormTitle('');
      setChFormInstructions('');
      setChFormMinutes(30);
      setChFormDue('');
      setChBanner('Challenge assignment created.');
      window.setTimeout(() => setChBanner(null), 4000);
      await refreshChallengeAssignments();
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { detail?: string } } };
      alert(ax.response?.data?.detail || 'Create failed');
    } finally {
      setChSubmitting(false);
    }
  };

  const deactivateChAssignment = async (id: number) => {
    if (!window.confirm('Deactivate this assignment?')) return;
    try {
      await api.delete(`/api/challenge-assignments/${id}`);
      await refreshChallengeAssignments();
    } catch {
      alert('Deactivate failed');
    }
  };

  const totalCh = studentAnalytics?.total_challenges ?? 10;
  const solvedCh = studentAnalytics?.vulnerabilities_solved ?? 0;
  const studentProgressPct = Math.min(100, Math.round((solvedCh / totalCh) * 100));

  // Fallback if stats aren't loaded yet
  if (!stats) return <div className="p-10 text-white">Loading dashboard...</div>;

  // Mock data for Line Chart (since we don't have daily logs yet)
  const studentActivityData = [
    { day: 'Mon', active: 10 }, { day: 'Tue', active: 25 },
    { day: 'Wed', active: 15 }, { day: 'Thu', active: 35 },
    { day: 'Fri', active: 40 },
  ];

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-white relative">
      <h1 className="text-3xl font-bold mb-6 text-purple-400">Instructor Analytics</h1>
      {mistakesBanner && (
        <div className="mb-4 p-3 rounded-lg bg-teal-900/40 border border-teal-600 text-teal-100 text-sm">
          {mistakesBanner}
        </div>
      )}

      {/* Top Stats Cards (REAL DATA) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 shadow-lg">
          <div className="flex items-center gap-3 mb-2">
            <FaUserGraduate className="text-green-400 text-2xl" />
            <h3 className="text-gray-400 font-bold">Total Students</h3>
          </div>
          <p className="text-3xl font-bold">{stats.total_students}</p>
        </div>
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 shadow-lg">
          <div className="flex items-center gap-3 mb-2">
            <FaChalkboardTeacher className="text-blue-400 text-2xl" />
            <h3 className="text-gray-400 font-bold">Assignments Created</h3>
          </div>
          <p className="text-3xl font-bold">{stats.quizzes_created}</p>
        </div>
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 shadow-lg">
          <div className="flex items-center gap-3 mb-2">
            <FaClipboardCheck className="text-purple-400 text-2xl" />
            <h3 className="text-gray-400 font-bold">Questions in Bank</h3>
          </div>
          <p className="text-3xl font-bold">{stats.questions_in_bank}</p>
        </div>
      </div>

      {/* Main Charts Area */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h3 className="text-xl font-bold mb-4">Class Performance by Topic (Real Data)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.class_performance}>
                <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                <XAxis dataKey="name" stroke="#ccc" />
                <YAxis stroke="#ccc" />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }} />
                <Legend />
                <Bar dataKey="avgScore" fill="#8884d8" name="Avg Score %" />
                <Bar dataKey="completions" fill="#82ca9d" name="Total Completions" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h3 className="text-xl font-bold mb-4">Weekly Student Activity (Simulated)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={studentActivityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                <XAxis dataKey="day" stroke="#ccc" />
                <YAxis stroke="#ccc" />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }} />
                <Line type="monotone" dataKey="active" stroke="#ff7300" strokeWidth={3} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Student List Table */}
      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Student Directory</h2>
          <div className="relative">
            <FaSearch className="absolute left-3 top-3 text-gray-400" />
            <input
              className="bg-gray-700 rounded-full py-2 pl-10 pr-4 text-white outline-none focus:ring-2 focus:ring-blue-500 w-64"
              placeholder="Search email..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-gray-300">
            <thead className="bg-gray-700 text-gray-200 uppercase text-xs">
              <tr>
                <th className="px-6 py-3">ID</th>
                <th className="px-6 py-3">Student Email</th>
                <th className="px-6 py-3">Global Status</th>
                <th className="px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {filteredStudents.length === 0 ? (
                <tr><td colSpan={4} className="text-center py-4">No students found</td></tr>
              ) : (
                filteredStudents.map(student => (
                  <tr key={student.id} className="hover:bg-gray-700/50 transition">
                    <td className="px-6 py-4 text-gray-500">#{student.id}</td>
                    <td className="px-6 py-4 font-medium text-white">{student.email}</td>
                    <td className="px-6 py-4"><span className="text-green-400 bg-green-900/30 px-2 py-1 rounded text-xs">Enrolled</span></td>
                    <td className="px-6 py-4">
                      <button
                        type="button"
                        onClick={() => handleViewAnalytics(student)}
                        className="text-blue-400 hover:text-white hover:underline text-sm font-bold mr-3"
                      >
                        View Analytics
                      </button>
                      <button
                        type="button"
                        disabled={mistakesSendingFor === student.id}
                        onClick={() => sendMistakesToStudent(student.id, student.email)}
                        className="text-teal-400 hover:text-teal-200 text-sm font-bold disabled:opacity-50"
                      >
                        {mistakesSendingFor === student.id ? 'Sending…' : 'Send Mistakes Quiz'}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* --- STUDENT DETAILS MODAL --- */}
      {selectedStudent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-gray-800 w-full max-w-4xl rounded-xl border border-gray-600 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">

            {/* Modal Header */}
            <div className="p-6 border-b border-gray-700 flex justify-between items-center bg-gray-900">
              <div className="flex items-center gap-4">
                <div className="bg-blue-600 p-3 rounded-full text-white"><FaUserGraduate size={24} /></div>
                <div>
                  <h2 className="text-2xl font-bold text-white">Student Report</h2>
                  <p className="text-gray-400">{selectedStudent.email} (ID: {selectedStudent.id})</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setShowResetConfirm(false);
                  setSelectedStudent(null);
                }}
                className="text-gray-400 hover:text-white hover:bg-gray-700 p-2 rounded-full transition"
              >
                <FaTimes size={24} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-8 overflow-y-auto grid grid-cols-1 md:grid-cols-2 gap-8 relative">

              {analyticsLoading && (
                <div className="absolute inset-0 bg-gray-900/60 flex items-center justify-center z-10 text-white font-bold">
                  Loading analytics…
                </div>
              )}

              <div className="space-y-6">
                <div className="bg-gray-700/50 p-4 rounded-lg border border-gray-600">
                  <h3 className="text-gray-300 font-bold mb-2">Lab progress</h3>
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div className="p-3 bg-gray-800 rounded">
                      <p className="text-xs text-gray-400">Challenges solved</p>
                      <p className="text-2xl font-bold text-green-400">{solvedCh}/{totalCh}</p>
                    </div>
                    <div className="p-3 bg-gray-800 rounded">
                      <p className="text-xs text-gray-400">Level</p>
                      <p className="text-2xl font-bold text-yellow-400">{studentAnalytics?.level ?? '—'}</p>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">Class avg completion: {stats.avg_completion_rate}%</p>
                  <div className="mt-3 h-2 rounded bg-gray-900 overflow-hidden">
                    <div className="h-full bg-blue-500 transition-all" style={{ width: `${studentProgressPct}%` }} />
                  </div>
                  <p className="text-right text-xs text-gray-400 mt-1">{studentProgressPct}%</p>
                </div>

                <div className="bg-gray-700/50 p-4 rounded-lg border border-gray-600">
                  <h3 className="text-gray-300 font-bold mb-3 flex items-center gap-2">
                    <FaChartPie /> Skill radar (same as student dashboard)
                  </h3>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart cx="50%" cy="50%" outerRadius="80%" data={studentAnalytics?.skills_radar || []}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="subject" stroke="#ccc" />
                        <PolarRadiusAxis domain={[0, 100]} />
                        <Radar name="Skills" dataKey="value" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="bg-blue-900/20 p-4 rounded border border-blue-800">
                  <h4 className="text-blue-400 font-bold mb-2">Strongest / weakest</h4>
                  <p className="text-sm">
                    Strongest: <span className="text-green-300">{studentAnalytics?.strongest_category ?? '—'}</span>
                    <br />
                    Weakest: <span className="text-amber-300">{studentAnalytics?.weakest_category ?? '—'}</span>
                  </p>
                  {studentAnalytics?.recommendations?.[0] && (
                    <p className="text-sm text-gray-300 mt-2">{studentAnalytics.recommendations[0]}</p>
                  )}
                </div>

                <div className="mt-6 pt-6 border-t border-gray-700">
                  <h4 className="text-sm font-bold text-gray-400 mb-2">Instructor Actions</h4>
                  <div className="flex gap-2 flex-wrap">
                    <button type="button" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-bold">Message Student</button>
                    <button
                      type="button"
                      onClick={() => setShowResetConfirm(true)}
                      className="bg-red-700 hover:bg-red-600 text-white px-4 py-2 rounded text-sm font-bold"
                    >
                      Reset Progress
                    </button>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>
      )}

      <section className="mt-12 border-t border-gray-700 pt-8">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <h2 className="text-2xl font-bold text-white">Red vs Blue Games</h2>
          <button
            type="button"
            onClick={() => navigate('/redblue/create')}
            className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 font-semibold text-white"
          >
            Create New Game
          </button>
        </div>
        {rbError && (
          <p className="text-amber-300 mb-3 text-sm" role="alert">
            {rbError}
          </p>
        )}
        {rbLoading ? (
          <p className="text-gray-400">Loading games…</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-gray-700">
            <table className="min-w-full text-sm text-left text-gray-200">
              <thead className="bg-gray-800 text-gray-300">
                <tr>
                  <th className="px-3 py-2">Game ID</th>
                  <th className="px-3 py-2">Challenge</th>
                  <th className="px-3 py-2">Red Team</th>
                  <th className="px-3 py-2">Blue Team</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Red Score</th>
                  <th className="px-3 py-2">Blue Score</th>
                  <th className="px-3 py-2">Action</th>
                </tr>
              </thead>
              <tbody>
                {redBlueGames.length === 0 && !rbError && (
                  <tr>
                    <td colSpan={8} className="px-3 py-4 text-center text-gray-500">
                      No games created yet. Click &apos;Create New Game&apos; to start.
                    </td>
                  </tr>
                )}
                {redBlueGames.map((g) => (
                  <tr key={g.game_id} className="border-t border-gray-700 bg-gray-900/40">
                    <td className="px-3 py-2 font-mono">{g.game_id}</td>
                    <td className="px-3 py-2">{RB_CHALLENGE_LABELS[g.challenge_id] ?? g.challenge_id}</td>
                    <td className="px-3 py-2">{g.red_team_name}</td>
                    <td className="px-3 py-2">{g.blue_team_name}</td>
                    <td className="px-3 py-2 capitalize">{g.status}</td>
                    <td className="px-3 py-2">{g.red_score}</td>
                    <td className="px-3 py-2">{g.blue_score}</td>
                    <td className="px-3 py-2">
                      <div className="flex flex-wrap gap-2 items-center">
                        <button
                          type="button"
                          onClick={() => navigate(`/redblue/game/${g.game_id}`)}
                          className="text-purple-400 hover:text-purple-300 font-semibold"
                        >
                          View Game
                        </button>
                        <button
                          type="button"
                          disabled={rbDeletingId === Number(g.game_id)}
                          onClick={(ev) => {
                            ev.preventDefault();
                            ev.stopPropagation();
                            deleteRedBlueGame(Number(g.game_id));
                          }}
                          className="text-red-400 hover:text-red-300 font-semibold disabled:opacity-50"
                        >
                          {rbDeletingId === Number(g.game_id) ? 'Deleting…' : 'Delete'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="mt-12 border-t border-gray-700 pt-8">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <h2 className="text-2xl font-bold text-white">Challenge Assignments</h2>
          <button
            type="button"
            onClick={() => {
              setShowChForm(true);
              const init: Record<number, boolean> = {};
              users.filter((u: { role: string }) => u.role === 'user').forEach((u: { id: number }) => {
                init[u.id] = false;
              });
              setChStudentIds(init);
            }}
            className="px-4 py-2 rounded-lg bg-teal-600 hover:bg-teal-500 font-semibold"
          >
            Create Challenge Assignment
          </button>
        </div>
        {chBanner && (
          <p className="mb-3 text-sm text-teal-300 bg-teal-950/50 border border-teal-800 rounded px-3 py-2">{chBanner}</p>
        )}
        {chLoadError && <p className="text-amber-300 text-sm mb-2">{chLoadError}</p>}
        <div className="overflow-x-auto rounded-lg border border-gray-700">
          <table className="min-w-full text-sm text-left text-gray-200">
            <thead className="bg-gray-800 text-gray-300">
              <tr>
                <th className="px-3 py-2">Title</th>
                <th className="px-3 py-2">Challenge</th>
                <th className="px-3 py-2">Time Limit</th>
                <th className="px-3 py-2">Due Date</th>
                <th className="px-3 py-2">Students</th>
                <th className="px-3 py-2">Passed</th>
                <th className="px-3 py-2">Failed</th>
                <th className="px-3 py-2">Pending</th>
                <th className="px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {chAssignments.length === 0 && (
                <tr>
                  <td colSpan={9} className="px-3 py-4 text-center text-gray-500">
                    No challenge assignments yet.
                  </td>
                </tr>
              )}
              {chAssignments.map((row) => (
                <tr key={row.id} className="border-t border-gray-700 bg-gray-900/40">
                  <td className="px-3 py-2 font-medium">{row.title}</td>
                  <td className="px-3 py-2">{row.challenge_name || row.challenge_slug}</td>
                  <td className="px-3 py-2">{row.time_limit_minutes} min</td>
                  <td className="px-3 py-2">{row.due_date ? new Date(row.due_date).toLocaleString() : '—'}</td>
                  <td className="px-3 py-2">{row.total_students}</td>
                  <td className="px-3 py-2 text-green-400">{row.passed_count}</td>
                  <td className="px-3 py-2 text-red-400">{row.failed_count}</td>
                  <td className="px-3 py-2 text-amber-200">{row.not_started_count + row.in_progress_count}</td>
                  <td className="px-3 py-2 space-x-2 whitespace-nowrap">
                    <button
                      type="button"
                      onClick={() => navigate(`/instructor/assignment/${row.id}/results`)}
                      className="text-purple-400 hover:underline font-semibold"
                    >
                      View Results
                    </button>
                    <button
                      type="button"
                      onClick={() => deactivateChAssignment(row.id)}
                      className="text-red-400 hover:underline font-semibold"
                    >
                      Deactivate
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {showChForm && (
          <div className="fixed inset-0 z-[70] bg-black/80 flex items-center justify-center p-4 overflow-y-auto">
            <div className="bg-gray-800 border border-gray-600 rounded-xl max-w-lg w-full p-6 shadow-2xl my-8">
              <h3 className="text-xl font-bold mb-4">Create Challenge Assignment</h3>
              <label className="block text-sm text-gray-400 mb-1">Title *</label>
              <input
                className="w-full mb-3 bg-gray-900 border border-gray-600 rounded px-3 py-2"
                value={chFormTitle}
                onChange={(e) => setChFormTitle(e.target.value)}
              />
              <label className="block text-sm text-gray-400 mb-1">Challenge</label>
              <select
                className="w-full mb-3 bg-gray-900 border border-gray-600 rounded px-3 py-2"
                value={chFormSlug}
                onChange={(e) => setChFormSlug(e.target.value)}
              >
                {ASSIGNMENT_SLUGS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
              <label className="block text-sm text-gray-400 mb-1">Instructions (optional)</label>
              <textarea
                className="w-full mb-3 bg-gray-900 border border-gray-600 rounded px-3 py-2 min-h-[80px]"
                value={chFormInstructions}
                onChange={(e) => setChFormInstructions(e.target.value)}
              />
              <label className="block text-sm text-gray-400 mb-1">Time limit (minutes, 10–240)</label>
              <input
                type="number"
                min={10}
                max={240}
                className="w-full mb-3 bg-gray-900 border border-gray-600 rounded px-3 py-2"
                value={chFormMinutes}
                onChange={(e) => setChFormMinutes(Number(e.target.value))}
              />
              <label className="block text-sm text-gray-400 mb-1">Due date (optional)</label>
              <input
                type="datetime-local"
                className="w-full mb-3 bg-gray-900 border border-gray-600 rounded px-3 py-2"
                value={chFormDue}
                onChange={(e) => setChFormDue(e.target.value)}
              />
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-400">Assign to students</span>
                <button
                  type="button"
                  className="text-xs text-teal-400 underline"
                  onClick={() => {
                    const next = { ...chStudentIds };
                    const all = filteredStudents.length > 0 ? filteredStudents : users.filter((u) => u.role === 'user');
                    const allOn = all.every((u: { id: number }) => next[u.id]);
                    all.forEach((u: { id: number }) => {
                      next[u.id] = !allOn;
                    });
                    setChStudentIds(next);
                  }}
                >
                  Select all (filtered)
                </button>
              </div>
              <div className="max-h-40 overflow-y-auto border border-gray-600 rounded p-2 bg-gray-900 mb-4 space-y-1">
                {(filteredStudents.length ? filteredStudents : users.filter((u) => u.role === 'user')).map(
                  (u: { id: number; email: string }) => (
                    <label key={u.id} className="flex items-center gap-2 text-sm cursor-pointer">
                      <input
                        type="checkbox"
                        checked={!!chStudentIds[u.id]}
                        onChange={(e) => setChStudentIds((prev) => ({ ...prev, [u.id]: e.target.checked }))}
                      />
                      {u.email}
                    </label>
                  ),
                )}
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowChForm(false)}
                  className="px-4 py-2 rounded bg-gray-700 hover:bg-gray-600"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={chSubmitting}
                  onClick={submitChallengeAssignment}
                  className="px-4 py-2 rounded bg-teal-600 hover:bg-teal-500 disabled:opacity-50 font-bold"
                >
                  {chSubmitting ? 'Creating…' : 'Create Assignment'}
                </button>
              </div>
            </div>
          </div>
        )}
      </section>

      {showResetConfirm && selectedStudent && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 p-4">
          <div className="bg-gray-800 border border-gray-600 rounded-lg p-6 max-w-md w-full shadow-xl">
            <h3 className="text-xl font-bold text-white mb-2">Reset student progress?</h3>
            <p className="text-gray-300 text-sm mb-4">
              This clears lab progress, quiz attempts, answers, and learning stats for {selectedStudent.email}. This cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowResetConfirm(false)}
                className="px-4 py-2 rounded bg-gray-700 text-white hover:bg-gray-600"
                disabled={resetting}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmResetProgress}
                className="px-4 py-2 rounded bg-red-600 text-white hover:bg-red-500 disabled:opacity-50"
                disabled={resetting}
              >
                {resetting ? 'Resetting…' : 'Confirm reset'}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default InstructorDashboardPage;