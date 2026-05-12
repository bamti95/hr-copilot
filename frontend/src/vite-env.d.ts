/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 백엔드 origin (예: https://xxx.up.railway.app) 또는 끝까지 `/api/v1` 포함 URL */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
