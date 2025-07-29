import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import './LoginPage.css';

// Logging utility for LoginPage
const logLoginEvent = (level: 'info' | 'warn' | 'error', message: string, data?: any) => {
  const timestamp = new Date().toISOString();
  const logMessage = `[LoginPage] ${timestamp} - ${level.toUpperCase()}: ${message}`;
  
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

interface LoginPageProps {}

const LoginPage: React.FC<LoginPageProps> = () => {
  const [showLogin, setShowLogin] = useState(false);
  const [loginType, setLoginType] = useState<'admin' | 'va'>('admin');
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  logLoginEvent('info', 'LoginPage component initialized');

  useEffect(() => {
    logLoginEvent('info', 'Checking existing authentication status');
    
    // Check if user is already logged in
    const token = localStorage.getItem('auth_token');
    if (token) {
      logLoginEvent('info', 'Found existing token, verifying...');
      authService.verifyToken(token).then(result => {
        if (result.success) {
          const user = JSON.parse(localStorage.getItem('user') || '{}');
          logLoginEvent('info', 'Token valid, redirecting user', { 
            username: user.username, 
            role: user.role 
          });
          
          if (user.role === 'admin') {
            navigate('/admin');
          } else {
            navigate('/home');
          }
        } else {
          logLoginEvent('warn', 'Token invalid, clearing storage');
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user');
        }
      }).catch(error => {
        logLoginEvent('error', 'Error verifying token', error);
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
      });
    } else {
      logLoginEvent('info', 'No existing token found');
    }
  }, [navigate]);

  const handleRoleSelection = (role: 'admin' | 'va') => {
    logLoginEvent('info', 'Role selected', { role });
    setLoginType(role);
    setShowLogin(true);
    setError('');
    setCredentials({ username: '', password: '' });
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    logLoginEvent('info', 'Input field changed', { field: name, hasValue: !!value });
    setCredentials(prev => ({
      ...prev,
      [name]: value
    }));
    setError('');
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    logLoginEvent('info', 'Login attempt started', { 
      username: credentials.username, 
      loginType 
    });
    
    setLoading(true);
    setError('');

    try {
      const result = await authService.login(credentials.username, credentials.password);
      
      if (result.success && result.token && result.user) {
        logLoginEvent('info', 'Login successful', { 
          username: result.user.username, 
          role: result.user.role 
        });
        // Store token and user info
        localStorage.setItem('auth_token', result.token);
        localStorage.setItem('user', JSON.stringify(result.user));
        
        // Redirect based on role
        if (result.user.role === 'admin') {
          logLoginEvent('info', 'Redirecting admin user to admin dashboard');
          navigate('/admin');
        } else {
          logLoginEvent('info', 'Redirecting VA user to home page');
          navigate('/home');
        }
      } else {
        const errorMsg = result.message || 'Login failed';
        logLoginEvent('warn', 'Login failed', { error: errorMsg, username: credentials.username });
        setError(errorMsg);
      }
    } catch (error) {
      const errorMsg = 'Network error. Please try again.';
      logLoginEvent('error', 'Login network error', { 
        error, 
        username: credentials.username 
      });
      setError(errorMsg);
    } finally {
      setLoading(false);
      logLoginEvent('info', 'Login attempt completed');
    }
  };

  const handleBack = () => {
    logLoginEvent('info', 'Back button clicked, returning to role selection');
    setShowLogin(false);
    setError('');
    setCredentials({ username: '', password: '' });
  };

  if (!showLogin) {
    return (
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <h1>Instagram Automation System</h1>
            <p>Select your login type to continue</p>
          </div>
          
          <div className="login-options">
            <button 
              className="login-option admin-option"
              onClick={() => handleRoleSelection('admin')}
            >
              <div className="option-icon">👑</div>
              <h3>Admin Login</h3>
              <p>Manage users, track activities, and oversee operations</p>
            </button>
            
            <button 
              className="login-option va-option"
              onClick={() => handleRoleSelection('va')}
            >
              <div className="option-icon">🤖</div>
              <h3>VA Login</h3>
              <p>Access automation tools and manage campaigns</p>
            </button>
          </div>
          
          <div className="login-footer">
            <p>© 2025 Instagram Automation System</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="login-container">
      <div className="login-form-card">
        <div className="login-form-header">
          <button className="back-button" onClick={handleBack}>
            ← Back
          </button>
          <h2>{loginType === 'admin' ? 'Admin' : 'VA'} Login</h2>
          <div className="role-indicator">
            <span className={`role-badge ${loginType}`}>
              {loginType === 'admin' ? '👑 Admin' : '🤖 VA'}
            </span>
          </div>
        </div>

        <form onSubmit={handleLogin} className="login-form">
          {error && (
            <div className="error-message">
              <span>⚠️ {error}</span>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="username"
              value={credentials.username}
              onChange={handleInputChange}
              placeholder={`Enter your ${loginType} username`}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={credentials.password}
              onChange={handleInputChange}
              placeholder="Enter your password"
              required
              disabled={loading}
            />
          </div>

          <button 
            type="submit" 
            className={`login-submit ${loginType}`}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Logging in...
              </>
            ) : (
              `Login as ${loginType === 'admin' ? 'Admin' : 'VA'}`
            )}
          </button>

          {loginType === 'admin' && (
            <div className="admin-hint">
              {/* <small>Default admin credentials: admin / admin123</small> */}
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
