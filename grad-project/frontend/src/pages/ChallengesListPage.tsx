import * as React from 'react';
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FaSyringe,
  FaBug,
  FaUserSecret,
  FaTerminal,
  FaUserShield,
  FaTools,
  FaLock,
  FaFolderOpen,
  FaFileCode,
  FaExternalLinkAlt,
} from 'react-icons/fa';
import { api } from '../lib/api';

const colorMap: Record<string, string> = {
  cyan: '#06b6d4',
  pink: '#d946ef',
  orange: '#fb923c',
  purple: '#8b5cf6',
  red: '#ef4444',
  green: '#10b981',
  yellow: '#facc15',
  blue: '#3b82f6',
  indigo: '#6366f1',
  teal: '#14b8a6',
};

const successTypeMap: Record<number, string> = {
  1: 'sql-injection',
  2: 'xss',
  3: 'csrf',
  4: 'command-injection',
  5: 'broken-auth',
  6: 'security-misc',
  7: 'insecure-storage',
  8: 'directory-traversal',
  9: 'xxe',
  10: 'redirect',
};

const challenges = [
  {
    id: 1,
    title: 'SQL Scenario',
    icon: <FaSyringe />,
    color: 'cyan',
    buttons: [
      { text: 'Simulate', url: '/challenges/1/attack' },
      { text: 'Fix', url: '/challenges/1/fix' },
      { text: 'Tutorial', url: '/challenges/1/tutorial' },
    ],
  },
  {
    id: 2,
    title: 'XSS Scenario',
    icon: <FaBug />,
    color: 'pink',
    buttons: [
      { text: 'Simulate', url: '/challenges/2/attack' },
      { text: 'Fix', url: '/challenges/2/fix' },
      { text: 'Tutorial', url: '/challenges/2/tutorial' },
    ],
  },
  {
    id: 3,
    title: 'CSRF Scenario',
    icon: <FaUserSecret />,
    color: 'orange',
    buttons: [
      { text: 'Simulate', url: '/challenges/3/attack' },
      { text: 'Fix', url: '/challenges/3/fix' },
      { text: 'Tutorial', url: '/challenges/3/tutorial' },
    ],
  },
  {
    id: 4,
    title: 'Command Injection',
    icon: <FaTerminal />,
    color: 'purple',
    buttons: [
      { text: 'Simulate', url: '/challenges/4/attack' },
      { text: 'Fix', url: '/challenges/4/fix' },
      { text: 'Tutorial', url: '/challenges/4/tutorial' },
    ],
  },
  {
    id: 5,
    title: 'Broken Authentication',
    icon: <FaUserShield />,
    color: 'red',
    buttons: [
      { text: 'Simulate', url: '/challenges/5/attack' },
      { text: 'Fix', url: '/challenges/5/fix' },
      { text: 'Tutorial', url: '/challenges/5/tutorial' },
    ],
  },
  {
    id: 6,
    title: 'Security Misconfiguration',
    icon: <FaTools />,
    color: 'green',
    buttons: [
      { text: 'Simulate', url: '/challenges/6/attack' },
      { text: 'Fix', url: '/challenges/6/fix' },
      { text: 'Tutorial', url: '/challenges/6/tutorial' },
    ],
  },
  {
    id: 7,
    title: 'Insecure Storage',
    icon: <FaLock />,
    color: 'yellow',
    buttons: [
      { text: 'Simulate', url: '/challenges/7/attack' },
      { text: 'Fix', url: '/challenges/7/fix' },
      { text: 'Tutorial', url: '/challenges/7/tutorial' },
    ],
  },
  {
    id: 8,
    title: 'Directory Traversal',
    icon: <FaFolderOpen />,
    color: 'blue',
    buttons: [
      { text: 'Simulate', url: '/challenges/8/attack' },
      { text: 'Fix', url: '/challenges/8/fix' },
      { text: 'Tutorial', url: '/challenges/8/tutorial' },
    ],
  },
  {
    id: 9,
    title: 'XML External Entity (XXE)',
    icon: <FaFileCode />,
    color: 'indigo',
    buttons: [
      { text: 'Simulate', url: '/challenges/9/attack' },
      { text: 'Fix', url: '/challenges/9/fix' },
      { text: 'Tutorial', url: '/challenges/9/tutorial' },
    ],
  },
  {
    id: 10,
    title: 'Unvalidated Redirect',
    icon: <FaExternalLinkAlt />,
    color: 'teal',
    buttons: [
      { text: 'Simulate', url: '/challenges/10/attack' },
      { text: 'Fix', url: '/challenges/10/fix' },
      { text: 'Tutorial', url: '/challenges/10/tutorial' },
    ],
  },
];

