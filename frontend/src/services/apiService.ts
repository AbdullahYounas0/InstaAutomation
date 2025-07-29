import axios, { AxiosRequestConfig } from 'axios';
import { authService } from './authService';
import { config } from '../config/config';

// Logging utility for apiService
const logApiEvent = (level: 'info' | 'warn' | 'error', message: string, data?: any) => {
  const timestamp = new Date().toISOString();
  const logMessage = `[ApiService] ${timestamp} - ${level.toUpperCase()}: ${message}`;
  
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

const API_BASE_URL = config.API_BASE_URL;

logApiEvent('info', 'Initializing API service', { baseUrl: API_BASE_URL });

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

logApiEvent('info', 'Axios client created successfully');

// Add request interceptor to include auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = authService.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      logApiEvent('info', 'Request intercepted - auth token added', { 
        url: config.url,
        method: config.method?.toUpperCase(),
        hasToken: true
      });
    } else {
      logApiEvent('warn', 'Request intercepted - no auth token found', { 
        url: config.url,
        method: config.method?.toUpperCase()
      });
    }
    return config;
  },
  (error) => {
    logApiEvent('error', 'Request interceptor error', error);
    return Promise.reject(error);
  }
);

// Add response interceptor to handle auth errors
apiClient.interceptors.response.use(
  (response) => {
    logApiEvent('info', 'Response received successfully', {
      url: response.config.url,
      method: response.config.method?.toUpperCase(),
      status: response.status,
      statusText: response.statusText
    });
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      logApiEvent('warn', 'Unauthorized response - clearing auth and redirecting', {
        url: error.config?.url,
        method: error.config?.method?.toUpperCase(),
        status: error.response.status
      });
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    } else if (error.response) {
      logApiEvent('error', 'API response error', {
        url: error.config?.url,
        method: error.config?.method?.toUpperCase(),
        status: error.response.status,
        statusText: error.response.statusText,
        data: error.response.data
      });
    } else if (error.request) {
      logApiEvent('error', 'Network error - no response received', {
        url: error.config?.url,
        method: error.config?.method?.toUpperCase(),
        message: error.message
      });
    } else {
      logApiEvent('error', 'Request setup error', {
        message: error.message
      });
    }
    return Promise.reject(error);
  }
);

