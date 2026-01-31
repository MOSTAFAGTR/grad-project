import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { 
  FaHome, FaShieldAlt, FaQuestionCircle, FaSignOutAlt, 
  FaBars, FaTimes, FaChalkboardTeacher, FaUserCog, FaLock 
} from 'react-icons/fa';

interface SidebarProps {
  collapsed: boolean;
  setCollapsed: (val: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ collapsed, setCollapsed }) => {
  const navigate = useNavigate();
  const toggleSidebar = () => setCollapsed(!collapsed);

  // --- FIX: READ FROM SESSION STORAGE ---
  const role = sessionStorage.getItem('role') || 'user'; 

  const handleLogout = () => {
    sessionStorage.clear(); // Clears only this tab
    navigate('/login');
  };

  const getHomeLink = () => {
    if (role === 'admin') return '/admin/stats';
    if (role === 'instructor') return '/instructor/dashboard';
    return '/home';
  };

  const linkStyle = "flex items-center gap-3 p-3 my-1 rounded-lg text-gray-400 hover:bg-gray-700 hover:text-white transition-all";
  const activeLinkStyle = { backgroundColor: '#374151', color: '#60A5FA', borderLeft: '4px solid #3B82F6' };

  return (
    <div className={`fixed top-0 left-0 h-screen bg-gray-900 text-white flex flex-col justify-between p-4 border-r border-gray-800 transition-all duration-300 z-50 ${collapsed ? 'w-20' : 'w-64'}`}>
      
      <div>
        <div className="flex justify-between items-center mb-8">
          {!collapsed && (
            <div className="flex flex-col">
                <h1 className="text-2xl font-extrabold tracking-wider">SCALE</h1>
                <span className="text-xs text-gray-500 uppercase tracking-widest">{role} Portal</span>
            </div>
          )}
          <button onClick={toggleSidebar} className="text-xl text-gray-400 hover:text-white p-2">
            {collapsed ? <FaBars /> : <FaTimes />}
          </button>
        </div>

        <nav className="space-y-2">
          
          <NavLink to={getHomeLink()} end style={({ isActive }) => (isActive ? activeLinkStyle : undefined)} className={linkStyle}>
            <FaHome className="text-lg" />
            {!collapsed && <span className="font-medium">Dashboard</span>}
          </NavLink>

          {/* STUDENT LINKS */}
          {role === 'user' && (
            <>
              <NavLink to="/challenges" style={({ isActive }) => (isActive ? activeLinkStyle : undefined)} className={linkStyle}>
                <FaShieldAlt className="text-lg" />
                {!collapsed && <span className="font-medium">Labs & Attacks</span>}
              </NavLink>
              <NavLink to="/quiz" style={({ isActive }) => (isActive ? activeLinkStyle : undefined)} className={linkStyle}>
                <FaQuestionCircle className="text-lg" />
                {!collapsed && <span className="font-medium">My Quizzes</span>}
              </NavLink>
            </>
          )}

          {/* INSTRUCTOR LINKS */}
          {(role === 'instructor' || role === 'admin') && (
            <>
              <div className="my-4 border-t border-gray-700"></div>
              {!collapsed && <p className="text-xs text-gray-500 font-bold mb-2 uppercase">Instructor Zone</p>}
              
              <NavLink to="/instructor/quiz" style={({ isActive }) => (isActive ? activeLinkStyle : undefined)} className={linkStyle}>
                <FaChalkboardTeacher className="text-lg" />
                {!collapsed && <span className="font-medium">Quiz Manager</span>}
              </NavLink>
            </>
          )}

          {/* ADMIN LINKS */}
          {role === 'admin' && (
            <>
              <div className="my-4 border-t border-gray-700"></div>
              {!collapsed && <p className="text-xs text-gray-500 font-bold mb-2 uppercase">System Admin</p>}

              <NavLink to="/admin/dashboard" style={({ isActive }) => (isActive ? activeLinkStyle : undefined)} className={linkStyle}>
                <FaUserCog className="text-lg" />
                {!collapsed && <span className="font-medium">Admin Panel</span>}
              </NavLink>
              <NavLink to="/admin/logs" style={({ isActive }) => (isActive ? activeLinkStyle : undefined)} className={linkStyle}>
                <FaLock className="text-lg" />
                {!collapsed && <span className="font-medium">Security Logs</span>}
              </NavLink>
            </>
          )}

        </nav>
      </div>

      <div>
        <button onClick={handleLogout} className={`${linkStyle} w-full text-red-400 hover:bg-red-900/30 hover:text-red-300`}>
          <FaSignOutAlt className="text-lg" />
          {!collapsed && <span className="font-medium">Sign Out</span>}
        </button>
        {!collapsed && <div className="text-gray-600 text-xs mt-4 text-center">v1.0.0-Beta</div>}
      </div>
    </div>
  );
};

export default Sidebar;