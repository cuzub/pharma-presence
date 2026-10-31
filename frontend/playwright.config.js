import { defineConfig } from '@playwright/test'

// Parcours de bout en bout sur l'environnement de développement (base « presence » avec `flask demo`).
// Réutilise les serveurs déjà lancés, sinon les démarre.
export default defineConfig({
  testDir: './tests/e2e',
  timeout: 60_000,
  workers: 1,
  use: {
    baseURL: 'http://127.0.0.1:5174',
    headless: true,
    acceptDownloads: true
  },
  webServer: [
    {
      command: 'cd ../backend && RATELIMIT_AUTH_LOGIN="100 per minute" FLASK_ENV=development PORT=5002 .venv/bin/python run.py',
      url: 'http://127.0.0.1:5002/api/health',
      reuseExistingServer: true,
      timeout: 60_000
    },
    {
      command: 'npm run dev',
      url: 'http://127.0.0.1:5174',
      reuseExistingServer: true,
      timeout: 60_000
    }
  ]
})
