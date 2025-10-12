import React, { useState } from 'react';
import { Outlet, Link } from 'react-router-dom'; // CORRECTLY IMPORTING LINK
import Sidebar from './Sidebar';
import { FaBars } from 'react-icons/fa';

const MainLayout: React.FC = () => {
  const [isSidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    setSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="relative min-h-screen md:flex bg-gray-800">
      {/* Sidebar Component */}
      <Sidebar isOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Top bar for mobile with Hamburger Menu Button */}
        <div className="md:hidden p-4 bg-gray-900 text-white flex justify-between items-center shadow-lg">
          <Link to="/challenges" className="text-xl font-bold">SCALE ❤️</Link>
          <button onClick={toggleSidebar} className="text-2xl p-2">
            <FaBars />
          </button>
        </div>

        {/* Page Content */}
        <main className="p-4 sm:p-8">
          <Outlet /> {/* Renders the actual page component */}
        </main>
      </div>

      {/* Full-screen overlay for mobile to close the sidebar */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black opacity-50 z-30 md:hidden"
          onClick={toggleSidebar}
        ></div>
      )}
    </div>
  );
};

export default MainLayout;