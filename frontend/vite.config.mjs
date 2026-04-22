import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

const isModelApp = process.env.CTPATH_APP_TARGET === 'model'

export default defineConfig({
  // Keep Vite's temp dependency cache out of node_modules on Windows.
  // This avoids EPERM errors when the package manager or antivirus briefly locks node_modules/.vite.
  cacheDir: '.vite-cache',
  plugins: [vue()],
  resolve: {
    alias: [
      {
        find: /^dayjs\/plugin\/(.*?)(?:\.js)?$/,
        replacement: `${fileURLToPath(new URL('./node_modules/dayjs/esm/plugin/', import.meta.url))}$1/index.js`,
      },
      {
        find: /^dayjs\/locale\/(.*?)(?:\.js)?$/,
        replacement: `${fileURLToPath(new URL('./node_modules/dayjs/esm/locale/', import.meta.url))}$1.js`,
      },
      {
        find: /^dayjs$/,
        replacement: fileURLToPath(new URL('./node_modules/dayjs/esm/index.js', import.meta.url)),
      },
    ],
  },
  optimizeDeps: {
    // Disable dependency pre-bundling in dev on this Windows environment.
    // Explicit aliases above handle the CommonJS packages that would otherwise white-screen the app.
    noDiscovery: true,
  },
  build: isModelApp
    ? {
        rollupOptions: {
          input: fileURLToPath(new URL('./model.html', import.meta.url)),
        },
      }
    : undefined,
  server: {
    port: isModelApp ? 5174 : 5173,
    proxy: {
      '/api': {
        target: isModelApp ? 'http://127.0.0.1:8001' : 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
