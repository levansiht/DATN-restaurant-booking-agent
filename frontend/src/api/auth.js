import api from "./axios.js";

export const ADMIN_ACCESS_TOKEN_KEY = "admin_access_token";
export const ADMIN_REFRESH_TOKEN_KEY = "admin_refresh_token";

export const auth = {
  login: (credentials) => api.post("/auth/login", credentials),
  logout: (refreshToken) => api.post("/auth/logout", { refresh: refreshToken }),
  refreshToken: (refreshToken) =>
    api.post("/auth/token/refresh", { refresh: refreshToken }),
};

export const setAdminAuthTokens = ({ accessToken, refreshToken }) => {
  if (accessToken) {
    localStorage.setItem(ADMIN_ACCESS_TOKEN_KEY, accessToken);
  }
  if (refreshToken) {
    localStorage.setItem(ADMIN_REFRESH_TOKEN_KEY, refreshToken);
  }
};

export const getAdminAccessToken = () => {
  return localStorage.getItem(ADMIN_ACCESS_TOKEN_KEY);
};

export const getAdminRefreshToken = () => {
  return localStorage.getItem(ADMIN_REFRESH_TOKEN_KEY);
};

export const isAdminAuthenticated = () => {
  return Boolean(getAdminAccessToken());
};

export const clearAdminAuthTokens = () => {
  localStorage.removeItem(ADMIN_ACCESS_TOKEN_KEY);
  localStorage.removeItem(ADMIN_REFRESH_TOKEN_KEY);
};

export default auth;
