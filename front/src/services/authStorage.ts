const ACCESS_TOKEN_KEY = "managerAccessToken";
const REFRESH_TOKEN_KEY = "managerRefreshToken";
const MANAGER_PROFILE_KEY = "managerProfile";

function getStorageValue(key: string) {
  return localStorage.getItem(key);
}

function setStorageValue(key: string, value: string) {
  localStorage.setItem(key, value);
}

function removeStorageValue(key: string) {
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

  getManager<T>() {
    const raw = getStorageValue(MANAGER_PROFILE_KEY);
    return raw ? (JSON.parse(raw) as T) : null;
  },

  setManager(manager: unknown) {
    setStorageValue(MANAGER_PROFILE_KEY, JSON.stringify(manager));
  },

  clear() {
    removeStorageValue(ACCESS_TOKEN_KEY);
    removeStorageValue(REFRESH_TOKEN_KEY);
    removeStorageValue(MANAGER_PROFILE_KEY);
  },
};