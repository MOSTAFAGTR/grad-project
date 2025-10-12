import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { FaHome, FaQuestionCircle, FaShieldAlt, FaChalkboardTeacher, FaTimes } from 'react-icons/fa';

interface SidebarProps {
  isOpen: boolean;
  toggleSidebar: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, toggleSidebar }) => {
  const linkStyle = "flex items-center p-3 my-2 rounded-lg text-gray-300 hover:bg-gray-700 transition-colors";
  const activeLinkStyle = {
    backgroundColor: '#4338ca', // A darker indigo
    color: 'white'
  };

  return (
    <aside className={`fixed top-0 left-0 z-40 w-64 h-screen bg-gray-900 text-white flex flex-col p-4 transform ${isOpen ? 'translate-x-0' : '-translate-x-full'} transition-transform duration-300 ease-in-out md:relative md:translate-x-0`}>
      <div className="flex justify-between items-center mb-10">
        <Link to="/challenges" className="text-2xl font-bold flex items-center">
          SCALE <span className="text-red-500 ml-2">❤️</span>
        </Link>
        <button onClick={toggleSidebar} className="md:hidden text-2xl text-gray-300 hover:text-white">
          <FaTimes />
        </button>
      </div>
      <nav>
        {/*
          THE FIX:
          The 'to' prop now points to a unique path for each link.
          The 'end' prop on '/challenges' ensures it's ONLY active on that exact page.
        */}
        <NavLink to="/home" end style={({ isActive }) => isActive ? activeLinkStyle : undefined} className={linkStyle}>
          <FaHome className="mr-3" /> Home
        </NavLink>
        
        <NavLink to="/questions" style={({ isActive }) => isActive ? activeLinkStyle : undefined} className={linkStyle}>
          <FaQuestionCircle className="mr-3" /> Questions
        </NavLink>

        <NavLink to="/challenges" style={({ isActive }) => isActive ? activeLinkStyle : undefined} className={linkStyle}>
          <FaShieldAlt className="mr-3" /> Challenges
        </NavLink>
        
        <NavLink to="/instructor" style={({ isActive }) => isActive ? activeLinkStyle : undefined} className={linkStyle}>
          <FaChalkboardTeacher className="mr-3" /> Instructor
        </NavLink>
      </nav>
    </aside>
  );
};

export default Sidebar;