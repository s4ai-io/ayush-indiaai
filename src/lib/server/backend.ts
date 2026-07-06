/**
 * Server-side helpers for calling the FastAPI backend.
 *
 * Browser code goes same-origin through the Next rewrite proxy and the
 * ayush_token httpOnly cookie rides along automatically — but server-side
 * code (server actions, route handlers, the CopilotKit runtime) fetches the
 * backend directly, so it must forward the caller's cookie explicitly.
 */
import { cookies } from 'next/headers';

export const BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

const AUTH_COOKIE = 'ayush_token';

/** Headers carrying the current request's auth cookie (empty if signed out). */
export async function authHeaders(): Promise<Record<string, string>> {
    const token = (await cookies()).get(AUTH_COOKIE)?.value;
    return token ? { Cookie: `${AUTH_COOKIE}=${token}` } : {};
}
