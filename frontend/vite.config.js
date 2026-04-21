// vite.config.js

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 1. tailwindcss 플러그인 불러오기
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config>
export default defineConfig({

// 2. tailwindcss() 플러그인(plugin) 추가
  plugins: [react(), tailwindcss()],
});