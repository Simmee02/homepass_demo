import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  envDir: '..', // 루트의 .env를 공유해요 (VITE_ 접두사 변수만 프론트에 노출됨)
  server: { proxy: { '/api': 'http://localhost:8000' } },
});
