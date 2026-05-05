/**
 * Dev server proxy: browser calls same-origin `/api/*` → backend (no CORS).
 * Default target matches backend `API_PORT` (8010). Override when needed:
 *   PowerShell: $env:BACKEND_URL='http://127.0.0.1:8088'; npm start
 */
const target = process.env.BACKEND_URL || "http://127.0.0.1:8010";

module.exports = {
  "/api": {
    target,
    secure: false,
    changeOrigin: true,
    pathRewrite: { "^/api": "" },
  },
};
