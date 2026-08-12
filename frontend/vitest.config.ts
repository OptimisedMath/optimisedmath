import path from 'node:path';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./test/setup.ts'],
    globals: true,
    // Node 25+ ships a native Web Storage stub that breaks jsdom's localStorage.
    // Disable it so Vitest/jsdom install a working in-memory Storage instead.
    // https://github.com/vitest-dev/vitest/issues/8757
    execArgv: ['--no-webstorage'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
});
