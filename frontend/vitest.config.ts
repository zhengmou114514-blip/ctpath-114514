import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  cacheDir: '.vite-cache/vitest',
  plugins: [vue()],
  test: {
    environment: 'jsdom',
  },
})
