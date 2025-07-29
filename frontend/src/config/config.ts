// Configuration settings for the application
const isDevelopment = process.env.NODE_ENV === 'development';
const apiUrl = isDevelopment 
  ? 'http://localhost:5000' 
  : 'https://wdyautomation.shop';

export const config = {
  API_BASE_URL: `${apiUrl}/api`,
  isDevelopment,
  environment: process.env.NODE_ENV || 'development',
};

export default config;
