import { NextResponse, type NextRequest } from "next/server";
import { jwtVerify } from "jose";
import { ROLE_HOME, allowedRolesFor, type Role } from "@/lib/auth/roles";

const COOKIE_NAME = "ayush_token";

// Pages reachable without a session. The deprecated redirect-only pages
// stay public so old links keep working (their targets are still gated).
const PUBLIC_PAGES = new Set([
  "/login",
  "/403",
  "/consultation",
  "/forecasting",
  "/trends",
]);

async function verifyToken(token: string): Promise<{ role: Role } | null> {
  const secret = process.env.JWT_SECRET;
  if (!secret) {
    console.error("middleware: JWT_SECRET is not set — all requests treated as unauthenticated");
    return null;
  }
  try {
    const { payload } = await jwtVerify(token, new TextEncoder().encode(secret), {
      algorithms: ["HS256"],
    });
    return typeof payload.role === "string" ? { role: payload.role as Role } : null;
  } catch {
    return null;
  }
}

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get(COOKIE_NAME)?.value;
  const session = token ? await verifyToken(token) : null;

  // Already logged in and visiting /login → send to role home.
  if (pathname === "/login") {
    if (session) {
      return NextResponse.redirect(new URL(ROLE_HOME[session.role] ?? "/", request.url));
    }
    return NextResponse.next();
  }

  if (PUBLIC_PAGES.has(pathname)) {
    return NextResponse.next();
  }

  if (!session) {
    const login = new URL("/login", request.url);
    login.searchParams.set("next", pathname);
    return NextResponse.redirect(login);
  }

  const allowed = allowedRolesFor(pathname);
  if (allowed && !allowed.includes(session.role)) {
    return NextResponse.redirect(new URL("/403", request.url));
  }

  return NextResponse.next();
}

export const config = {
  // Pages only: /api auth is enforced by the FastAPI RBAC middleware
  // (JSON 401/403 through the rewrite proxy), and static assets stay open.
  matcher: ["/((?!api|_next|favicon.ico|.*\\..*).*)"],
};
