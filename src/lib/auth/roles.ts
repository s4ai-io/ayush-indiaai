/**
 * Shared role definitions for RBAC.
 *
 * Used by the login page (post-login redirect), the Next.js middleware
 * (route gating), the sidebar (nav filtering), and the 403 page.
 * Keep ROUTE_ROLES in sync with the backend rules table in
 * backend/security.py — the backend is the authority for API access;
 * this map only controls page navigation.
 */

export type Role = "receptionist" | "doctor" | "admin";

export const ALL_ROLES: Role[] = ["receptionist", "doctor", "admin"];

export interface AuthUser {
  id: string;
  username: string;
  name: string;
  role: Role;
}

/** Where each role lands after login (and from the 403 page). */
export const ROLE_HOME: Record<Role, string> = {
  receptionist: "/registration",
  doctor: "/doctor",
  admin: "/public-health/dashboard",
};

/**
 * Page-route access map, first match wins (checked in order).
 * Routes not listed here but matched by the middleware matcher
 * require authentication with no specific role.
 */
export const ROUTE_ROLES: [RegExp, Role[]][] = [
  [/^\/registration/, ["receptionist", "admin"]],
  [/^\/patients/, ALL_ROLES],
  [/^\/doctor/, ["doctor", "admin"]],
  [/^\/visits/, ["doctor", "admin"]],
  [/^\/public-health/, ["admin"]],
  [/^\/admin/, ["admin"]],
  [/^\/$/, ALL_ROLES],
];

export function allowedRolesFor(pathname: string): Role[] | null {
  for (const [pattern, roles] of ROUTE_ROLES) {
    if (pattern.test(pathname)) return roles;
  }
  return null;
}
