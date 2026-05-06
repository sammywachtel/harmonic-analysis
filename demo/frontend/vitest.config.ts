import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true,
    // Keep Playwright e2e specs out of Vitest's runner — they live in /e2e
    // and execute under @playwright/test.
    exclude: ['node_modules', 'dist', 'e2e/**'],
  },
});
