import { config } from '../config/config';

const API_BASE_URL = config.API_BASE_URL;

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
    return {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    };
  }

  async login(username: string, password: string): Promise<LoginResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      const res = await response.json();
      console.log(res);
      return res;
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async verifyToken(token: string): Promise<VerifyTokenResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/verify-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });

      return await response.json();
    } catch (error) {
      console.error('Verify token error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async logout(): Promise<void> {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
    }
  }

  getToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  getCurrentUser(): any {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }

  // Admin functions
  async getUsers(): Promise<{ success: boolean; users?: User[]; message?: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users`, {
        headers: this.getAuthHeaders(),
      });

      return await response.json();
    } catch (error) {
      console.error('Get users error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async createUser(name: string, username: string, password: string, role: 'admin' | 'va'): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ name, username, password, role }),
      });

      return await response.json();
    } catch (error) {
      console.error('Create user error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async updateUser(userId: string, updates: Partial<User>): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
        method: 'PUT',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(updates),
      });

      return await response.json();
    } catch (error) {
      console.error('Update user error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async deactivateUser(userId: string): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/deactivate`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
      });

      return await response.json();
    } catch (error) {
      console.error('Deactivate user error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async deleteUser(userId: string): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders(),
      });

      return await response.json();
    } catch (error) {
      console.error('Delete user error:', error);
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

  async getScriptLogs(userId?: string, limit: number = 100): Promise<{ success: boolean; script_logs?: ScriptLog[]; message?: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/scripts`, {
        headers: this.getAuthHeaders(),
      });

      const data = await response.json();
      
      if (response.ok && data) {
        // Convert the scripts object to an array format expected by the frontend
        const scriptLogs = Object.entries(data).map(([scriptId, scriptData]: [string, any]) => ({
          script_id: scriptId,
          user_name: scriptData.user_id || 'Unknown',
          user_username: scriptData.user_id || 'unknown',
          script_type: scriptData.type,
          status: scriptData.status,
          start_time: scriptData.start_time,
          end_time: scriptData.end_time,
          config: scriptData.config,
          error: scriptData.error,
          logs_available: true
        }));

        return {
          success: true,
          script_logs: scriptLogs
        };
      }

      return { success: false, message: 'Failed to fetch script logs' };
    } catch (error) {
      console.error('Get script logs error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async getAdminStats(): Promise<{ success: boolean; stats?: AdminStats; message?: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/stats`, {
        headers: this.getAuthHeaders(),
      });

      return await response.json();
    } catch (error) {
      console.error('Get admin stats error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  // Instagram Accounts Management
  async getInstagramAccounts(): Promise<{ success: boolean; accounts?: InstagramAccount[]; message?: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/instagram-accounts`, {
        headers: this.getAuthHeaders(),
      });

      return await response.json();
    } catch (error) {
      console.error('Get Instagram accounts error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async addInstagramAccount(username: string, password: string, email: string, phone: string, notes: string): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/instagram-accounts`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ username, password, email, phone, notes }),
      });

      return await response.json();
    } catch (error) {
      console.error('Add Instagram account error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async updateInstagramAccount(accountId: string, updates: Partial<InstagramAccount>): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/instagram-accounts/${accountId}`, {
        method: 'PUT',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(updates),
      });

      return await response.json();
    } catch (error) {
      console.error('Update Instagram account error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async deleteInstagramAccount(accountId: string): Promise<ApiResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/instagram-accounts/${accountId}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders(),
      });

      return await response.json();
    } catch (error) {
      console.error('Delete Instagram account error:', error);
      return { success: false, message: 'Network error' };
    }
  }

  async importInstagramAccounts(file: File): Promise<{ success: boolean; added_count?: number; skipped_count?: number; message?: string }> {
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

      return await response.json();
    } catch (error) {
      console.error('Import Instagram accounts error:', error);
      return { success: false, message: 'Network error' };
    }
  }
}

export const authService = new AuthService();
