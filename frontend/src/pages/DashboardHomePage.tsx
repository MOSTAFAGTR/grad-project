import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { FaShieldAlt, FaBug, FaTrophy, FaArrowRight, FaClipboardList } from 'react-icons/fa';

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

const DashboardHomePage: React.FC = () => {
  const [progress, setProgress] = useState(0);
  const [userEmail, setUserEmail] = useState('');
  const [progressCount, setProgressCount] = useState(0);
  const [quizAttempts, setQuizAttempts] = useState<QuizAttempt[]>([]);

  useEffect(() => {
    const email = sessionStorage.getItem('user_email') || sessionStorage.getItem('role') || 'Student';
    setUserEmail(email);
    const token = sessionStorage.getItem('token');
    if (token) {
      axios.get(`${API_URL}/api/challenges/progress`, { headers: { Authorization: `Bearer ${token}` } })
        .then((res) => {
          const items = res.data as ProgressItem[];
          setProgressCount(items.length);
          setProgress(Math.min(100, Math.round((items.length / 10) * 100)));
        })
        .catch(() => {});
      axios.get(`${API_URL}/api/quizzes/attempts`, { headers: { Authorization: `Bearer ${token}` } })
        .then((res) => setQuizAttempts(res.data as QuizAttempt[]))
        .catch(() => {});
    } else {
      setTimeout(() => setProgress(35), 500);
    }
  }, []);

  const latestQuiz = quizAttempts[0];
  const avgTimeSeconds = quizAttempts.length > 0
    ? Math.round(quizAttempts.reduce((s, a) => s + a.time_seconds, 0) / quizAttempts.length)
    : 0;
  const formatTime = (s: number) => (s >= 60 ? `${Math.floor(s / 60)}m ${s % 60}s` : `${s}s`);

  return (
    <div className="relative min-h-screen text-white bg-gray-900 p-8">
      {/* Content Container */}
      <div className="max-w-6xl mx-auto">

        {/* Welcome Header */}
        <div className="mb-12">
          <h1 className="text-5xl font-extrabold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
            Welcome back, {userEmail}
          </h1>
          <p className="text-xl text-gray-300">
            Your secure coding journey continues. You have <span className="text-yellow-400 font-bold">2 active challenges</span> waiting.
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-xl hover:border-blue-500 transition duration-300">
            <div className="flex items-center gap-4 mb-2">
              <div className="p-3 bg-blue-900/50 rounded-lg text-blue-400"><FaShieldAlt size={24} /></div>
              <h3 className="text-xl font-bold">Defense Level</h3>
            </div>
            <p className="text-3xl font-bold">{progressCount < 2 ? 'Novice' : progressCount < 5 ? 'Apprentice' : progressCount < 10 ? 'Expert' : 'Master'}</p>
            <p className="text-sm text-gray-400 mt-1">Keep fixing to rank up</p>
          </div>

          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-xl hover:border-purple-500 transition duration-300">
            <div className="flex items-center gap-4 mb-2">
              <div className="p-3 bg-purple-900/50 rounded-lg text-purple-400"><FaBug size={24} /></div>
              <h3 className="text-xl font-bold">Vulnerabilities</h3>
            </div>
            <p className="text-3xl font-bold">{progressCount}/20</p>
            <p className="text-sm text-gray-400 mt-1">Patched successfully</p>
          </div>

          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-xl hover:border-yellow-500 transition duration-300">
            <div className="flex items-center gap-4 mb-2">
              <div className="p-3 bg-yellow-900/50 rounded-lg text-yellow-400"><FaTrophy size={24} /></div>
              <h3 className="text-xl font-bold">Current Score</h3>
            </div>
            <p className="text-3xl font-bold">{progressCount * 100 + (quizAttempts.length ? Math.round(quizAttempts.reduce((s, a) => s + (a.score / a.total) * 100, 0) / quizAttempts.length) : 0)} XP</p>
            <p className="text-sm text-gray-400 mt-1">Challenges + quiz scores</p>
          </div>

          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-xl hover:border-teal-500 transition duration-300">
            <div className="flex items-center gap-4 mb-2">
              <div className="p-3 bg-teal-900/50 rounded-lg text-teal-400"><FaClipboardList size={24} /></div>
              <h3 className="text-xl font-bold">Quiz Results</h3>
            </div>
            <p className="text-3xl font-bold">
              {latestQuiz ? `${Math.round((latestQuiz.score / latestQuiz.total) * 100)}%` : '—'}
            </p>
            <p className="text-sm text-gray-400 mt-1">
              {quizAttempts.length > 0 ? `Latest quiz · Avg time: ${formatTime(avgTimeSeconds)}` : 'No quizzes yet'}
            </p>
          </div>
        </div>

        {/* Action Area */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

          {/* Quick Continue */}
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

          {/* Progress Overview */}
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
                  <span className="text-xs font-semibold inline-block text-blue-600">
                    {progress}%
                  </span>
                </div>
              </div>
              <div className="overflow-hidden h-4 mb-4 text-xs flex rounded bg-blue-200/20">
                <div style={{ width: `${progress}%` }} className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-blue-500 transition-all duration-1000 ease-out"></div>
              </div>
            </div>
            <p className="text-gray-400 text-sm mt-4">
              You are mastering the OWASP Top 10. Complete the XSS module to unlock "Broken Access Control".
            </p>
          </div>

          {/* Recent Quiz Attempts - same template as stat cards */}
          <div className="lg:col-span-2 bg-gray-800/50 p-8 rounded-xl border border-gray-700">
            <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
              <FaClipboardList className="text-teal-400" />
              Recent Quiz Attempts
            </h2>
            {quizAttempts.length === 0 ? (
              <p className="text-gray-500">No quiz attempts yet. <Link to="/quiz" className="text-teal-400 hover:underline">Take a quiz</Link> to get started.</p>
            ) : (
              <div className="space-y-3">
                {quizAttempts.slice(0, 5).map((a) => (
                  <div key={a.id} className="bg-gray-800 p-4 rounded-lg border border-gray-700 flex justify-between items-center">
                    <span className="font-medium truncate flex-1 mr-4">{a.title}</span>
                    <span className="text-teal-400 font-bold shrink-0">{Math.round((a.score / a.total) * 100)}%</span>
                    <span className="text-gray-500 text-sm shrink-0 ml-2">{formatTime(a.time_seconds)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
};

export default DashboardHomePage;