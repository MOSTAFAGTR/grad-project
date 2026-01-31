import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';

interface ProtectedRouteProps {
  allowedRoles?: string[]; 
  children?: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ allowedRoles, children }) => {
  // --- FIX: READ FROM SESSION STORAGE ---
  const token = sessionStorage.getItem('token');
  const userRole = sessionStorage.getItem('role');

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && userRole) {
    if (!allowedRoles.includes(userRole)) {
      if (userRole === 'admin') return <Navigate to="/admin/stats" replace />;
      if (userRole === 'instructor') return <Navigate to="/instructor/dashboard" replace />;
      return <Navigate to="/home" replace />;
    }
  }

  return children ? <>{children}</> : <Outlet />;
};

export default ProtectedRoute;