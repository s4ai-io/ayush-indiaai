import type { NextConfig } from "next";
import os from "os";

// Keep in sync with src/lib/config.ts → PROXY_TIMEOUT_MS
const PROXY_TIMEOUT_MS = 120_000;

// Dynamically collect all local network IPs and loopback addresses
// so the developer can access the Next.js dev server from local network devices or via aliases
const allowedDevOrigins = ["localhost", "127.0.0.1"];
const interfaces = os.networkInterfaces();
for (const name of Object.keys(interfaces)) {
  for (const net of interfaces[name] || []) {
    if (net.address) {
      allowedDevOrigins.push(net.address);
      // Include common dev ports to ensure dev-origins matching succeeds
      allowedDevOrigins.push(`${net.address}:3000`);
      allowedDevOrigins.push(`${net.address}:3001`);
    }
  }
}

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
  allowedDevOrigins,

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
