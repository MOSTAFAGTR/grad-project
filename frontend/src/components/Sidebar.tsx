import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { FaHome, FaShieldAlt, FaQuestionCircle, FaSignOutAlt, FaBars, FaTimes } from 'react-icons/fa';

interface SidebarProps {
  collapsed: boolean;
  setCollapsed: (val: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ collapsed, setCollapsed }) => {
  const navigate = useNavigate();
  const toggleSidebar = () => setCollapsed(!collapsed);

  const handleLogout = () => {
    sessionStorage.removeItem('user');
    navigate('/login');
  };

  const linkStyle = "flex items-center gap-3 p-3 my-1 rounded-lg text-gray-400 hover:bg-gray-700 hover:text-white transition-all";
  const activeLinkStyle = { backgroundColor: '#374151', color: 'white' };

  return (
    <div className={`fixed top-0 left-0 h-screen bg-gray-900 text-white flex flex-col justify-between p-5 border-r border-gray-800 transition-all duration-500 z-40 ${collapsed ? 'w-20' : 'w-64'}`}>
      <div>
        <div className="flex justify-between items-center mb-10">
          {!collapsed && <h1 className="text-2xl font-extrabold">SCALE</h1>}
          <button onClick={toggleSidebar} className="text-xl text-gray-400 hover:text-white">
            {collapsed ? <FaBars /> : <FaTimes />}
          </button>
        </div>
        <nav className="space-y-2">
          <NavLink to="/home" end style={({ isActive }) => (isActive ? activeLinkStyle : undefined)} className={linkStyle}>
            <FaHome className="text-lg" />
            {!collapsed && <span className="font-medium">Home</span>}
          </NavLink>
          <NavLink to="/challenges" style={({ isActive }) => (isActive ? activeLinkStyle : undefined)} className={linkStyle}>
            <FaShieldAlt className="text-lg" />
            {!collapsed && <span className="font-medium">Challenges</span>}
          </NavLink>
          <NavLink to="quiz" style={({ isActive }) => (isActive ? activeLinkStyle : undefined)} className={linkStyle}>
            <FaQuestionCircle className="text-lg" />
            {!collapsed && <span className="font-medium">Questions</span>}
          </NavLink>
          <NavLink to="instructor/quiz" style={({ isActive }) => (isActive ? activeLinkStyle : undefined)} className={linkStyle}>
            <FaQuestionCircle className="text-lg" />
            {!collapsed && <span className="font-medium">Questionsadmin</span>}
          </NavLink>
        </nav>
      </div>
      <div>
        
        <button onClick={handleLogout} className={linkStyle + " w-full"}>
          <FaSignOutAlt className="text-lg" />
          {!collapsed && <span className="font-medium">Logout</span>}
         
        </button>
         {!collapsed && <div className="text-gray-500 text-sm mb-2 text-center">© 2025 SCALE</div>}
      </div>
    </div>
  );
};

export default Sidebar;