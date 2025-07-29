import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { authService } from '../services/authService';
import { getApiUrl, getApiHeaders } from '../utils/apiUtils';
import './HomePage.css';

// Logging utility for HomePage
const logHomePageEvent = (level: 'info' | 'warn' | 'error', message: string, data?: any) => {
  const timestamp = new Date().toISOString();
  const logMessage = `[HomePage] ${timestamp} - ${level.toUpperCase()}: ${message}`;
  
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

interface Script {
  id: string;
  type: string;
  status: string;
  start_time: string;
  end_time?: string;
  user_id?: string;
}

interface ScriptStats {
  user_id: string;
  user_role: string;
  total_scripts: number;
  running_scripts: number;
  completed_scripts: number;
  error_scripts: number;
  stopped_scripts: number;
  script_types: Record<string, {
    total: number;
    running: number;
    completed: number;
    error: number;
    stopped: number;
  }>;
  recent_scripts: Script[];
}

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [activeScripts, setActiveScripts] = useState<Record<string, Script>>({});
  const [scriptStats, setScriptStats] = useState<ScriptStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const currentUser = authService.getCurrentUser();

  logHomePageEvent('info', 'HomePage component initialized', { 
    currentUser: currentUser?.username, 
    role: currentUser?.role 
  });

  useEffect(() => {
    logHomePageEvent('info', 'Setting up script polling interval');
    
    // Poll for script status updates every 5 seconds
    const interval = setInterval(() => {
      logHomePageEvent('info', 'Polling for script updates');
      fetchActiveScripts();
      fetchScriptStats();
    }, 5000);
    
    // Initial fetch
    logHomePageEvent('info', 'Performing initial data fetch');
    fetchActiveScripts();
    fetchScriptStats();

    return () => {
      logHomePageEvent('info', 'Cleaning up polling interval');
      clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchActiveScripts = async () => {
    try {
      logHomePageEvent('info', 'Fetching active scripts');
      setFetchError(null);
      const response = await axios.get(getApiUrl('/scripts'), {
        headers: getApiHeaders()
      });
      setActiveScripts(response.data);
      logHomePageEvent('info', 'Successfully fetched active scripts', { 
        scriptCount: Object.keys(response.data).length 
      });
    } catch (error) {
      logHomePageEvent('error', 'Error fetching scripts', error);
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 401) {
          // Unauthorized, redirect to login
          logHomePageEvent('warn', 'Unauthorized access, redirecting to login');
          navigate('/login');
        } else if (error.code === 'ECONNREFUSED' || !error.response) {
          const errorMsg = 'Backend server is not running';
          setFetchError(errorMsg);
          logHomePageEvent('error', errorMsg);
        } else {
          const errorMsg = `Error: ${error.response?.status} ${error.response?.statusText}`;
          setFetchError(errorMsg);
          logHomePageEvent('error', errorMsg);
        }
      } else {
        const errorMsg = 'Unknown error occurred';
        setFetchError(errorMsg);
        logHomePageEvent('error', errorMsg, error);
      }
    } finally {
      setIsLoading(false);
      logHomePageEvent('info', 'Finished fetching active scripts, loading state updated');
    }
  };

  const fetchScriptStats = async () => {
    try {
      logHomePageEvent('info', 'Fetching script statistics');
      const response = await axios.get(getApiUrl('/scripts/stats'), {
        headers: getApiHeaders()
      });
      setScriptStats(response.data);
      logHomePageEvent('info', 'Successfully fetched script statistics', {
        totalScripts: response.data.total_scripts,
        runningScripts: response.data.running_scripts,
        completedScripts: response.data.completed_scripts,
        errorScripts: response.data.error_scripts
      });
    } catch (error) {
      logHomePageEvent('error', 'Error fetching script stats', error);
      // Don't set loading error for stats, as main scripts data is more important
    }
  };

  const handleLogout = async () => {
    logHomePageEvent('info', 'User initiating logout');
    try {
      await authService.logout();
      logHomePageEvent('info', 'Logout successful, redirecting to login');
      navigate('/login');
    } catch (error) {
      logHomePageEvent('error', 'Error during logout', error);
      // Still redirect to login even if logout fails
      navigate('/login');
    }
  };

  const handleButtonClick = (path: string) => {
    logHomePageEvent('info', 'Script button clicked', { path });
    // Open in new tab
    window.open(path, '_blank');
  };

  const getScriptStatus = (type: string) => {
    logHomePageEvent('info', 'Getting script status', { type });
    
    // Use stats data if available, otherwise fall back to activeScripts
    if (scriptStats && scriptStats.script_types[type]) {
      const typeStats = scriptStats.script_types[type];
      let status = 'idle';
      
      if (typeStats.running > 0) status = 'running';
      else if (typeStats.error > 0) status = 'error';
      else if (typeStats.completed > 0) status = 'completed';
      else if (typeStats.stopped > 0) status = 'stopped';
      
      logHomePageEvent('info', 'Script status determined from stats', { 
        type, 
        status, 
        stats: typeStats 
      });
      return status;
    }

    // Fallback to old method
    const scripts = Object.values(activeScripts).filter(script => script.type === type);
    if (scripts.length === 0) {
      logHomePageEvent('info', 'No scripts found for type', { type });
      return 'idle';
    }
    
    const runningScripts = scripts.filter(script => script.status === 'running');
    if (runningScripts.length > 0) {
      logHomePageEvent('info', 'Found running scripts', { type, count: runningScripts.length });
      return 'running';
    }
    
    const recentScript = scripts[scripts.length - 1];
    logHomePageEvent('info', 'Using most recent script status', { 
      type, 
      status: recentScript.status 
    });
    return recentScript.status;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return '#ffa500';
      case 'completed': return '#28a745';
      case 'error': return '#dc3545';
      case 'stopped': return '#6c757d';
      default: return '#007bff';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'running': return 'Running';
      case 'completed': return 'Completed';
      case 'error': return 'Error';
      case 'stopped': return 'Stopped';
      default: return 'Ready';
    }
  };

  return (
    <div className="homepage">
      <header className="homepage-header">
        <div className="header-left">
          <h1>Instagram Automation Dashboard</h1>
          <p>Manage your Instagram automation scripts</p>
        </div>
        <div className="header-right">
          <div className="user-info">
            <span className="user-role">{currentUser?.role === 'admin' ? '👑' : '🤖'}</span>
            <span className="user-name">{currentUser?.name}</span>
          </div>
          <button className="logout-btn" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </header>

      <div className="stats-overview">
        {isLoading ? (
          <>
            <div className="stat-card">
              <h3>Total Scripts</h3>
              <span className="stat-number">...</span>
            </div>
            <div className="stat-card">
              <h3>Running</h3>
              <span className="stat-number">...</span>
            </div>
            <div className="stat-card">
              <h3>Completed</h3>
              <span className="stat-number">...</span>
            </div>
            <div className="stat-card">
              <h3>Errors</h3>
              <span className="stat-number">...</span>
            </div>
          </>
        ) : fetchError ? (
          <div className="error-message">
            <h3>⚠️ Connection Error</h3>
            <p>{fetchError}</p>
            <button onClick={() => { 
              logHomePageEvent('info', 'Retry button clicked, attempting to refetch data');
              fetchActiveScripts(); 
              fetchScriptStats(); 
            }} className="retry-btn">Retry</button>
          </div>
        ) : (
          <>
            <div className="stat-card">
              <h3>Total Scripts</h3>
              <span className="stat-number">{scriptStats?.total_scripts || Object.keys(activeScripts).length}</span>
              <small>{currentUser?.role === 'admin' ? 'All Users' : 'Your Scripts'}</small>
            </div>
            <div className="stat-card">
              <h3>Running</h3>
              <span className="stat-number">
                {scriptStats?.running_scripts || Object.values(activeScripts).filter(s => s.status === 'running').length}
              </span>
              <small>Active Now</small>
            </div>
            <div className="stat-card">
              <h3>Completed</h3>
              <span className="stat-number">
                {scriptStats?.completed_scripts || Object.values(activeScripts).filter(s => s.status === 'completed').length}
              </span>
              <small>Successful</small>
            </div>
            <div className="stat-card">
              <h3>Errors</h3>
              <span className="stat-number">
                {scriptStats?.error_scripts || Object.values(activeScripts).filter(s => s.status === 'error').length}
              </span>
              <small>Failed</small>
            </div>
          </>
        )}
      </div>

      <div className="scripts-grid">
        <div className="script-card">
          <div className="script-icon">📸</div>
          <h2>Insta Daily Post</h2>
          <p>Automatically post images or videos to multiple Instagram accounts simultaneously</p>
          
          <div className="script-status">
            <span 
              className="status-indicator"
              style={{ backgroundColor: getStatusColor(getScriptStatus('daily_post')) }}
            ></span>
            <span className="status-text">
              {getStatusText(getScriptStatus('daily_post'))}
            </span>
          </div>

          <div className="script-features">
            <ul>
              <li>✅ Supports up to 10 accounts</li>
              <li>✅ Image & Video support</li>
              <li>✅ Auto-caption generation</li>
              <li>✅ Concurrent posting</li>
            </ul>
            {scriptStats?.script_types.daily_post && (
              <div className="script-type-stats">
                <small>
                  Total: {scriptStats.script_types.daily_post.total} | 
                  Running: {scriptStats.script_types.daily_post.running} | 
                  Completed: {scriptStats.script_types.daily_post.completed}
                  {scriptStats.script_types.daily_post.error > 0 && ` | Errors: ${scriptStats.script_types.daily_post.error}`}
                </small>
              </div>
            )}
          </div>

          <button 
            className="script-button"
            onClick={() => handleButtonClick('/daily-post')}
            disabled={isLoading}
          >
            Launch Daily Post
          </button>
        </div>

        <div className="script-card">
          <div className="script-icon">💬</div>
          <h2>Insta Send DMs</h2>
          <p>Send personalized direct messages to targeted Instagram users with AI-powered content</p>
          
          <div className="script-status">
            <span 
              className="status-indicator"
              style={{ backgroundColor: getStatusColor(getScriptStatus('dm_automation')) }}
            ></span>
            <span className="status-text">
              {getStatusText(getScriptStatus('dm_automation'))}
            </span>
          </div>

          <div className="script-features">
            <ul>
              <li>✅ AI-powered personalization</li>
              <li>✅ Bulk DM campaigns</li>
              <li>✅ Response tracking</li>
              <li>✅ Rate limit protection</li>
            </ul>
            {scriptStats?.script_types.dm_automation && (
              <div className="script-type-stats">
                <small>
                  Total: {scriptStats.script_types.dm_automation.total} | 
                  Running: {scriptStats.script_types.dm_automation.running} | 
                  Completed: {scriptStats.script_types.dm_automation.completed}
                  {scriptStats.script_types.dm_automation.error > 0 && ` | Errors: ${scriptStats.script_types.dm_automation.error}`}
                </small>
              </div>
            )}
          </div>

          <button 
            className="script-button"
            onClick={() => handleButtonClick('/dm-automation')}
            disabled={isLoading}
          >
            Launch DM Automation
          </button>
        </div>

        <div className="script-card">
          <div className="script-icon">🔥</div>
          <h2>Insta Accounts Warm Up</h2>
          <p>Warm up Instagram accounts with natural human-like activities to build trust and engagement</p>
          
          <div className="script-status">
            <span 
              className="status-indicator"
              style={{ backgroundColor: getStatusColor(getScriptStatus('warmup')) }}
            ></span>
            <span className="status-text">
              {getStatusText(getScriptStatus('warmup'))}
            </span>
          </div>

          <div className="script-features">
            <ul>
              <li>✅ Human-like behavior</li>
              <li>✅ Multiple activities</li>
              <li>✅ Configurable duration</li>
              <li>✅ Concurrent warmup</li>
            </ul>
            {scriptStats?.script_types.warmup && (
              <div className="script-type-stats">
                <small>
                  Total: {scriptStats.script_types.warmup.total} | 
                  Running: {scriptStats.script_types.warmup.running} | 
                  Completed: {scriptStats.script_types.warmup.completed}
                  {scriptStats.script_types.warmup.error > 0 && ` | Errors: ${scriptStats.script_types.warmup.error}`}
                </small>
              </div>
            )}
          </div>

          <button 
            className="script-button"
            onClick={() => handleButtonClick('/warmup')}
            disabled={isLoading}
          >
            Launch Account Warmup
          </button>
        </div>
      </div>

      <div className="recent-activity">
        <h3>Recent Activity</h3>
        <div className="activity-list">
          {scriptStats?.recent_scripts && scriptStats.recent_scripts.length > 0 ? (
            scriptStats.recent_scripts.slice(0, 5).map((script, index) => (
              <div key={`${script.id || index}`} className="activity-item">
                <span className="activity-type">{script.type.replace('_', ' ')}</span>
                <span className="activity-time">
                  {new Date(script.start_time).toLocaleString()}
                </span>
                <span 
                  className="activity-status"
                  style={{ color: getStatusColor(script.status) }}
                >
                  {getStatusText(script.status)}
                </span>
                {currentUser?.role === 'admin' && script.user_id && (
                  <span className="activity-user">by {script.user_id}</span>
                )}
              </div>
            ))
          ) : Object.keys(activeScripts).length > 0 ? (
            Object.entries(activeScripts)
              .sort(([,a], [,b]) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime())
              .slice(0, 5)
              .map(([id, script]) => (
                <div key={id} className="activity-item">
                  <span className="activity-type">{script.type.replace('_', ' ')}</span>
                  <span className="activity-time">
                    {new Date(script.start_time).toLocaleString()}
                  </span>
                  <span 
                    className="activity-status"
                    style={{ color: getStatusColor(script.status) }}
                  >
                    {getStatusText(script.status)}
                  </span>
                  {currentUser?.role === 'admin' && script.user_id && (
                    <span className="activity-user">by {script.user_id}</span>
                  )}
                </div>
              ))
          ) : (
            <p className="no-activity">No recent activity</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default HomePage;
