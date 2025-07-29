import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { authService } from '../services/authService';

// Logging utility for ProtectedRoute
const logProtectedRouteEvent = (level: 'info' | 'warn' | 'error', message: string, data?: any) => {
  const timestamp = new Date().toISOString();
  const logMessage = `[ProtectedRoute] ${timestamp} - ${level.toUpperCase()}: ${message}`;
  
  switch (level) {
    case 'error':
      console.error(logMessage, data || '');
      break;
    case 'warn':
      console.warn(logMessage, data || '');
      break;
    default:
      console.log(logMessage, data || '');
      break;
  }
};

interface ProtectedRouteProps {
  children: React.ReactNode;
  adminOnly?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, adminOnly = false }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  logProtectedRouteEvent('info', 'ProtectedRoute initialized', { adminOnly });

  useEffect(() => {
    const checkAuth = async () => {
      logProtectedRouteEvent('info', 'Starting authentication check');
      
      const token = authService.getToken();
      const user = authService.getCurrentUser();

      if (!token || !user) {
        logProtectedRouteEvent('warn', 'No token or user found, authentication failed');
        setIsAuthenticated(false);
        return;
      }

      logProtectedRouteEvent('info', 'Found token and user, verifying token', { 
        username: user.username, 
        role: user.role 
      });

      try {
        const result = await authService.verifyToken(token);
        if (result.success) {
          setIsAuthenticated(true);
          setIsAdmin(user.role === 'admin');
          logProtectedRouteEvent('info', 'Token verification successful', { 
            username: user.username, 
            role: user.role,
            isAdmin: user.role === 'admin'
          });
        } else {
          // Token is invalid, clear storage
          logProtectedRouteEvent('warn', 'Token verification failed, clearing storage', { 
            error: result.message 
          });
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user');
          setIsAuthenticated(false);
        }
      } catch (error) {
        logProtectedRouteEvent('error', 'Auth check failed with exception', error);
        setIsAuthenticated(false);
      }
    };

    checkAuth();
  }, []);

  // Show loading while checking authentication
  if (isAuthenticated === null) {
    logProtectedRouteEvent('info', 'Authentication check in progress, showing loading state');
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontSize: '1.1rem',
        color: '#6c757d'
      }}>
        Verifying authentication...
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    logProtectedRouteEvent('warn', 'User not authenticated, redirecting to login');
    return <Navigate to="/login" replace />;
  }

  // Redirect to login if admin access required but user is not admin
  if (adminOnly && !isAdmin) {
    logProtectedRouteEvent('warn', 'Admin access required but user is not admin, redirecting to login');
    return <Navigate to="/login" replace />;
  }

  logProtectedRouteEvent('info', 'Authentication successful, rendering protected content', { 
    isAdmin, 
    adminOnly 
  });
  return <>{children}</>;
};

export default ProtectedRoute;
