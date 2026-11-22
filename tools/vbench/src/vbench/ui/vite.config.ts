import path from "node:path"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"
import { defineConfig } from "vite"

// In development the page talks to a running `vbench serve` (default port 3100) through this proxy.
const api = process.env.VBENCH_API ?? "http://127.0.0.1:3100"

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(import.meta.dirname, "src") } },
  server: { host: "127.0.0.1", port: 5173, proxy: { "/api": api, "/plantuml": api } },
  build: { chunkSizeWarningLimit: 1500 },
})
