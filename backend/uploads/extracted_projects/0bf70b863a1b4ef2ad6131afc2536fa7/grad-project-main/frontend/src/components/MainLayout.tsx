import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-gray-800 flex">
      {/* The Sidebar is a permanent fixture in the layout */}
      <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />

      {/* The Main Content area that will adjust its margin */}
      <div
        className="flex-1 transition-all duration-500 ease-in-out p-6 sm:p-8"
        // This style dynamically changes the margin based on the sidebar's state
        style={{ marginLeft: collapsed ? '5rem' : '16rem' }} 
      >
        <Outlet />
      </div>
    </div>
  );
};

export default MainLayout;