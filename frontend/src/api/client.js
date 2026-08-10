import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

const client = axios.create({
  baseURL: BASE_URL,
});

const TOKEN_KEY = 'dms_access_token';
const REFRESH_KEY = 'dms_refresh_token';

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens({ access, refresh }) {
  if (access) localStorage.setItem(TOKEN_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

client.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshPromise = null;

async function refreshAccessToken() {
  const refresh = getRefreshToken();
  if (!refresh) throw new Error('No refresh token available');
  const resp = await axios.post(`${BASE_URL}/auth/refresh/`, { refresh });
  setTokens({ access: resp.data.access, refresh: resp.data.refresh });
  return resp.data.access;
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error;
    if (!response) {
      return Promise.reject(error);
    }

    const isAuthEndpoint = config.url?.includes('/auth/login') || config.url?.includes('/auth/refresh');

    if (response.status === 401 && !config._retry && !isAuthEndpoint && getRefreshToken()) {
      config._retry = true;
      try {
        if (!refreshPromise) {
          refreshPromise = refreshAccessToken().finally(() => {
            refreshPromise = null;
          });
        }
        const newAccess = await refreshPromise;
        config.headers.Authorization = `Bearer ${newAccess}`;
        return client(config);
      } catch (refreshError) {
        clearTokens();
        window.dispatchEvent(new CustomEvent('dms:session-expired'));
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default client;
