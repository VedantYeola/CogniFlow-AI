import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000, // Forces Vite to run on http://localhost:3000
    strictPort: true, // If 3000 is busy, it will fail instead of picking a random port
  }
})