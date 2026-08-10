import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import client, { clearTokens, getAccessToken, setTokens } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadCurrentUser = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const resp = await client.get('/auth/me/');
      setUser(resp.data);
    } catch {
      clearTokens();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCurrentUser();

    const handleExpired = () => {
      setUser(null);
    };
    window.addEventListener('dms:session-expired', handleExpired);
    return () => window.removeEventListener('dms:session-expired', handleExpired);
  }, [loadCurrentUser]);

  const login = useCallback(async (username, password) => {
    const resp = await client.post('/auth/login/', { username, password });
    setTokens({ access: resp.data.access, refresh: resp.data.refresh });
    setUser(resp.data.user);
    return resp.data.user;
  }, []);

  const logout = useCallback(async () => {
    const refresh = localStorage.getItem('dms_refresh_token');
    try {
      if (refresh) {
        await client.post('/auth/logout/', { refresh });
      }
    } catch {
      // Best-effort: even if the blacklist call fails (e.g. token already
      // expired), still clear local session state below.
    }
    clearTokens();
    setUser(null);
  }, []);

  const value = { user, loading, login, logout, refreshUser: loadCurrentUser };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
