const ACCESS_TOKEN_KEY = "jwtToken";
const REFRESH_TOKEN_KEY = "refreshToken";
const PERMISSIONS_KEY = "adminPermissions";
const ADMIN_KEY = "adminProfile";

function getStorageValue(key: string) {
  const sessionValue = sessionStorage.getItem(key);
  if (sessionValue !== null) {
    return sessionValue;
  }

  const legacyLocalValue = localStorage.getItem(key);
  if (legacyLocalValue !== null) {
    sessionStorage.setItem(key, legacyLocalValue);
    localStorage.removeItem(key);
    return legacyLocalValue;
  }

  return null;
}

function setStorageValue(key: string, value: string) {
  sessionStorage.setItem(key, value);
  localStorage.removeItem(key);
}

function removeStorageValue(key: string) {
  sessionStorage.removeItem(key);
  localStorage.removeItem(key);
}

export const authStorage = {
  getAccessToken() {
    return getStorageValue(ACCESS_TOKEN_KEY);
  },

  setAccessToken(token: string) {
    setStorageValue(ACCESS_TOKEN_KEY, token);
  },

  getRefreshToken() {
    return getStorageValue(REFRESH_TOKEN_KEY);
  },

  setRefreshToken(token: string) {
    setStorageValue(REFRESH_TOKEN_KEY, token);
  },

  getPermissions() {
    const raw = getStorageValue(PERMISSIONS_KEY);
    return raw ? JSON.parse(raw) : [];
  },

  setPermissions(permissions: unknown) {
    setStorageValue(PERMISSIONS_KEY, JSON.stringify(permissions));
  },

  getAdmin<T>() {
    const raw = getStorageValue(ADMIN_KEY);
    return raw ? (JSON.parse(raw) as T) : null;
  },

  setAdmin(admin: unknown) {
    setStorageValue(ADMIN_KEY, JSON.stringify(admin));
  },

  clear() {
    removeStorageValue(ACCESS_TOKEN_KEY);
    removeStorageValue(REFRESH_TOKEN_KEY);
    removeStorageValue(PERMISSIONS_KEY);
    removeStorageValue(ADMIN_KEY);
  },
};
