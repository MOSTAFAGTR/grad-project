import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../lib/api';

interface ResultsResponse {
  assignment: {
    id: number;
    title: string;
    challenge_slug: string;
    time_limit_minutes: number;
    due_date: string | null;
  };
  students: Array<{
    email: string;
    status: string;
    time_used_seconds: number | null;
    sandbox_passed: boolean | null;
    score: number | null;
    submitted_at: string | null;
  }>;
}

const InstructorAssignmentResultsPage: React.FC = () => {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const aid = Number(assignmentId);
  const navigate = useNavigate();
  const [data, setData] = useState<ResultsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!assignmentId || Number.isNaN(aid)) return;
    api
      .get<ResultsResponse>(`/api/challenge-assignments/${aid}/results`)
      .then((res) => setData(res.data))
      .catch((e: { response?: { data?: { detail?: string } } }) => {
        setError(e?.response?.data?.detail || 'Failed to load results');
      });
  }, [aid, assignmentId]);

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 text-red-300 p-8">
        {error}{' '}
        <button type="button" className="ml-4 underline" onClick={() => navigate('/instructor/dashboard')}>
          Back
        </button>
      </div>
    );
  }
  if (!data) {
    return <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">Loading…</div>;
  }

  const { assignment, students } = data;
  const passed = students.filter((s) => s.status === 'passed').length;
  const times = students.map((s) => s.time_used_seconds || 0).filter((t) => t > 0);
  const avgTime = times.length ? Math.round(times.reduce((a, b) => a + b, 0) / times.length) : 0;

  const badge = (s: string) => {
    const c =
      s === 'passed'
        ? 'bg-green-900/50 text-green-300'
        : s === 'failed'
          ? 'bg-red-900/50 text-red-300'
          : s === 'expired'
            ? 'bg-gray-700 text-gray-300'
            : s === 'in_progress'
              ? 'bg-blue-900/50 text-blue-300'
              : 'bg-amber-900/50 text-amber-200';
    return <span className={`px-2 py-0.5 rounded text-xs font-semibold ${c}`}>{s}</span>;
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <button
        type="button"
        onClick={() => navigate('/instructor/dashboard')}
        className="mb-4 text-sm text-teal-400 hover:underline"
      >
        ← Back to dashboard
      </button>
      <h1 className="text-2xl font-bold mb-2">{assignment.title}</h1>
      <p className="text-gray-400 text-sm mb-1">
        Challenge: <span className="text-gray-200">{assignment.challenge_slug}</span>
      </p>
      <p className="text-gray-400 text-sm mb-1">Time limit: {assignment.time_limit_minutes} minutes</p>
      {assignment.due_date && (
        <p className="text-gray-400 text-sm mb-6">
          Due: {new Date(assignment.due_date).toLocaleString()}
        </p>
      )}

      <div className="mb-6 p-4 rounded-lg bg-gray-800 border border-gray-700 flex flex-wrap gap-6">
        <div>
          <p className="text-xs text-gray-500">Passed</p>
          <p className="text-xl font-bold text-green-400">
            {passed}/{students.length}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Avg. time (submitted)</p>
          <p className="text-xl font-bold text-blue-300">{avgTime}s</p>
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border border-gray-700">
        <table className="min-w-full text-sm text-left">
          <thead className="bg-gray-800 text-gray-300">
            <tr>
              <th className="px-3 py-2">Student email</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Time used</th>
              <th className="px-3 py-2">Score</th>
              <th className="px-3 py-2">Passed</th>
              <th className="px-3 py-2">Submitted at</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {students.map((s) => (
              <tr key={s.email} className="bg-gray-900/50">
                <td className="px-3 py-2 font-mono text-xs">{s.email}</td>
                <td className="px-3 py-2">{badge(s.status)}</td>
                <td className="px-3 py-2">{s.time_used_seconds != null ? `${s.time_used_seconds}s` : '—'}</td>
                <td className="px-3 py-2">{s.score ?? '—'}</td>
                <td className="px-3 py-2">{s.sandbox_passed === true ? 'yes' : s.sandbox_passed === false ? 'no' : '—'}</td>
                <td className="px-3 py-2 text-gray-400 text-xs">
                  {s.submitted_at ? new Date(s.submitted_at).toLocaleString() : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default InstructorAssignmentResultsPage;