const idToChallengeId: Record<number, string> = {
  1: 'sql-injection',
  2: 'xss',
  3: 'csrf',
  4: 'command-injection',
  5: 'broken-auth',
  6: 'security-misc',
  7: 'insecure-storage',
  8: 'directory-traversal',
  9: 'xxe',
  10: 'redirect',
};

interface ProgressItem {
  challenge_id: string;
  completed_at: string;
}

const ChallengesListPage: React.FC = () => {
  const [completedIds, setCompletedIds] = useState<Set<string>>(new Set());
  const [deletingChallenge, setDeletingChallenge] = useState<string | null>(null);
  const [deleteSuccess, setDeleteSuccess] = useState<string | null>(null);

  useEffect(() => {
    const token = sessionStorage.getItem('token');
    if (!token) return;
    api
      .get<ProgressItem[]>('/api/challenges/progress')
      .then((res) => setCompletedIds(new Set(res.data.map((p) => p.challenge_id))))
      .catch(() => {});
  }, []);

  const handleReset = async (slug: string, title: string) => {
    if (
      !window.confirm(
        `Are you sure you want to reset your progress for ${title}? This will remove your completion record and reset your attempt history.`,
      )
    ) {
      return;
    }
    setDeletingChallenge(slug);
    try {
      await api.delete(`/api/challenges/progress/${encodeURIComponent(slug)}`);
      setCompletedIds((prev) => {
        const next = new Set(prev);
        next.delete(slug);
        return next;
      });
      setDeleteSuccess(slug);
      window.setTimeout(() => setDeleteSuccess(null), 4000);
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { detail?: string } } };
      alert(ax.response?.data?.detail || 'Failed to reset progress');
    } finally {
      setDeletingChallenge(null);
    }
  };

  return (
    <>
      {deleteSuccess && (
        <p className="text-emerald-400 text-sm mb-4">
          Progress reset for {challenges.find((c) => idToChallengeId[c.id] === deleteSuccess)?.title || deleteSuccess}.
        </p>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-8">
        {challenges.map((ch) => {
          const slug = idToChallengeId[ch.id];
          const done = slug && completedIds.has(slug);
          return (
            <div
              key={ch.id}
              className="card-container bg-gray-900 rounded-2xl p-6 flex flex-col border-2 transition-all duration-300"
              style={
                {
                  borderColor: colorMap[ch.color],
                  '--shadow-color': colorMap[ch.color],
                } as React.CSSProperties
              }
            >
              <div className="flex-grow">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-white text-2xl font-bold">{ch.title}</h3>
                  <div className="text-5xl icon-container" style={{ color: colorMap[ch.color] }}>
                    {ch.icon}
                  </div>
                </div>
              </div>
              <div className="flex flex-wrap gap-3 mt-8 items-center">
                {ch.buttons.map((btn) => (
                  <Link
                    key={btn.text}
                    to={btn.url}
                    className="bg-gray-700 text-gray-300 text-sm font-semibold py-2 px-5 rounded-full hover:bg-gray-600 hover:text-white transition-colors"
                  >
                    {btn.text}
                  </Link>
                ))}
                {successTypeMap[ch.id] && done && (
                  <>
                    <Link
                      to={`/challenges/attack-success?type=${successTypeMap[ch.id]}`}
                      className="bg-green-900/50 text-green-400 text-sm font-semibold py-2 px-5 rounded-full hover:bg-green-800/50 hover:text-green-300 transition-colors border border-green-600/50"
                    >
                      Success
                    </Link>
                    <button
                      type="button"
                      disabled={deletingChallenge === slug}
                      onClick={() => handleReset(slug, ch.title)}
                      className="text-xs font-semibold py-1 px-2.5 rounded border border-red-500 text-red-400 hover:bg-red-950/40 disabled:opacity-50"
                    >
                      {deletingChallenge === slug ? '…' : 'Reset'}
                    </button>
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>
      <style>
        {`
          .card-container:hover {
            transform: translateY(-5px) scale(1.02);
            box-shadow: 0 10px 20px -5px var(--shadow-color);
          }
          .icon-container {
            transition: transform 0.3s ease-in-out;
          }
          .card-container:hover .icon-container {
            transform: scale(1.2) rotate(5deg);
          }
        `}
      </style>
    </>
  );
};

export default ChallengesListPage;
