import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { FaServer, FaUsers, FaNetworkWired, FaSync } from 'react-icons/fa';

const AdminStatsPage: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

  const fetchStats = async () => {
    setLoading(true);
    try {
      // --- FIX: USE SESSION STORAGE ---
      const token = sessionStorage.getItem('token');
      const res = await axios.get('http://localhost:8000/api/stats/admin/dashboard', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(res.data);
    } catch (err) {
      console.error("Failed to fetch admin stats", err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) return <div className="p-10 text-white">Loading live statistics...</div>;
  if (!stats) return <div className="p-10 text-red-400">Failed to load statistics. Backend might be down.</div>;

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-white">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Platform Overview</h1>
          <p className="text-gray-400">Real-time system performance and usage statistics.</p>
        </div>
        <button onClick={fetchStats} className="bg-gray-800 p-2 rounded hover:bg-gray-700 transition" title="Refresh Data">
          <FaSync className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* System Load */}
        <div className="bg-gray-800 p-6 rounded-lg border border-blue-500/50">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400">System Status</p>
              <h2 className="text-2xl font-bold mt-2 text-green-400">{stats.system_status}</h2>
            </div>
            <FaServer className="text-3xl text-blue-500" />
          </div>
        </div>

        {/* Total Users */}
        <div className="bg-gray-800 p-6 rounded-lg border border-purple-500/50">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400">Total Registered Users</p>
              <h2 className="text-3xl font-bold mt-2">{stats.total_users}</h2>
            </div>
            <FaUsers className="text-3xl text-purple-500" />
          </div>
        </div>

        {/* Fixed Vulns */}
        <div className="bg-gray-800 p-6 rounded-lg border border-green-500/50">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400">Verified Fixes</p>
              <h2 className="text-3xl font-bold mt-2">{stats.fixed_vulns}</h2>
            </div>
            <FaNetworkWired className="text-3xl text-green-500" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Challenge Usage Chart */}
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h3 className="text-xl font-bold mb-6">Challenge Success Rate</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.challenge_usage}>
                <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                <XAxis dataKey="name" stroke="#ccc" />
                <YAxis stroke="#ccc" />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', color: '#fff' }} />
                <Legend />
                <Bar dataKey="attempts" fill="#8884d8" name="Total Attempts" />
                <Bar dataKey="successes" fill="#82ca9d" name="Successful Fixes" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* User Distribution Chart */}
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h3 className="text-xl font-bold mb-6">User Roles</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stats.user_distribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  fill="#8884d8"
                  paddingAngle={5}
                  dataKey="value"
                  label
                >
                  {stats.user_distribution.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminStatsPage;