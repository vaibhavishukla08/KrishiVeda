import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// In development, /api requests are forwarded to the FastAPI backend,
// so no API keys or backend URLs are ever bundled into the frontend.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: process.env.VITE_BACKEND_URL || "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
  test: { environment: "node" },
});
