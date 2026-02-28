import type { NextConfig } from "next";

// Keep in sync with src/lib/config.ts → PROXY_TIMEOUT_MS
const PROXY_TIMEOUT_MS = 120_000;

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,

  // Increase the rewrite proxy timeout.
  // Modal ASR / IndicTrans2 cold starts can take 20–60 s; the default
  // Next.js proxy timeout drops the connection before the response arrives.
  experimental: {
    proxyTimeout: PROXY_TIMEOUT_MS,
  },

  async rewrites() {
    return [
      {
        // Proxy all /api/* calls to the FastAPI backend.
        // /api/copilotkit is handled by its own Next.js route handler and
        // takes priority over this rewrite automatically — no exclusion needed.
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
    ]
  },
};

export default nextConfig;
