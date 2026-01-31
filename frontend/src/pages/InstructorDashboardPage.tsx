import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import { FaUserGraduate, FaChalkboardTeacher, FaClipboardCheck, FaSearch, FaTimes, FaChartPie } from 'react-icons/fa';

const InstructorDashboardPage: React.FC = () => {
  const [users, setUsers] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [stats, setStats] = useState<any>(null); // State for Real Stats

  const [selectedStudent, setSelectedStudent] = useState<any | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = sessionStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      // 1. Fetch Students List
      const resUsers = await axios.get('http://localhost:8000/api/auth/users', { headers });
      setUsers(resUsers.data.filter((u: any) => u.role === 'user'));

      // 2. Fetch Instructor Stats (Real Data)
      const resStats = await axios.get('http://localhost:8000/api/stats/instructor/dashboard', { headers });
      setStats(resStats.data);

    } catch (err) { console.error(err); }
  };

  const filteredStudents = users.filter(u => u.email.toLowerCase().includes(searchTerm.toLowerCase()));
  const handleViewAnalytics = (student: any) => setSelectedStudent(student);

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
                <th className="px-6 py-3">Action</th>
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
                        onClick={() => handleViewAnalytics(student)}
                        className="text-blue-400 hover:text-white hover:underline text-sm font-bold"
                      >
                        View Analytics
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
              <button onClick={() => setSelectedStudent(null)} className="text-gray-400 hover:text-white hover:bg-gray-700 p-2 rounded-full transition">
                <FaTimes size={24} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-8 overflow-y-auto grid grid-cols-1 md:grid-cols-2 gap-8">

              {/* Left Column: Stats */}
              <div className="space-y-6">
                <div className="bg-gray-700/50 p-4 rounded-lg border border-gray-600">
                  <h3 className="text-gray-300 font-bold mb-2">Performance Summary</h3>
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div className="p-3 bg-gray-800 rounded">
                      <p className="text-xs text-gray-400">Class Rank</p>
                      <p className="text-2xl font-bold text-yellow-400">Top 10%</p>
                    </div>
                    <div className="p-3 bg-gray-800 rounded">
                      <p className="text-xs text-gray-400">Avg Completion</p>
                      <p className="text-2xl font-bold text-green-400">{stats.avg_completion_rate}%</p>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-700/50 p-4 rounded-lg border border-gray-600">
                  <h3 className="text-gray-300 font-bold mb-3 flex items-center gap-2">
                    <FaChartPie /> Skill Breakdown (Estimate)
                  </h3>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart cx="50%" cy="50%" outerRadius="80%" data={[
                        { subject: 'SQLi', A: 120, fullMark: 150 },
                        { subject: 'XSS', A: 98, fullMark: 150 },
                        { subject: 'Auth', A: 86, fullMark: 150 },
                        { subject: 'Config', A: 99, fullMark: 150 },
                      ]}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="subject" stroke="#ccc" />
                        <PolarRadiusAxis />
                        <Radar name="Student" dataKey="A" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              {/* Right Column: Info */}
              <div className="space-y-4">
                <div className="bg-blue-900/20 p-4 rounded border border-blue-800">
                  <h4 className="text-blue-400 font-bold mb-2">Status</h4>
                  <p className="text-sm">This student has been active recently. Their progress aligns with the class average.</p>
                </div>

                <div className="mt-6 pt-6 border-t border-gray-700">
                  <h4 className="text-sm font-bold text-gray-400 mb-2">Instructor Actions</h4>
                  <div className="flex gap-2">
                    <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-bold">Message Student</button>
                    <button className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm font-bold">Reset Password</button>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default InstructorDashboardPage;