import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
  FaUsers, FaBug, FaCheckCircle, FaServer, FaBell,
  FaTimes, FaUserPlus, FaCheck, FaTrash, FaEdit
} from 'react-icons/fa';

const AdminDashboardPage: React.FC = () => {
  // Data State
  const [users, setUsers] = useState<any[]>([]);
  const [pendingUsers, setPendingUsers] = useState<any[]>([]);

  // UI State
  const [showRequests, setShowRequests] = useState(false);
  const [showAddAdmin, setShowAddAdmin] = useState(false);
  const [editingUser, setEditingUser] = useState<any | null>(null);

  // Form State
  const [newAdminEmail, setNewAdminEmail] = useState('');
  const [newAdminPass, setNewAdminPass] = useState('');
  const [editRole, setEditRole] = useState('user');

  const token = sessionStorage.getItem('token');
  const headers = { headers: { Authorization: `Bearer ${token}` } };
  const API_URL = 'http://localhost:8000/api';

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const uRes = await axios.get(`${API_URL}/auth/users`, headers);
      setUsers(uRes.data);
      const pRes = await axios.get(`${API_URL}/auth/admin/pending`, headers);
      setPendingUsers(pRes.data);
    } catch (err) {
      console.error("Failed to fetch data", err);
    }
  };

  // --- ACTIONS ---

  const handleApprove = async (userId: number) => {
    try {
      await axios.post(`${API_URL}/auth/admin/approve/${userId}`, {}, headers);
      alert('User Approved!');
      fetchData();
    } catch (err) { alert('Approval failed'); }
  };

  const handleCreateAdmin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/auth/admin/create-admin`, {
        email: newAdminEmail,
        password: newAdminPass
      }, headers);
      alert('Admin Created!');
      setShowAddAdmin(false);
      setNewAdminEmail('');
      setNewAdminPass('');
      fetchData();
    } catch (err: any) { alert(err.response?.data?.detail || 'Error'); }
  };

  const handleBan = async (userId: number) => {
    if (!confirm("Are you sure you want to BAN (Delete) this user? This cannot be undone.")) return;
    try {
      await axios.delete(`${API_URL}/auth/admin/users/${userId}`, headers);
      fetchData();
    } catch (err) { alert('Failed to ban user'); }
  };

  const openEditModal = (user: any) => {
    setEditingUser(user);
    setEditRole(user.role);
  };

  const handleEditSave = async () => {
    if (!editingUser) return;
    try {
      await axios.put(`${API_URL}/auth/admin/users/${editingUser.id}/role`, { role: editRole }, headers);
      setEditingUser(null);
      fetchData();
    } catch (err) { alert('Failed to update role'); }
  };

  return (
    <div className="text-white space-y-6 relative min-h-screen">

      {/* HEADER */}
      <div className="flex justify-between items-center border-b border-gray-700 pb-4">
        <h1 className="text-3xl font-bold">System Administration</h1>
        <div className="flex gap-3">
          {/* Add Admin Button */}
          <button
            onClick={() => setShowAddAdmin(true)}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded flex items-center gap-2 font-bold"
          >
            <FaUserPlus /> Add Admin
          </button>

          {/* Requests Button */}
          <button
            onClick={() => setShowRequests(true)}
            className="relative bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded flex items-center gap-2 font-bold"
          >
            <FaBell /> Requests
            {pendingUsers.length > 0 && (
              <span className="bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center border border-gray-900 absolute -top-2 -right-2">
                {pendingUsers.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* STATS CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-gray-800 p-6 rounded-lg border border-blue-500 shadow-lg shadow-blue-900/20">
          <div className="flex items-center justify-between">
            <h3 className="text-gray-400">Total Users</h3>
            <FaUsers className="text-blue-400 text-2xl" />
          </div>
          <p className="text-3xl font-bold mt-2">{users.length}</p>
        </div>
        <div className="bg-gray-800 p-6 rounded-lg border border-red-500 shadow-lg shadow-red-900/20">
          <div className="flex items-center justify-between">
            <h3 className="text-gray-400">Active Exploits</h3>
            <FaBug className="text-red-400 text-2xl" />
          </div>
          <p className="text-3xl font-bold mt-2">12</p>
        </div>
        <div className="bg-gray-800 p-6 rounded-lg border border-green-500 shadow-lg shadow-green-900/20">
          <div className="flex items-center justify-between">
            <h3 className="text-gray-400">Fixed Vulnerabilities</h3>
            <FaCheckCircle className="text-green-400 text-2xl" />
          </div>
          <p className="text-3xl font-bold mt-2">89</p>
        </div>
        <div className="bg-gray-800 p-6 rounded-lg border border-purple-500 shadow-lg shadow-purple-900/20">
          <div className="flex items-center justify-between">
            <h3 className="text-gray-400">Sandbox Status</h3>
            <FaServer className="text-purple-400 text-2xl" />
          </div>
          <p className="text-lg font-bold mt-2 text-green-400">Operational</p>
        </div>
      </div>

      {/* USER MANAGEMENT TABLE */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-bold mb-4">User Management</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-400">
            <thead className="bg-gray-700 text-gray-200 uppercase">
              <tr>
                <th className="px-6 py-3">ID</th>
                <th className="px-6 py-3">Email</th>
                <th className="px-6 py-3">Role</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-gray-700 hover:bg-gray-750 transition">
                  <td className="px-6 py-4">{u.id}</td>
                  <td className="px-6 py-4 font-medium text-white">{u.email}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded text-xs font-bold uppercase ${u.role === 'admin' ? 'bg-red-900 text-red-200' :
                      u.role === 'instructor' ? 'bg-purple-900 text-purple-200' :
                        'bg-blue-900 text-blue-200'
                      }`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {u.is_approved ? <span className="text-green-400">Active</span> : <span className="text-yellow-400">Pending</span>}
                  </td>
                  <td className="px-6 py-4 flex gap-3">
                    <button onClick={() => openEditModal(u)} className="text-blue-400 hover:text-white transition" title="Edit Role">
                      <FaEdit />
                    </button>
                    <button onClick={() => handleBan(u.id)} className="text-red-400 hover:text-white transition" title="Ban User">
                      <FaTrash />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* --- MODAL: ADD ADMIN --- */}
      {showAddAdmin && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-gray-800 p-8 rounded-lg border border-blue-500 w-96 shadow-2xl">
            <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
              <FaUserPlus className="text-blue-400" /> Create Admin
            </h2>
            <form onSubmit={handleCreateAdmin} className="space-y-4">
              <input type="email" placeholder="Email" required className="w-full bg-gray-700 p-2 rounded text-white outline-none" value={newAdminEmail} onChange={e => setNewAdminEmail(e.target.value)} />
              <input type="password" placeholder="Password" required className="w-full bg-gray-700 p-2 rounded text-white outline-none" value={newAdminPass} onChange={e => setNewAdminPass(e.target.value)} />
              <div className="flex justify-end gap-2 mt-4">
                <button type="button" onClick={() => setShowAddAdmin(false)} className="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- MODAL: EDIT USER --- */}
      {editingUser && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-gray-800 p-8 rounded-lg border border-gray-600 w-96 shadow-2xl">
            <h2 className="text-xl font-bold mb-4">Edit User: {editingUser.email}</h2>
            <label className="block mb-2 text-sm text-gray-400">Change Role:</label>
            <select value={editRole} onChange={e => setEditRole(e.target.value)} className="w-full bg-gray-700 p-2 rounded text-white mb-6">
              <option value="user">Student</option>
              <option value="instructor">Instructor</option>
              <option value="admin">Admin</option>
            </select>
            <div className="flex justify-end gap-2">
              <button onClick={() => setEditingUser(null)} className="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600">Cancel</button>
              <button onClick={handleEditSave} className="px-4 py-2 bg-green-600 rounded hover:bg-green-700">Save</button>
            </div>
          </div>
        </div>
      )}

      {/* --- DRAWER: PENDING REQUESTS --- */}
      {showRequests && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setShowRequests(false)}></div>
          <div className="relative w-full md:w-1/3 bg-gray-900 h-screen shadow-2xl border-l border-gray-700 flex flex-col slide-in-right">
            <div className="p-6 border-b border-gray-800 bg-gray-800/50 flex justify-between items-center">
              <h2 className="text-xl font-bold text-white flex items-center gap-2"><FaBell className="text-purple-500" /> Requests</h2>
              <button onClick={() => setShowRequests(false)} className="text-gray-400 hover:text-white"><FaTimes size={20} /></button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {pendingUsers.length === 0 ? (
                <div className="text-center text-gray-500 mt-20 opacity-50"><FaCheckCircle className="text-5xl mx-auto mb-4" /><p>No pending requests.</p></div>
              ) : (
                pendingUsers.map(u => (
                  <div key={u.id} className="bg-gray-800 p-4 rounded border border-gray-700 shadow-md flex justify-between items-center">
                    <div>
                      <p className="font-bold text-white">{u.email}</p>
                      <span className="text-xs bg-purple-900 text-purple-200 px-2 py-0.5 rounded">Instructor</span>
                    </div>
                    <button onClick={() => handleApprove(u.id)} className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded font-bold flex gap-2 items-center"><FaCheck /> Approve</button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboardPage;