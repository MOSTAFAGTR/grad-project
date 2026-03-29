import React from 'react';
import { useEffect, useMemo, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { api } from '../lib/api';

interface ProtectedRouteProps {
  allowedRoles?: string[]; 
  children?: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ allowedRoles, children }) => {
  const [isVerifying, setIsVerifying] = useState(true);
  const [verifiedRole, setVerifiedRole] = useState<string | null>(sessionStorage.getItem('role'));

  const allowedRoleSet = useMemo(() => new Set(allowedRoles || []), [allowedRoles]);

  useEffect(() => {
    let mounted = true;
    const verifySession = async () => {
      try {
        const res = await api.get('/api/auth/me');
        const serverRole = res.data?.role ?? 'user';
        if (mounted) {
          setVerifiedRole(serverRole);
          setIsVerifying(false);
        }
        sessionStorage.setItem('token', 'cookie-auth');
        sessionStorage.setItem('role', serverRole);
      } catch {
        sessionStorage.clear();
        if (mounted) {
          setVerifiedRole(null);
          setIsVerifying(false);
        }
      }
    };
    verifySession();
    return () => {
      mounted = false;
    };
  }, []);

  if (isVerifying) {
    return <div className="p-6 text-white">Verifying session...</div>;
  }
  if (!verifiedRole) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles) {
    if (!allowedRoleSet.has(verifiedRole)) {
      if (verifiedRole === 'admin') return <Navigate to="/admin/stats" replace />;
      if (verifiedRole === 'instructor') return <Navigate to="/instructor/dashboard" replace />;
      return <Navigate to="/home" replace />;
    }
  }

  return children ? <>{children}</> : <Outlet />;
};

export default ProtectedRoute;