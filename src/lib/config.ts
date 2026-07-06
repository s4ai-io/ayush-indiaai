/**
 * Central configuration for the Ayush AI frontend.
 *
 * All API base URLs and shared constants should be read from here.
 * Never hardcode backend URLs directly in pages or components.
 *
 * Environment variables (set in .env.local):
 *   NEXT_PUBLIC_API_BASE     — override for browser API calls; leave unset for
 *                              same-origin via the Next rewrite proxy (required
 *                              for httpOnly cookie auth to flow automatically)
 *   NEXT_PUBLIC_COPILOT_URL  — CopilotKit runtime route (default: /api/copilotkit)
 */

/**
 * Base for browser calls to the FastAPI backend. Empty string means
 * same-origin: /api/* is proxied by next.config.ts rewrites, and the
 * ayush_token httpOnly cookie rides along without CORS/SameSite issues.
 */
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? '';

/** CopilotKit runtime URL (Next.js API route) */
export const COPILOT_RUNTIME_URL = process.env.NEXT_PUBLIC_COPILOT_URL ?? '/api/copilotkit';

// ── Timeout constants (keep in sync with backend/config.py) ──────────────────
/** Max seconds for the CopilotKit SSE route & AG-UI workflow */
export const AGENT_TIMEOUT_SECONDS = 300;

/** Next.js rewrite proxy timeout (ms) — covers Modal ASR cold starts */
export const PROXY_TIMEOUT_MS = 120_000;
