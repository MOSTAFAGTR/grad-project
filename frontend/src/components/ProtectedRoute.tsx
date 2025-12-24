import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';

interface ProtectedRouteProps {
  children?: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  // 1. Get the token from storage
  const token = localStorage.getItem('token');

  // 2. If no token, kick user back to Login
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // 3. If token exists, allow access
  // If children are provided (wrapping), render them. Otherwise use Outlet (nested routes).
  return children ? <>{children}</> : <Outlet />;
};

export default ProtectedRoute;