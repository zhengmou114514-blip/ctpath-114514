import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  cacheDir: '.vite-cache/vitest',
  resolve: {
    preserveSymlinks: true,
  },
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    pool: 'vmThreads',
    poolOptions: {
      vmThreads: {
        singleThread: true,
      },
    },
  },
})
