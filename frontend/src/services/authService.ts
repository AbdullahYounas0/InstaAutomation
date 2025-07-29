import { config } from '../config/config';

// Logging utility for auth service
const logAuthEvent = (level: 'info' | 'warn' | 'error', message: string, data?: any) => {
  const timestamp = new Date().toISOString();
  const logMessage = `[AuthService] ${timestamp}: ${message}`;
  
  if (data) {
    console[level](logMessage, data);
  } else {
    console[level](logMessage);
  }
};

const API_BASE_URL = config.API_BASE_URL;
logAuthEvent('info', 'AuthService initialized', { apiBaseUrl: API_BASE_URL });

export interface LoginResponse {
  success: boolean;
  token?: string;
  user?: {
    id: string;
    name: string;
    username: string;
    role: 'admin' | 'va';
  };
  message?: string;
}

export interface VerifyTokenResponse {
  success: boolean;
  payload?: {
    user_id: string;
    username: string;
    name: string;
    role: string;
  };
  message?: string;
}

export interface User {
  id: string;
  name: string;
  username: string;
  role: 'admin' | 'va';
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface ActivityLog {
  timestamp: string;
  user_id: string;
  action: string;
  details: string;
  ip_address: string;
  city?: string;
  country?: string;
  country_code?: string;
}

export interface ScriptLog {
  script_id: string;
  user_name: string;
  user_username: string;
  script_type: string;
  status: string;
  start_time: string;
  end_time?: string;
  config?: any;
  error?: string;
  logs_available: boolean;
}

export interface AdminStats {
  total_users: number;
  active_users: number;
  admin_users: number;
  va_users: number;
  total_scripts: number;
  running_scripts: number;
  recent_logins: number;
}

export interface InstagramAccount {
  id: string;
  username: string;
  password: string;
  email: string;
  phone: string;
  notes: string;
  is_active: boolean;
  created_at: string;
  last_used?: string;
}

export interface ApiResponse {
  success: boolean;
  message?: string;
}

class AuthService {
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('auth_token');
    const hasToken = !!token;
    logAuthEvent('info', 'Getting auth headers', { hasToken });
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` })
    };
  }

  async login(username: string, password: string): Promise<LoginResponse> {
    logAuthEvent('info', 'Attempting user login', { username });
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      const result = await response.json();
      
      if (result.success) {
        logAuthEvent('info', 'Login successful', { 
          username,
          role: result.user?.role,
          hasToken: !!result.token
        });
      } else {
        logAuthEvent('warn', 'Login failed', { 
          username,
          message: result.message
        });
      }
      
      return result;
    } catch (error) {
      logAuthEvent('error', 'Login network error', { 
        username,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return { success: false, message: 'Network error' };
    }
  }

  async verifyToken(token: string): Promise<VerifyTokenResponse> {
    logAuthEvent('info', 'Verifying token', { hasToken: !!token });
    try {
      const response = await fetch(`${API_BASE_URL}/auth/verify-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });

      const result = await response.json();
      
      if (result.success) {
        logAuthEvent('info', 'Token verification successful', { 
          username: result.payload?.username,
          role: result.payload?.role
        });
      } else {
        logAuthEvent('warn', 'Token verification failed', { 
          message: result.message
        });
      }
      
      return result;
    } catch (error) {
      logAuthEvent('error', 'Token verification network error', { 
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return { success: false, message: 'Network error' };
    }
  }

  async logout(): Promise<void> {
    logAuthEvent('info', 'Initiating logout');
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
      });
      logAuthEvent('info', 'Logout request completed');
    } catch (error) {
      logAuthEvent('error', 'Logout network error', { 
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    } finally {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      logAuthEvent('info', 'Local auth data cleared');
    }
  }

  getToken(): string | null {
    const token = localStorage.getItem('auth_token');
    logAuthEvent('info', 'Getting token from localStorage', { hasToken: !!token });
    return token;
  }

  getCurrentUser(): any {
    const userStr = localStorage.getItem('user');
    const user = userStr ? JSON.parse(userStr) : null;
    logAuthEvent('info', 'Getting current user from localStorage', { 
      hasUser: !!user,
      username: user?.username,
      role: user?.role
    });
    return user;
  }

  isAuthenticated(): boolean {
    const authenticated = !!this.getToken();
    logAuthEvent('info', 'Checking authentication status', { authenticated });
    return authenticated;
  }

  isAdmin(): boolean {
    const user = this.getCurrentUser();
    const isAdmin = user?.role === 'admin';
    logAuthEvent('info', 'Checking admin status', { 
      isAdmin,
      role: user?.role,
      username: user?.username
    });
    return isAdmin;
  }

  // FIXED: Script logs function that calls the correct endpoint (/scripts instead of /admin/script-logs)
  async getScriptLogs(userId?: string, limit: number = 100): Promise<{ success: boolean; script_logs?: ScriptLog[]; message?: string }> {
    logAuthEvent('info', 'Fetching script logs', { userId, limit });
    try {
      const response = await fetch(`${API_BASE_URL}/scripts`, {
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        logAuthEvent('error', 'Script logs fetch failed - HTTP error', { 
          status: response.status,
          statusText: response.statusText
        });
        return { success: false, message: `HTTP error! status: ${response.status}` };
      }

      const data = await response.json();
      
      if (data) {
        // Convert the scripts object to an array format expected by the frontend
        const scriptLogs = Object.entries(data).map(([scriptId, scriptData]: [string, any]) => ({
          script_id: scriptId,
          user_name: scriptData.user_id || 'Unknown',
          user_username: scriptData.user_id || 'unknown',
          script_type: scriptData.type || 'unknown',
          status: scriptData.status || 'unknown',
          start_time: scriptData.start_time || new Date().toISOString(),
          end_time: scriptData.end_time,
          config: scriptData.config,
          error: scriptData.error,
          logs_available: true
        }));

        logAuthEvent('info', 'Successfully fetched script logs', { 
          scriptCount: scriptLogs.length
        });

        return {
          success: true,
          script_logs: scriptLogs
        };
      }

      logAuthEvent('warn', 'No script data received');
      return { success: false, message: 'No data received' };
    } catch (error) {
      logAuthEvent('error', 'Script logs fetch network error', { 
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return { success: false, message: 'Network error' };
    }
  }

  // Admin functions
  async getUsers(): Promise<{ success: boolean; users?: User[]; message?: string }> {
    logAuthEvent('info', 'Fetching users (admin operation)');
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users`, {
        headers: this.getAuthHeaders(),
      });

      const result = await response.json();
      
      if (result.success) {
        logAuthEvent('info', 'Successfully fetched users', { 
          userCount: result.users?.length || 'unknown'
        });
      } else {
        logAuthEvent('warn', 'Failed to fetch users', { 
          message: result.message
        });
      }
      
      return result;
    } catch (error) {
      logAuthEvent('error', 'Get users network error', { 
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return { success: false, message: 'Network error' };
    }
  }

  async createUser(name: string, username: string, password: string, role: 'admin' | 'va' = 'va'): Promise<ApiResponse> {
    logAuthEvent('info', 'Creating new user (admin operation)', { username, role });
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ name, username, password, role }),
      });

      const result = await response.json();
      
      if (result.success) {
        logAuthEvent('info', 'Successfully created user', { username, role });
      } else {
        logAuthEvent('warn', 'Failed to create user', { 
          username,
          role,
          message: result.message
        });
      }
      
      return result;
    } catch (error) {
      logAuthEvent('error', 'Create user network error', { 
        username,
        role,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return { success: false, message: 'Network error' };
    }
  }

  async updateUser(userId: string, updates: Partial<User>): Promise<ApiResponse> {
    logAuthEvent('info', 'Updating user (admin operation)', { userId, updates });
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
        method: 'PUT',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(updates),
      });

      const result = await response.json();
      
      if (result.success) {
        logAuthEvent('info', 'Successfully updated user', { userId });
      } else {
        logAuthEvent('warn', 'Failed to update user', { 
          userId,
          message: result.message
        });
      }
      
      return result;
    } catch (error) {
      logAuthEvent('error', 'Update user network error', { 
        userId,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return { success: false, message: 'Network error' };
    }
  }

  async deactivateUser(userId: string): Promise<ApiResponse> {
    logAuthEvent('info', 'Deactivating user (admin operation)', { userId });
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/deactivate`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
      });

      const result = await response.json();
      
      if (result.success) {
        logAuthEvent('info', 'Successfully deactivated user', { userId });
      } else {
        logAuthEvent('warn', 'Failed to deactivate user', { 
          userId,
          message: result.message
        });
      }
      
      return result;
    } catch (error) {
      logAuthEvent('error', 'Deactivate user network error', { 
        userId,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return { success: false, message: 'Network error' };
    }
  }

  async deleteUser(userId: string): Promise<ApiResponse> {
    logAuthEvent('info', 'Deleting user (admin operation)', { userId });
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders(),
      });

      const result = await response.json();
      
      if (result.success) {
        logAuthEvent('info', 'Successfully deleted user', { userId });
      } else {
        logAuthEvent('warn', 'Failed to delete user', { 
          userId,
          message: result.message
        });
      }
      
      return result;
    } catch (error) {
      logAuthEvent('error', 'Delete user network error', { 
        userId,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return { success: false, message: 'Network error' };
    }
  }

  async getActivityLogs(userId?: string, limit: number = 100): Promise<{ success: boolean; logs?: ActivityLog[]; message?: string }> {
    try {
      const params = new URLSearchParams();
      if (userId) params.append('user_id', userId);
      params.append('limit', limit.toString());

      const response = await fetch(`${API_BASE_URL}/admin/activity-logs?${params}`, {
        headers: this.getAuthHeaders(),
      });

      return await response.json();
    } catch (error) {
      console.error('Get activity logs error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async getAdminStats(): Promise<{ success: boolean; stats?: AdminStats; message?: string }> {
    logAuthEvent('info', 'Fetching admin statistics');
    try {
      const response = await fetch(`${API_BASE_URL}/admin/stats`, {
        headers: this.getAuthHeaders(),
      });

      const result = await response.json();
      
      if (result.success) {
        logAuthEvent('info', 'Successfully fetched admin statistics', { 
          hasStats: !!result.stats
        });
      } else {
        logAuthEvent('warn', 'Failed to fetch admin statistics', { 
          message: result.message
        });
      }
      
      return result;
    } catch (error) {
      logAuthEvent('error', 'Get admin stats network error', { 
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return { success: false, message: 'Network error' };
    }
  }

  // Instagram Accounts Management
  async getInstagramAccounts(): Promise<{ success: boolean; accounts?: InstagramAccount[]; message?: string }> {
    logAuthEvent('info', 'Fetching Instagram accounts');
    try {
      const response = await fetch(`${API_BASE_URL}/instagram-accounts`, {
        headers: this.getAuthHeaders(),
      });

      const result = await response.json();
      
      if (result.success) {
        logAuthEvent('info', 'Successfully fetched Instagram accounts', { 
          accountCount: result.accounts?.length || 'unknown'
        });
      } else {
        logAuthEvent('warn', 'Failed to fetch Instagram accounts', { 
          message: result.message
        });
      }
      
      return result;
    } catch (error) {
      logAuthEvent('error', 'Get Instagram accounts network error', { 
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return { success: false, message: 'Network error' };
    }
  }

  async getActiveInstagramAccounts(): Promise<{ success: boolean; accounts?: InstagramAccount[]; message?: string }> {
    logAuthEvent('info', 'Fetching active Instagram accounts');
    try {
      const response = await fetch(`${API_BASE_URL}/instagram-accounts/active`, {
        headers: this.getAuthHeaders(),
      });

      const result = await response.json();
      
      if (result.success) {
        logAuthEvent('info', 'Successfully fetched active Instagram accounts', { 
          accountCount: result.accounts?.length || 'unknown'
        });
      } else {
        logAuthEvent('warn', 'Failed to fetch active Instagram accounts', { 
          message: result.message
        });
      }
      
      return result;
    } catch (error) {
      logAuthEvent('error', 'Get active Instagram accounts network error', { 
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return { success: false, message: 'Network error' };
    }
  }

  async addInstagramAccount(username: string, password: string, email: string, phone: string, notes: string): Promise<ApiResponse> {
    logAuthEvent('info', 'Adding Instagram account (admin operation)', { username });
    try {
      const response = await fetch(`${API_BASE_URL}/admin/instagram-accounts`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ username, password, email, phone, notes }),
      });

      const result = await response.json();
      
      if (result.success) {
        logAuthEvent('info', 'Successfully added Instagram account', { username });
      } else {
        logAuthEvent('warn', 'Failed to add Instagram account', { 
          username,
          message: result.message
        });
      }
      
      return result;
    } catch (error) {
      logAuthEvent('error', 'Add Instagram account network error', { 
        username,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return { success: false, message: 'Network error' };
    }
  }

  async updateInstagramAccount(accountId: string, updates: Partial<InstagramAccount>): Promise<ApiResponse> {
    logAuthEvent('info', 'Updating Instagram account (admin operation)', { accountId });
    try {
      const response = await fetch(`${API_BASE_URL}/admin/instagram-accounts/${accountId}`, {
        method: 'PUT',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(updates),
      });

      const result = await response.json();
      
      if (result.success) {
        logAuthEvent('info', 'Successfully updated Instagram account', { accountId });
      } else {
        logAuthEvent('warn', 'Failed to update Instagram account', { 
          accountId,
          message: result.message
        });
      }
      
      return result;
    } catch (error) {
      logAuthEvent('error', 'Update Instagram account network error', { 
        accountId,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return { success: false, message: 'Network error' };
    }
  }

  async deleteInstagramAccount(accountId: string): Promise<ApiResponse> {
    logAuthEvent('info', 'Deleting Instagram account (admin operation)', { accountId });
    try {
      const response = await fetch(`${API_BASE_URL}/admin/instagram-accounts/${accountId}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders(),
      });

      const result = await response.json();
      
      if (result.success) {
        logAuthEvent('info', 'Successfully deleted Instagram account', { accountId });
      } else {
        logAuthEvent('warn', 'Failed to delete Instagram account', { 
          accountId,
          message: result.message
        });
      }
      
      return result;
    } catch (error) {
      logAuthEvent('error', 'Delete Instagram account network error', { 
        accountId,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return { success: false, message: 'Network error' };
    }
  }

  async importInstagramAccounts(file: File): Promise<{ success: boolean; added_count?: number; skipped_count?: number; message?: string }> {
    logAuthEvent('info', 'Importing Instagram accounts (admin operation)', { 
      fileName: file.name,
      fileSize: file.size
    });
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/admin/instagram-accounts/import`, {
        method: 'POST',
        headers: {
          'Authorization': this.getToken() ? `Bearer ${this.getToken()}` : ''
        },
        body: formData,
      });

      const result = await response.json(); 
      
      if (result.success) {
        logAuthEvent('info', 'Successfully imported Instagram accounts', { 
          fileName: file.name,
          addedCount: result.added_count,
          skippedCount: result.skipped_count
        });
      } else {
        logAuthEvent('warn', 'Failed to import Instagram accounts', { 
          fileName: file.name,
          message: result.message
        });
      }
      
      return result;
    } catch (error) {
      logAuthEvent('error', 'Import Instagram accounts network error', { 
        fileName: file.name,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return { success: false, message: 'Network error' };
    }
  }
}

export const authService = new AuthService();
