import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService, User, ActivityLog, AdminStats, InstagramAccount, ScriptLog } from '../services/authService';
import { getApiUrl, getApiHeaders } from '../utils/apiUtils';
import './AdminDashboard.css';

const AdminDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'logs' | 'session-logs' | 'accounts'>('overview');
  const [users, setUsers] = useState<User[]>([]);
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [scriptLogs, setScriptLogs] = useState<ScriptLog[]>([]);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [instagramAccounts, setInstagramAccounts] = useState<InstagramAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedUserId, setSelectedUserId] = useState<string>(''); // For filtering script logs
  
  // User management state
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [newUser, setNewUser] = useState({
    name: '',
    username: '',
    password: '',
    role: 'va' as 'admin' | 'va'
  });
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [editForm, setEditForm] = useState({
    name: '',
    password: '',
    is_active: true
  });
  
  // Logs modal state
  const [showLogsModal, setShowLogsModal] = useState(false);
  const [selectedScriptId, setSelectedScriptId] = useState<string>('');
  const [scriptLogContent, setScriptLogContent] = useState<string>('');
  const [logsLoading, setLogsLoading] = useState(false);
  
  // Instagram Accounts management state
  const [showCreateAccount, setShowCreateAccount] = useState(false);
  const [newAccount, setNewAccount] = useState({
    username: '',
    password: '',
    email: '',
    phone: '',
    notes: ''
  });
  const [editingAccount, setEditingAccount] = useState<InstagramAccount | null>(null);
  const [editAccountForm, setEditAccountForm] = useState({
    username: '',
    password: '',
    email: '',
    phone: '',
    notes: '',
    is_active: true
  });
  const [showImportAccounts, setShowImportAccounts] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  
  const navigate = useNavigate();

  const loadData = useCallback(async () => {
    console.log('AdminDashboard: Starting loadData...');
    setLoading(true);
    try {
      console.log('AdminDashboard: Making parallel API calls...');
      const [usersRes, logsRes, statsRes, accountsRes, scriptLogsRes] = await Promise.all([
        authService.getUsers(),
        authService.getActivityLogs(),
        authService.getAdminStats(),
        authService.getInstagramAccounts(),
        authService.getScriptLogs(selectedUserId || undefined, 100)
      ]);

      console.log('AdminDashboard: API responses received:', { 
        usersSuccess: usersRes.success, 
        logsSuccess: logsRes.success,
        statsSuccess: statsRes.success,
        accountsSuccess: accountsRes.success
      });

      if (usersRes.success && usersRes.users) {
        console.log('AdminDashboard: Setting users:', usersRes.users.length, 'users');
        setUsers(usersRes.users);
      } else {
        console.error('AdminDashboard: Failed to load users:', usersRes.message);
      }

      if (logsRes.success) {
        console.log('AdminDashboard: Setting activity logs:', logsRes.logs?.length || 0, 'logs');
        setLogs(logsRes.logs || []);
      } else {
        console.error('AdminDashboard: Failed to load activity logs:', logsRes.message);
      }

      if (statsRes.success && statsRes.stats) {
        console.log('AdminDashboard: Setting admin stats:', statsRes.stats);
        setStats(statsRes.stats);
      } else {
        console.error('AdminDashboard: Failed to load admin stats:', statsRes.message);
      }

      if (accountsRes.success && accountsRes.accounts) {
        console.log('AdminDashboard: Setting Instagram accounts:', accountsRes.accounts.length, 'accounts');
        setInstagramAccounts(accountsRes.accounts);
      } else {
        console.error('AdminDashboard: Failed to load Instagram accounts:', accountsRes.message);
      }

      if (scriptLogsRes.success && scriptLogsRes.script_logs && Array.isArray(scriptLogsRes.script_logs)) {
        console.log('AdminDashboard: Setting script logs:', scriptLogsRes.script_logs.length, 'logs');
        setScriptLogs(scriptLogsRes.script_logs);
      } else {
        console.error('AdminDashboard: Failed to load script logs:', scriptLogsRes.message || 'Invalid script logs data');
        setScriptLogs([]);
      }
    } catch (error) {
      console.error('AdminDashboard: Error loading data:', error);
    } finally {
      setLoading(false);
      console.log('AdminDashboard: loadData completed');
    }
  }, [selectedUserId]);

  useEffect(() => {
    console.log('AdminDashboard: Component mounted, checking admin access...');
    // Verify admin access
    const user = authService.getCurrentUser();
    console.log('AdminDashboard: Current user:', user);
    
    if (!user || user.role !== 'admin') {
      console.log('AdminDashboard: Access denied, redirecting to login');
      navigate('/login');
      return;
    }

    console.log('AdminDashboard: Admin access verified, loading data...');
    loadData();
  }, [navigate, loadData]);

  const loadScriptLogs = useCallback(async () => {
    console.log('AdminDashboard: Loading script logs for user:', selectedUserId || 'all users');
    try {
      const scriptLogsRes = await authService.getScriptLogs(selectedUserId || undefined, 100);
      console.log('AdminDashboard: Script logs response:', scriptLogsRes);
      
      if (scriptLogsRes.success && scriptLogsRes.script_logs && Array.isArray(scriptLogsRes.script_logs)) {
        console.log('AdminDashboard: Script logs loaded successfully:', scriptLogsRes.script_logs.length, 'logs');
        setScriptLogs(scriptLogsRes.script_logs);
      } else {
        console.error('AdminDashboard: Failed to load script logs:', scriptLogsRes.message || 'Invalid script logs data');
        setScriptLogs([]); // Set empty array as fallback
      }
    } catch (error) {
      console.error('AdminDashboard: Error loading script logs:', error);
    }
  }, [selectedUserId]);

  // Reload script logs when selected user changes
  useEffect(() => {
    console.log('AdminDashboard: Tab or selectedUserId changed:', { activeTab, selectedUserId });
    if (activeTab === 'logs') {
      console.log('AdminDashboard: Loading script logs for user:', selectedUserId || 'all users');
      loadScriptLogs();
    }
  }, [selectedUserId, activeTab, loadScriptLogs]);

  const handleLogout = async () => {
    console.log('AdminDashboard: Logout initiated');
    try {
      await authService.logout();
      console.log('AdminDashboard: Logout successful, navigating to login');
      navigate('/login');
    } catch (error) {
      console.error('AdminDashboard: Logout error:', error);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('AdminDashboard: Creating user with data:', { 
      name: newUser.name, 
      username: newUser.username, 
      role: newUser.role 
    });
    setLoading(true);

    try {
      const result = await authService.createUser(
        newUser.name,
        newUser.username,
        newUser.password,
        newUser.role
      );

      console.log('AdminDashboard: Create user result:', result);

      if (result.success) {
        console.log('AdminDashboard: User created successfully, clearing form and reloading data');
        setShowCreateUser(false);
        setNewUser({ name: '', username: '', password: '', role: 'va' });
        loadData(); // Refresh data
      } else {
        console.error('AdminDashboard: Failed to create user:', result.message);
        setError(result.message || 'Failed to create user');
      }
    } catch (error) {
      console.error('AdminDashboard: Create user network error:', error);
      setError('Network error');
    } finally {
      setLoading(false);
      console.log('AdminDashboard: Create user operation completed');
    }
  };

  const handleEditUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) {
      console.error('AdminDashboard: No user selected for editing');
      return;
    }

    console.log('AdminDashboard: Editing user:', editingUser.id, 'with updates:', {
      name: editForm.name,
      is_active: editForm.is_active,
      passwordChanged: !!editForm.password
    });

    setLoading(true);
    try {
      const updates: any = { name: editForm.name, is_active: editForm.is_active };
      if (editForm.password) {
        updates.password = editForm.password;
        console.log('AdminDashboard: Password will be updated');
      }

      const result = await authService.updateUser(editingUser.id, updates);
      console.log('AdminDashboard: Edit user result:', result);

      if (result.success) {
        console.log('AdminDashboard: User updated successfully, clearing form and reloading data');
        setEditingUser(null);
        loadData(); // Refresh data
      } else {
        console.error('AdminDashboard: Failed to update user:', result.message);
        setError(result.message || 'Failed to update user');
      }
    } catch (error) {
      console.error('AdminDashboard: Edit user network error:', error);
      setError('Network error');
    } finally {
      setLoading(false);
      console.log('AdminDashboard: Edit user operation completed');
    }
  };

  const handleDeactivateUser = async (userId: string) => {
    console.log('AdminDashboard: Deactivating user:', userId);
    if (!window.confirm('Are you sure you want to deactivate this user?')) {
      console.log('AdminDashboard: User deactivation cancelled');
      return;
    }

    console.log('AdminDashboard: User confirmed deactivation, proceeding...');
    try {
      const result = await authService.deactivateUser(userId);
      console.log('AdminDashboard: Deactivate user result:', result);
      
      if (result.success) {
        console.log('AdminDashboard: User deactivated successfully, reloading data');
        loadData(); // Refresh data
      } else {
        console.error('AdminDashboard: Failed to deactivate user:', result.message);
        setError(result.message || 'Failed to deactivate user');
      }
    } catch (error) {
      console.error('AdminDashboard: Deactivate user network error:', error);
      setError('Network error');
    }
  };

  const handleDeleteUser = async (userId: string, username: string) => {
    console.log('AdminDashboard: Deleting user:', userId, 'username:', username);
    if (!window.confirm(`Are you sure you want to permanently delete user "${username}"? This action cannot be undone.`)) {
      console.log('AdminDashboard: User deletion cancelled');
      return;
    }

    console.log('AdminDashboard: User confirmed deletion, proceeding...');
    setLoading(true);
    try {
      const result = await authService.deleteUser(userId);
      console.log('AdminDashboard: Delete user result:', result);
      
      if (result.success) {
        console.log('AdminDashboard: User deleted successfully, reloading data');
        loadData(); // Refresh data
      } else {
        console.error('AdminDashboard: Failed to delete user:', result.message);
        setError(result.message || 'Failed to delete user');
      }
    } catch (error) {
      console.error('AdminDashboard: Delete user network error:', error);
      setError('Network error');
    } finally {
      setLoading(false);
      console.log('AdminDashboard: Delete user operation completed');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const startEditUser = (user: User) => {
    console.log('AdminDashboard: Starting user edit for:', user.id, user.name);
    setEditingUser(user);
    setEditForm({
      name: user.name,
      password: '',
      is_active: user.is_active
    });
    console.log('AdminDashboard: Edit form initialized with user data');
  };

  // Instagram Accounts Management Functions
  const handleCreateAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('AdminDashboard: Creating Instagram account with data:', { 
      username: newAccount.username, 
      email: newAccount.email, 
      phone: newAccount.phone,
      hasNotes: !!newAccount.notes
    });
    setLoading(true);

    try {
      const result = await authService.addInstagramAccount(
        newAccount.username,
        newAccount.password,
        newAccount.email,
        newAccount.phone,
        newAccount.notes
      );

      console.log('AdminDashboard: Create Instagram account result:', result);

      if (result.success) {
        console.log('AdminDashboard: Instagram account created successfully, clearing form and reloading data');
        setShowCreateAccount(false);
        setNewAccount({ username: '', password: '', email: '', phone: '', notes: '' });
        loadData(); // Refresh data
      } else {
        console.error('AdminDashboard: Failed to create Instagram account:', result.message);
        setError(result.message || 'Failed to create account');
      }
    } catch (error) {
      console.error('AdminDashboard: Create Instagram account network error:', error);
      setError('Network error');
    } finally {
      setLoading(false);
      console.log('AdminDashboard: Create Instagram account operation completed');
    }
  };

  const handleEditAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingAccount) {
      console.error('AdminDashboard: No Instagram account selected for editing');
      return;
    }

    console.log('AdminDashboard: Editing Instagram account:', editingAccount.id, 'with updates:', {
      username: editAccountForm.username,
      email: editAccountForm.email,
      phone: editAccountForm.phone,
      is_active: editAccountForm.is_active,
      passwordChanged: !!editAccountForm.password
    });

    setLoading(true);
    try {
      const updates: any = {
        username: editAccountForm.username,
        email: editAccountForm.email,
        phone: editAccountForm.phone,
        notes: editAccountForm.notes,
        is_active: editAccountForm.is_active
      };
      
      if (editAccountForm.password) {
        updates.password = editAccountForm.password;
        console.log('AdminDashboard: Instagram account password will be updated');
      }

      const result = await authService.updateInstagramAccount(editingAccount.id, updates);
      console.log('AdminDashboard: Edit Instagram account result:', result);

      if (result.success) {
        console.log('AdminDashboard: Instagram account updated successfully, clearing form and reloading data');
        setEditingAccount(null);
        loadData(); // Refresh data
      } else {
        console.error('AdminDashboard: Failed to update Instagram account:', result.message);
        setError(result.message || 'Failed to update account');
      }
    } catch (error) {
      console.error('AdminDashboard: Edit Instagram account network error:', error);
      setError('Network error');
    } finally {
      setLoading(false);
      console.log('AdminDashboard: Edit Instagram account operation completed');
    }
  };

  const handleDeleteAccount = async (accountId: string, username: string) => {
    console.log('AdminDashboard: Deleting Instagram account:', accountId, 'username:', username);
    if (!window.confirm(`Are you sure you want to permanently delete Instagram account "${username}"? This action cannot be undone.`)) {
      console.log('AdminDashboard: Instagram account deletion cancelled');
      return;
    }

    console.log('AdminDashboard: User confirmed Instagram account deletion, proceeding...');
    setLoading(true);
    try {
      const result = await authService.deleteInstagramAccount(accountId);
      console.log('AdminDashboard: Delete Instagram account result:', result);
      
      if (result.success) {
        console.log('AdminDashboard: Instagram account deleted successfully, reloading data');
        loadData(); // Refresh data
      } else {
        console.error('AdminDashboard: Failed to delete Instagram account:', result.message);
        setError(result.message || 'Failed to delete account');
      }
    } catch (error) {
      console.error('AdminDashboard: Delete Instagram account network error:', error);
      setError('Network error');
    } finally {
      setLoading(false);
      console.log('AdminDashboard: Delete Instagram account operation completed');
    }
  };

  const handleImportAccounts = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('AdminDashboard: Starting Instagram accounts import');
    
    if (!importFile) {
      console.error('AdminDashboard: No file selected for import');
      setError('Please select a file to import');
      return;
    }

    console.log('AdminDashboard: Importing file:', importFile.name, 'Size:', importFile.size, 'bytes');
    setLoading(true);
    
    try {
      const result = await authService.importInstagramAccounts(importFile);
      console.log('AdminDashboard: Import Instagram accounts result:', result);
      
      if (result.success) {
        console.log('AdminDashboard: Import successful - added:', result.added_count, 'skipped:', result.skipped_count);
        setShowImportAccounts(false);
        setImportFile(null);
        loadData(); // Refresh data
        
        let message = `Successfully imported ${result.added_count} accounts`;
        if (result.skipped_count && result.skipped_count > 0) {
          message += `, skipped ${result.skipped_count} accounts`;
        }
        console.log('AdminDashboard: Import completed:', message);
        alert(message);
      } else {
        console.error('AdminDashboard: Import failed:', result.message);
        setError(result.message || 'Failed to import accounts');
      }
    } catch (error) {
      console.error('AdminDashboard: Import Instagram accounts network error:', error);
      setError('Network error');
    } finally {
      setLoading(false);
      console.log('AdminDashboard: Import Instagram accounts operation completed');
    }
  };

  const startEditAccount = (account: InstagramAccount) => {
    console.log('AdminDashboard: Starting Instagram account edit for:', account.id, account.username);
    setEditingAccount(account);
    setEditAccountForm({
      username: account.username,
      password: '',
      email: account.email,
      phone: account.phone,
      notes: account.notes,
      is_active: account.is_active
    });
    console.log('AdminDashboard: Instagram account edit form initialized with account data');
  };

  // Logs modal functions
  const viewScriptLogs = async (scriptId: string) => {
    console.log('AdminDashboard: Viewing script logs for:', scriptId);
    setSelectedScriptId(scriptId);
    setShowLogsModal(true);
    setLogsLoading(true);
    
    try {
      const response = await fetch(getApiUrl(`/script/${scriptId}/logs`), {
        headers: getApiHeaders()
      });
      
      console.log('AdminDashboard: Script logs API response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('AdminDashboard: Script logs data received:', data.logs ? data.logs.length + ' log lines' : 'No logs');
        setScriptLogContent(data.logs.join('\n'));
      } else {
        console.error('AdminDashboard: Failed to load script logs, status:', response.status);
        setScriptLogContent('Failed to load logs');
      }
    } catch (error) {
      console.error('AdminDashboard: Error loading script logs:', error);
      setScriptLogContent('Error loading logs');
    } finally {
      setLogsLoading(false);
      console.log('AdminDashboard: Script logs loading completed');
    }
  };

  const downloadScriptLogs = async () => {
    if (!selectedScriptId) {
      console.error('AdminDashboard: No script ID selected for download');
      return;
    }
    
    console.log('AdminDashboard: Downloading logs for script:', selectedScriptId);
    
    try {
      const response = await fetch(getApiUrl(`/script/${selectedScriptId}/download-logs`), {
        headers: getApiHeaders()
      });
      
      console.log('AdminDashboard: Download logs API response status:', response.status);
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `script_${selectedScriptId}_logs.txt`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        console.log('AdminDashboard: Script logs downloaded successfully');
      } else {
        console.error('AdminDashboard: Failed to download logs, status:', response.status);
        alert('Failed to download logs');
      }
    } catch (error) {
      console.error('AdminDashboard: Error downloading script logs:', error);
      alert('Error downloading logs');
    }
  };

  return (
    <div className="admin-dashboard">
      {/* Header */}
      <div className="admin-header">
        <div className="header-left">
          <h1>Admin Dashboard</h1>
          <p>Instagram Automation System</p>
        </div>
        <div className="header-right">
          <span className="admin-user">👑 {authService.getCurrentUser()?.name}</span>
          <button className="logout-btn" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={() => {
            console.log('AdminDashboard: Clearing error message:', error);
            setError('');
          }}>×</button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="admin-tabs">
        <button
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => {
            console.log('AdminDashboard: Switching to overview tab');
            setActiveTab('overview');
          }}
        >
          📊 Overview
        </button>
        <button
          className={`tab-button ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => {
            console.log('AdminDashboard: Switching to users tab');
            setActiveTab('users');
          }}
        >
          👥 Users
        </button>
        <button
          className={`tab-button ${activeTab === 'accounts' ? 'active' : ''}`}
          onClick={() => {
            console.log('AdminDashboard: Switching to accounts tab');
            setActiveTab('accounts');
          }}
        >
          📱 Instagram Accounts
        </button>
        <button
          className={`tab-button ${activeTab === 'logs' ? 'active' : ''}`}
          onClick={() => {
            console.log('AdminDashboard: Switching to logs tab');
            setActiveTab('logs');
          }}
        >
          📋 Script Logs
        </button>
        <button
          className={`tab-button ${activeTab === 'session-logs' ? 'active' : ''}`}
          onClick={() => {
            console.log('AdminDashboard: Switching to session-logs tab');
            setActiveTab('session-logs');
          }}
        >
          📈 Session Logs
        </button>
      </div>

      {/* Content Area */}
      <div className="admin-content">
        {loading && <div className="loading-overlay">Loading...</div>}

        {/* Overview Tab */}
        {activeTab === 'overview' && stats && (
          <div className="overview-tab">
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">👥</div>
                <div className="stat-content">
                  <h3>{stats.total_users}</h3>
                  <p>Total Users</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">✅</div>
                <div className="stat-content">
                  <h3>{stats.active_users}</h3>
                  <p>Active Users</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">🤖</div>
                <div className="stat-content">
                  <h3>{stats.va_users}</h3>
                  <p>VA Users</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">👑</div>
                <div className="stat-content">
                  <h3>{stats.admin_users}</h3>
                  <p>Admin Users</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">🔄</div>
                <div className="stat-content">
                  <h3>{stats.running_scripts}</h3>
                  <p>Running Scripts</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">📊</div>
                <div className="stat-content">
                  <h3>{stats.recent_logins}</h3>
                  <p>Recent Logins (24h)</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className="users-tab">
            <div className="users-header">
              <h2>User Management</h2>
              <button
                className="create-user-btn"
                onClick={() => {
                  console.log('AdminDashboard: Opening create user modal');
                  setShowCreateUser(true);
                }}
              >
                + Create User
              </button>
            </div>

            {/* Users Table */}
            <div className="users-table">
              <table>
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Username</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Last Login</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td>
                        <div className="user-info">
                          <span className="user-name">{user.name}</span>
                          <span className="user-id">{user.id}</span>
                        </div>
                      </td>
                      <td>{user.username}</td>
                      <td>
                        <span className={`role-badge ${user.role}`}>
                          {user.role === 'admin' ? '👑 Admin' : '🤖 VA'}
                        </span>
                      </td>
                      <td>
                        <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>
                        {user.last_login ? formatDate(user.last_login) : 'Never'}
                      </td>
                      <td>
                        <div className="user-actions">
                          <button
                            className="edit-btn"
                            onClick={() => startEditUser(user)}
                          >
                            Edit
                          </button>
                          {user.is_active && user.role !== 'admin' && (
                            <button
                              className="deactivate-btn"
                              onClick={() => handleDeactivateUser(user.id)}
                            >
                              Deactivate
                            </button>
                          )}
                          <button
                            className="delete-btn"
                            onClick={() => handleDeleteUser(user.id, user.username)}
                            title="Delete user permanently"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Instagram Accounts Tab */}
        {activeTab === 'accounts' && (
          <div className="accounts-tab">
            <div className="accounts-header">
              <h2>Instagram Accounts Management</h2>
              <div className="accounts-actions">
                <button
                  className="create-account-btn"
                  onClick={() => {
                    console.log('AdminDashboard: Opening create Instagram account modal');
                    setShowCreateAccount(true);
                  }}
                >
                  + Add Account
                </button>
                <button
                  className="import-accounts-btn"
                  onClick={() => {
                    console.log('AdminDashboard: Opening import Instagram accounts modal');
                    setShowImportAccounts(true);
                  }}
                >
                  📂 Import Accounts
                </button>
              </div>
            </div>

            {/* Accounts Table */}
            <div className="accounts-table">
              <table>
                <thead>
                  <tr>
                    <th>Username</th>
                    <th>Email</th>
                    <th>Email Password</th>
                    <th>Status</th>
                    <th>Last Used</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {instagramAccounts.map((account) => (
                    <tr key={account.id}>
                      <td>
                        <div className="account-info">
                          <span className="account-username">{account.username}</span>
                          {account.notes && (
                            <span className="account-notes" title={account.notes}>📝</span>
                          )}
                        </div>
                      </td>
                      <td>{account.email || '-'}</td>
                      <td>{account.phone || '-'}</td>
                      <td>
                        <span className={`status-badge ${account.is_active ? 'active' : 'inactive'}`}>
                          {account.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>
                        {account.last_used ? formatDate(account.last_used) : 'Never'}
                      </td>
                      <td>{formatDate(account.created_at)}</td>
                      <td>
                        <div className="account-actions">
                          <button
                            className="edit-btn"
                            onClick={() => startEditAccount(account)}
                          >
                            Edit
                          </button>
                          <button
                            className="delete-btn"
                            onClick={() => handleDeleteAccount(account.id, account.username)}
                            title="Delete account permanently"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {instagramAccounts.length === 0 && (
              <div className="no-accounts">
                <p>No Instagram accounts found. Add some accounts to get started.</p>
              </div>
            )}
          </div>
        )}

        {/* Logs Tab */}
        {activeTab === 'logs' && (
          <div className="logs-tab">
            <div className="logs-header">
              <h2>Script Execution Logs</h2>
              <div className="logs-filters">
                <select
                  value={selectedUserId}
                  onChange={(e) => setSelectedUserId(e.target.value)}
                  className="user-filter"
                >
                  <option value="">All Users</option>
                  {users.filter(user => user.role === 'va').map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.name} ({user.username})
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="logs-table">
              <table>
                <thead>
                  <tr>
                    <th>Script ID</th>
                    <th>User</th>
                    <th>Script Type</th>
                    <th>Status</th>
                    <th>Started</th>
                    <th>Duration</th>
                    <th>Accounts</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {scriptLogs.map((log) => (
                    <tr key={log.script_id}>
                      <td>
                        <span className="script-id" title={log.script_id}>
                          {log.script_id.substring(0, 8)}...
                        </span>
                      </td>
                      <td>
                        <div className="user-info">
                          <span className="user-name">{log.user_name}</span>
                          <small className="user-username">@{log.user_username}</small>
                        </div>
                      </td>
                      <td>
                        <span className={`script-type-badge ${log.script_type}`}>
                          {log.script_type === 'daily_post' ? '📸 Daily Post' :
                           log.script_type === 'dm_automation' ? '💬 DM Automation' :
                           log.script_type === 'warmup' ? '🔥 Warmup' :
                           log.script_type}
                        </span>
                      </td>
                      <td>
                        <span className={`status-badge ${log.status}`}>
                          {log.status === 'running' ? '🔄 Running' :
                           log.status === 'completed' ? '✅ Completed' :
                           log.status === 'error' ? '❌ Error' :
                           log.status === 'stopped' ? '⏹️ Stopped' :
                           log.status}
                        </span>
                      </td>
                      <td>{formatDate(log.start_time)}</td>
                      <td>
                        {log.end_time ? (
                          <span>
                            {Math.round((new Date(log.end_time).getTime() - new Date(log.start_time).getTime()) / 1000 / 60)} min
                          </span>
                        ) : (
                          log.status === 'running' ? (
                            <span>
                              {Math.round((new Date().getTime() - new Date(log.start_time).getTime()) / 1000 / 60)} min
                            </span>
                          ) : '-'
                        )}
                      </td>
                      <td>
                        {log.config?.selected_account_ids?.length || 
                         log.config?.concurrent_accounts || 
                         '-'}
                      </td>
                      <td>
                        <div className="log-actions">
                          {log.logs_available && (
                            <button
                              className="view-logs-btn"
                              onClick={() => viewScriptLogs(log.script_id)}
                              title="View detailed logs"
                            >
                              📋 Logs
                            </button>
                          )}
                          {log.error && (
                            <span className="error-indicator" title={log.error}>
                              ⚠️
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {scriptLogs.length === 0 && (
              <div className="no-logs">
                <p>No script execution logs found.</p>
                {selectedUserId && (
                  <p>Try selecting a different user or view all users.</p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Session Logs Tab */}
        {activeTab === 'session-logs' && (
          <div className="logs-tab">
            <h2>Session Activity Logs</h2>
            <div className="logs-table">
              <table>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>User</th>
                    <th>Action</th>
                    <th>Details</th>
                    <th>Location</th>
                    <th>IP Address</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log, index) => (
                    <tr key={`${log.timestamp}-${log.user_id}-${index}`}>
                      <td>{formatDate(log.timestamp)}</td>
                      <td>{log.user_id}</td>
                      <td>
                        <span className={`action-badge ${log.action}`}>
                          {log.action}
                        </span>
                      </td>
                      <td>{log.details}</td>
                      <td>
                        <div className="location-info">
                          <span className="location-text">
                            {(log.city && log.country) ? `${log.city}, ${log.country}` : 
                             (log.ip_address === '127.0.0.1' || log.ip_address === 'system') ? 'Local, Local' : 'Unknown'}
                          </span>
                          {log.country_code && log.country_code !== 'UN' && (
                            <span className="country-flag">
                              {log.country_code === 'LC' ? '🏠' : '🌍'}
                            </span>
                          )}
                        </div>
                      </td>
                      <td>
                        <span className="ip-address">{log.ip_address}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Create User Modal */}
      {showCreateUser && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Create New User</h3>
              <button onClick={() => setShowCreateUser(false)}>×</button>
            </div>
            <form onSubmit={handleCreateUser} className="modal-form">
              <div className="form-group">
                <label>Name</label>
                <input
                  type="text"
                  value={newUser.name}
                  onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Username</label>
                <input
                  type="text"
                  value={newUser.username}
                  onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Role</label>
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value as 'admin' | 'va' })}
                >
                  <option value="va">VA</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowCreateUser(false)}>
                  Cancel
                </button>
                <button type="submit" disabled={loading}>
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {editingUser && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Edit User: {editingUser.name}</h3>
              <button onClick={() => setEditingUser(null)}>×</button>
            </div>
            <form onSubmit={handleEditUser} className="modal-form">
              <div className="form-group">
                <label>Name</label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>New Password (leave empty to keep current)</label>
                <input
                  type="password"
                  value={editForm.password}
                  onChange={(e) => setEditForm({ ...editForm, password: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={editForm.is_active}
                    onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
                  />
                  Active
                </label>
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setEditingUser(null)}>
                  Cancel
                </button>
                <button type="submit" disabled={loading}>
                  Update User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Instagram Account Modal */}
      {showCreateAccount && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Add New Instagram Account</h3>
              <button onClick={() => setShowCreateAccount(false)}>×</button>
            </div>
            <form onSubmit={handleCreateAccount} className="modal-form">
              <div className="form-group">
                <label>Username *</label>
                <input
                  type="text"
                  value={newAccount.username}
                  onChange={(e) => setNewAccount({ ...newAccount, username: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Password *</label>
                <input
                  type="password"
                  value={newAccount.password}
                  onChange={(e) => setNewAccount({ ...newAccount, password: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={newAccount.email}
                  onChange={(e) => setNewAccount({ ...newAccount, email: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Email Password</label>
                <input
                  type="text"
                  value={newAccount.phone}
                  onChange={(e) => setNewAccount({ ...newAccount, phone: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Notes</label>
                <textarea
                  value={newAccount.notes}
                  onChange={(e) => setNewAccount({ ...newAccount, notes: e.target.value })}
                  rows={3}
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowCreateAccount(false)}>
                  Cancel
                </button>
                <button type="submit" disabled={loading}>
                  Add Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Instagram Account Modal */}
      {editingAccount && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Edit Instagram Account: {editingAccount.username}</h3>
              <button onClick={() => setEditingAccount(null)}>×</button>
            </div>
            <form onSubmit={handleEditAccount} className="modal-form">
              <div className="form-group">
                <label>Username *</label>
                <input
                  type="text"
                  value={editAccountForm.username}
                  onChange={(e) => setEditAccountForm({ ...editAccountForm, username: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>New Password (leave empty to keep current)</label>
                <input
                  type="password"
                  value={editAccountForm.password}
                  onChange={(e) => setEditAccountForm({ ...editAccountForm, password: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={editAccountForm.email}
                  onChange={(e) => setEditAccountForm({ ...editAccountForm, email: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Email Password</label>
                <input
                  type="text"
                  value={editAccountForm.phone}
                  onChange={(e) => setEditAccountForm({ ...editAccountForm, phone: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Notes</label>
                <textarea
                  value={editAccountForm.notes}
                  onChange={(e) => setEditAccountForm({ ...editAccountForm, notes: e.target.value })}
                  rows={3}
                />
              </div>
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={editAccountForm.is_active}
                    onChange={(e) => setEditAccountForm({ ...editAccountForm, is_active: e.target.checked })}
                  />
                  Active
                </label>
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setEditingAccount(null)}>
                  Cancel
                </button>
                <button type="submit" disabled={loading}>
                  Update Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Import Instagram Accounts Modal */}
      {showImportAccounts && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Import Instagram Accounts</h3>
              <button onClick={() => setShowImportAccounts(false)}>×</button>
            </div>
            <form onSubmit={handleImportAccounts} className="modal-form">
              <div className="form-group">
                <label>Select Excel/CSV File</label>
                <input
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                  required
                />
                <small>
                  File should contain columns: username (required), password (required), email (optional), phone (optional), notes (optional)
                </small>
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowImportAccounts(false)}>
                  Cancel
                </button>
                <button type="submit" disabled={loading || !importFile}>
                  Import Accounts
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Logs Modal */}
      {showLogsModal && (
        <div className="modal-overlay">
          <div className="logs-modal">
            <div className="modal-header">
              <h3>Script Logs: {selectedScriptId.substring(0, 8)}...</h3>
              <div className="modal-actions">
                <button
                  className="download-logs-btn"
                  onClick={downloadScriptLogs}
                  title="Download logs as text file"
                >
                  📥 Download
                </button>
                <button
                  className="modal-close"
                  onClick={() => setShowLogsModal(false)}
                >
                  ×
                </button>
              </div>
            </div>
            <div className="modal-body">
              {logsLoading ? (
                <div className="logs-loading">
                  Loading logs...
                </div>
              ) : (
                <div className="logs-container">
                  <pre className="logs-content">
                    {scriptLogContent || 'No logs available'}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
