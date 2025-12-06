import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';

const ProtectedRoute: React.FC = () => {
  // Check if user data exists in session storage
  const user = sessionStorage.getItem('user');

  if (!user) {
    // If no user is logged in, redirect them to the login page
    return <Navigate to="/login" replace />;
  }

  // If a user is logged in, render the child component (e.g., MainLayout)
  return <Outlet />;
};

export default ProtectedRoute;