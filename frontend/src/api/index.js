// Main API instance
export { default as api } from './axios.js';

// API modules
export {
  auth,
  setAdminAuthTokens,
  getAdminAccessToken,
  getAdminRefreshToken,
  isAdminAuthenticated,
  clearAdminAuthTokens,
} from './auth.js';
export { admin } from './admin.js';
export { restaurant } from './restaurant.js';

// Re-export default axios instance
export { default } from './axios.js'; 
