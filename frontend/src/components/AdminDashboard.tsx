import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService, User, ActivityLog, AdminStats, InstagramAccount, ScriptLog } from '../services/authService';
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

  useEffect(() => {
    // Verify admin access
    const user = authService.getCurrentUser();
    if (!user || user.role !== 'admin') {
      navigate('/login');
      return;
    }

    loadData();
  }, [navigate]);

  // Reload script logs when selected user changes
  useEffect(() => {
    if (activeTab === 'logs') {
      loadScriptLogs();
    }
  }, [selectedUserId, activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [usersRes, logsRes, statsRes, accountsRes, scriptLogsRes] = await Promise.all([
        authService.getUsers(),
        authService.getActivityLogs(),
        authService.getAdminStats(),
        authService.getInstagramAccounts(),
        authService.getScriptLogs(selectedUserId || undefined, 100)
      ]);

      if (usersRes.success && usersRes.users) setUsers(usersRes.users);
      if (logsRes.success && logsRes.logs) {
        console.log('Received logs data:', logsRes.logs.slice(0, 3)); // Debug: check first 3 logs
        setLogs(logsRes.logs);
      }
      if (statsRes.success && statsRes.stats) setStats(statsRes.stats);
      if (accountsRes.success && accountsRes.accounts) setInstagramAccounts(accountsRes.accounts);
      if (scriptLogsRes.success && scriptLogsRes.script_logs) setScriptLogs(scriptLogsRes.script_logs);
    } catch (error) {
      console.error('Error loading data:', error);
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadScriptLogs = async () => {
    try {
      const scriptLogsRes = await authService.getScriptLogs(selectedUserId || undefined, 100);
      if (scriptLogsRes.success && scriptLogsRes.script_logs) {
        setScriptLogs(scriptLogsRes.script_logs);
      }
    } catch (error) {
      console.error('Error loading script logs:', error);
    }
  };

  const handleLogout = async () => {
    await authService.logout();
    navigate('/login');
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await authService.createUser(
        newUser.name,
        newUser.username,
        newUser.password,
        newUser.role
      );

      if (result.success) {
        setShowCreateUser(false);
        setNewUser({ name: '', username: '', password: '', role: 'va' });
        loadData(); // Refresh data
      } else {
        setError(result.message || 'Failed to create user');
      }
    } catch (error) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const handleEditUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;

    setLoading(true);
    try {
      const updates: any = { name: editForm.name, is_active: editForm.is_active };
      if (editForm.password) {
        updates.password = editForm.password;
      }

      const result = await authService.updateUser(editingUser.id, updates);

      if (result.success) {
        setEditingUser(null);
        loadData(); // Refresh data
      } else {
        setError(result.message || 'Failed to update user');
      }
    } catch (error) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeactivateUser = async (userId: string) => {
    if (!window.confirm('Are you sure you want to deactivate this user?')) return;

    try {
      const result = await authService.deactivateUser(userId);
      if (result.success) {
        loadData(); // Refresh data
      } else {
        setError(result.message || 'Failed to deactivate user');
      }
    } catch (error) {
      setError('Network error');
    }
  };

  const handleDeleteUser = async (userId: string, username: string) => {
    if (!window.confirm(`Are you sure you want to permanently delete user "${username}"? This action cannot be undone.`)) return;

    setLoading(true);
    try {
      const result = await authService.deleteUser(userId);
      if (result.success) {
        loadData(); // Refresh data
      } else {
        setError(result.message || 'Failed to delete user');
      }
    } catch (error) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const startEditUser = (user: User) => {
    setEditingUser(user);
    setEditForm({
      name: user.name,
      password: '',
      is_active: user.is_active
    });
  };

  // Instagram Accounts Management Functions
  const handleCreateAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await authService.addInstagramAccount(
        newAccount.username,
        newAccount.password,
        newAccount.email,
        newAccount.phone,
        newAccount.notes
      );

      if (result.success) {
        setShowCreateAccount(false);
        setNewAccount({ username: '', password: '', email: '', phone: '', notes: '' });
        loadData(); // Refresh data
      } else {
        setError(result.message || 'Failed to create account');
      }
    } catch (error) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const handleEditAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingAccount) return;

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
      }

      const result = await authService.updateInstagramAccount(editingAccount.id, updates);

      if (result.success) {
        setEditingAccount(null);
        loadData(); // Refresh data
      } else {
        setError(result.message || 'Failed to update account');
      }
    } catch (error) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async (accountId: string, username: string) => {
    if (!window.confirm(`Are you sure you want to permanently delete Instagram account "${username}"? This action cannot be undone.`)) return;

    setLoading(true);
    try {
      const result = await authService.deleteInstagramAccount(accountId);
      if (result.success) {
        loadData(); // Refresh data
      } else {
        setError(result.message || 'Failed to delete account');
      }
    } catch (error) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const handleImportAccounts = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importFile) {
      setError('Please select a file to import');
      return;
    }

    setLoading(true);
    try {
      const result = await authService.importInstagramAccounts(importFile);
      
      if (result.success) {
        setShowImportAccounts(false);
        setImportFile(null);
        loadData(); // Refresh data
        
        let message = `Successfully imported ${result.added_count} accounts`;
        if (result.skipped_count && result.skipped_count > 0) {
          message += `, skipped ${result.skipped_count} accounts`;
        }
        alert(message);
      } else {
        setError(result.message || 'Failed to import accounts');
      }
    } catch (error) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const startEditAccount = (account: InstagramAccount) => {
    setEditingAccount(account);
    setEditAccountForm({
      username: account.username,
      password: '',
      email: account.email,
      phone: account.phone,
      notes: account.notes,
      is_active: account.is_active
    });
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
          <button onClick={() => setError('')}>×</button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="admin-tabs">
        <button
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          📊 Overview
        </button>
        <button
          className={`tab-button ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          👥 Users
        </button>
        <button
          className={`tab-button ${activeTab === 'accounts' ? 'active' : ''}`}
          onClick={() => setActiveTab('accounts')}
        >
          📱 Instagram Accounts
        </button>
        <button
          className={`tab-button ${activeTab === 'logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('logs')}
        >
          📋 Script Logs
        </button>
        <button
          className={`tab-button ${activeTab === 'session-logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('session-logs')}
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
                onClick={() => setShowCreateUser(true)}
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
                  onClick={() => setShowCreateAccount(true)}
                >
                  + Add Account
                </button>
                <button
                  className="import-accounts-btn"
                  onClick={() => setShowImportAccounts(true)}
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
                              onClick={() => window.open(`/script/${log.script_id}/logs`, '_blank')}
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
                    <tr key={index}>
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
    </div>
  );
};

export default AdminDashboard;