export const apiService = {
  // Script management
  async startDailyPost(formData: FormData) {
    logApiEvent('info', 'Starting daily post automation', { 
      endpoint: '/daily-post/start'
    });
    try {
      const response = await apiClient.post('/daily-post/start', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      logApiEvent('info', 'Successfully started daily post automation', { 
        endpoint: '/daily-post/start',
        scriptId: response.data?.script_id
      });
      return response.data;
    } catch (error) {
      logApiEvent('error', 'Failed to start daily post automation', {
        endpoint: '/daily-post/start',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  },

  async startDMAutomation(formData: FormData) {
    logApiEvent('info', 'Starting DM automation', { 
      endpoint: '/dm-automation/start'
    });
    try {
      const response = await apiClient.post('/dm-automation/start', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      logApiEvent('info', 'Successfully started DM automation', { 
        endpoint: '/dm-automation/start',
        scriptId: response.data?.script_id
      });
      return response.data;
    } catch (error) {
      logApiEvent('error', 'Failed to start DM automation', {
        endpoint: '/dm-automation/start',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  },

  async startWarmup(formData: FormData) {
    logApiEvent('info', 'Starting account warmup', { 
      endpoint: '/warmup/start'
    });
    try {
      const response = await apiClient.post('/warmup/start', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      logApiEvent('info', 'Successfully started account warmup', { 
        endpoint: '/warmup/start',
        scriptId: response.data?.script_id
      });
      return response.data;
    } catch (error) {
      logApiEvent('error', 'Failed to start account warmup', {
        endpoint: '/warmup/start',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  },

  async getScriptStatus(scriptId: string) {
    logApiEvent('info', 'Fetching script status', { 
      endpoint: `/script/${scriptId}/status`,
      scriptId
    });
    try {
      const response = await apiClient.get(`/script/${scriptId}/status`);
      logApiEvent('info', 'Successfully fetched script status', { 
        endpoint: `/script/${scriptId}/status`,
        scriptId,
        status: response.data?.status
      });
      return response.data;
    } catch (error) {
      logApiEvent('error', 'Failed to fetch script status', {
        endpoint: `/script/${scriptId}/status`,
        scriptId,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  },

  async getScriptLogs(scriptId: string) {
    logApiEvent('info', 'Fetching script logs', { 
      endpoint: `/script/${scriptId}/logs`,
      scriptId
    });
    try {
      const response = await apiClient.get(`/script/${scriptId}/logs`);
      logApiEvent('info', 'Successfully fetched script logs', { 
        endpoint: `/script/${scriptId}/logs`,
        scriptId,
        logCount: response.data?.logs?.length || 'unknown'
      });
      return response.data;
    } catch (error) {
      logApiEvent('error', 'Failed to fetch script logs', {
        endpoint: `/script/${scriptId}/logs`,
        scriptId,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  },

  async stopScript(scriptId: string) {
    logApiEvent('info', 'Stopping script', { 
      endpoint: `/script/${scriptId}/stop`,
      scriptId
    });
    try {
      const response = await apiClient.post(`/script/${scriptId}/stop`);
      logApiEvent('info', 'Successfully stopped script', { 
        endpoint: `/script/${scriptId}/stop`,
        scriptId
      });
      return response.data;
    } catch (error) {
      logApiEvent('error', 'Failed to stop script', {
        endpoint: `/script/${scriptId}/stop`,
        scriptId,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  },

  async listScripts() {
    logApiEvent('info', 'Fetching script list', { 
      endpoint: '/scripts'
    });
    try {
      const response = await apiClient.get('/scripts');
      logApiEvent('info', 'Successfully fetched script list', { 
        endpoint: '/scripts',
        scriptCount: response.data?.length || 'unknown'
      });
      return response.data;
    } catch (error) {
      logApiEvent('error', 'Failed to fetch script list', {
        endpoint: '/scripts',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  },

  async clearScriptLogs(scriptId: string) {
    logApiEvent('info', 'Clearing script logs', { 
      endpoint: `/script/${scriptId}/clear-logs`,
      scriptId
    });
    try {
      const response = await apiClient.post(`/script/${scriptId}/clear-logs`);
      logApiEvent('info', 'Successfully cleared script logs', { 
        endpoint: `/script/${scriptId}/clear-logs`,
        scriptId
      });
      return response.data;
    } catch (error) {
      logApiEvent('error', 'Failed to clear script logs', {
        endpoint: `/script/${scriptId}/clear-logs`,
        scriptId,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  },

  async downloadScriptLogs(scriptId: string) {
    logApiEvent('info', 'Downloading script logs', { 
      endpoint: `/script/${scriptId}/download-logs`,
      scriptId
    });
    try {
      const response = await apiClient.get(`/script/${scriptId}/download-logs`, {
        responseType: 'blob',
      });
      logApiEvent('info', 'Successfully downloaded script logs', { 
        endpoint: `/script/${scriptId}/download-logs`,
        scriptId,
        size: response.data?.size || 'unknown'
      });
      return response;
    } catch (error) {
      logApiEvent('error', 'Failed to download script logs', {
        endpoint: `/script/${scriptId}/download-logs`,
        scriptId,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  },

  // Validation endpoints
  async validateDailyPostFiles(formData: FormData) {
    logApiEvent('info', 'Validating daily post files', { 
      endpoint: '/daily-post/validate'
    });
    try {
      const response = await apiClient.post('/daily-post/validate', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      logApiEvent('info', 'Successfully validated daily post files', { 
        endpoint: '/daily-post/validate',
        isValid: response.data?.valid
      });
      return response.data;
    } catch (error) {
      logApiEvent('error', 'Failed to validate daily post files', {
        endpoint: '/daily-post/validate',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  },

  async validateDMAutomationFiles(formData: FormData) {
    logApiEvent('info', 'Validating DM automation files', { 
      endpoint: '/dm-automation/validate'
    });
    try {
      const response = await apiClient.post('/dm-automation/validate', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      logApiEvent('info', 'Successfully validated DM automation files', { 
        endpoint: '/dm-automation/validate',
        isValid: response.data?.valid
      });
      return response.data;
    } catch (error) {
      logApiEvent('error', 'Failed to validate DM automation files', {
        endpoint: '/dm-automation/validate',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  },

  async validateWarmupFiles(formData: FormData) {
    logApiEvent('info', 'Validating warmup files', { 
      endpoint: '/warmup/validate'
    });
    try {
      const response = await apiClient.post('/warmup/validate', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      logApiEvent('info', 'Successfully validated warmup files', { 
        endpoint: '/warmup/validate',
        isValid: response.data?.valid
      });
      return response.data;
    } catch (error) {
      logApiEvent('error', 'Failed to validate warmup files', {
        endpoint: '/warmup/validate',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  },
};

export default apiClient;
