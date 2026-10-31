import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const backendTarget = process.env.VITE_API_TARGET || 'http://127.0.0.1:5002'

export default defineConfig({
  base: process.env.VITE_BASE_PATH || '/',
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['tests/unit/**/*.spec.js']
  },
  server: {
    host: '127.0.0.1',
    port: 5174,
    proxy: {
      '/api': { target: backendTarget, changeOrigin: true }
    }
  }
})
