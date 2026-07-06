# RBAC Migration & Setup Guide

The `Gemma-4-12b` branch adds **login + role-based access control** (receptionist / doctor / admin).
After pulling this branch, the app will redirect everything to `/login` — follow this guide once per machine/database and you're set. Takes ~5 minutes.

## Is a DB migration required?

**Yes, but it is small and fully additive** — nothing is dropped or rewritten:

| Change | What | Why |
|---|---|---|
| New table `users` | id, username, password_hash, role, is_active, created_at | Staff accounts + roles |
| Backfill columns on `treatment_feedbacks` | `original_ai_plan`, `final_plan`, `added_herbs`, `removed_herbs`, `demo_session` | Pre-existing model columns that older databases are missing (`create_all` never ALTERs); without them `/api/visits/{id}` returns 500 |
| Backfill indexes on `medical_records` | `visit_date`, `diagnosis` | Same reason — added to the model after some DBs were created |

There is no Alembic in this project. Everything is handled by **one idempotent script** you can run as many times as you like.

## Quick start (recommended)

```bash
# ── 1. Backend deps ────────────────────────────────────────────────
cd backend
./venv/bin/pip install -r requirements.txt        # pulls new: pyjwt, bcrypt

# ── 2. Backend secret (skip if your .env already has SECRET_KEY) ──
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "COOKIE_SECURE=false" >> .env                # false for local HTTP dev

# ── 3. Run the one-shot migration + seed ──────────────────────────
./venv/bin/python3.11 scripts/setup_rbac.py

# ── 4. Frontend env — JWT_SECRET must EQUAL backend SECRET_KEY ────
cd ..
echo "JWT_SECRET=$(grep '^SECRET_KEY=' backend/.env | cut -d= -f2)" >> .env.local

# ── 5. Frontend deps + restart both servers ───────────────────────
npm install                                        # pulls new: jose
cd backend && ./run.sh                             # terminal 1
npx next dev                                       # terminal 2 (repo root)
```

Then open http://localhost:3000 — you'll land on the login page.

## Demo accounts (created by the script)

| Username | Password | Role | Lands on |
|---|---|---|---|
| `admin` | `Admin@123` | admin — sees & controls everything, incl. **Staff Management** | `/public-health/dashboard` |
| `doctor` | `Doctor@123` | doctor — queue, treatment plans, patient history | `/doctor` |
| `reception` | `Reception@123` | receptionist — registration, queueing, directory (no clinical history) | `/registration` |

Change passwords afterwards from **Staff Management** (admin sidebar) or re-seed with
`SEED_RESET_PASSWORDS=true SEED_ADMIN_PASSWORD=... ./venv/bin/python3.11 scripts/seed_users.py`.

## Important rules for the environment files

1. **`backend/.env → SECRET_KEY` and `.env.local → JWT_SECRET` must be the same value.**
   FastAPI signs the login token; the Next.js middleware (`src/proxy.ts`) verifies it. If they differ, every page bounces back to `/login` even after a successful login.
2. **Do NOT set `NEXT_PUBLIC_API_URL` in `.env.local` anymore.** Browser API calls must stay
   relative (`/api/...`) so they go through the Next rewrite proxy and carry the httpOnly auth
   cookie. Direct calls to `http://localhost:8000` from the browser will get 401s.
   (`PYTHON_BACKEND_URL` stays — that's for server-side calls, which forward the cookie explicitly.)
3. Sharing one team database? Steps 2–3 only need to run **once per database**; steps 1, 4, 5 are per machine.

## Verify it worked

```bash
# no cookie → 401
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/api/patients          # 401

# login and call an endpoint per role
curl -s -c /tmp/jar -X POST http://localhost:8000/api/auth/login \
     -H 'Content-Type: application/json' -d '{"username":"doctor","password":"Doctor@123"}'
curl -s -o /dev/null -w '%{http_code}\n' -b /tmp/jar http://localhost:8000/api/diagnoses/completed   # 200
curl -s -o /dev/null -w '%{http_code}\n' -b /tmp/jar http://localhost:8000/api/analytics/dashboard   # 403 (admin only)
```

In the browser: log in as each demo user and confirm the sidebar only shows that role's sections, and that visiting a forbidden URL (e.g. `/doctor` as `reception`) redirects to the **Access denied** page.

## Troubleshooting

| Symptom | Cause → Fix |
|---|---|
| Login succeeds but every page redirects back to `/login` | `JWT_SECRET` ≠ backend `SECRET_KEY` → make them identical, restart `next dev` |
| Backend exits with `SECRET_KEY is not set` | Step 2 skipped → add it to `backend/.env` |
| `/api/visits/{id}` returns 500 `UndefinedColumn ... original_ai_plan` | Migration not run on this DB → run `scripts/setup_rbac.py` (or `scripts/migrate_revamp.py`) |
| Browser gets 401 on all API calls right after pulling | Old dev server still running without the new env/middleware → fully restart `npx next dev` |
| 401s when calling `http://localhost:8000` straight from browser code | Expected — use relative `/api/...` URLs (see rule 2 above) |
| `ModuleNotFoundError: jwt` / `bcrypt` on backend start | `pip install -r requirements.txt` inside `backend/venv` |
| Deactivated a user but they can still browse pages | Pages render until their next API call, which 401s and logs them out — deactivation is enforced per-request on the API |

## Where the access rules live (for future changes)

- **API authorization (source of truth):** ordered rules table `RBAC_RULES` in `backend/security.py`
- **Page routing:** `ROUTE_ROLES` in `src/lib/auth/roles.ts` (used by `src/proxy.ts`)
- **Sidebar visibility:** `roles` on each item in `src/components/layout/AppSidebar.tsx`

When you add a new backend route or page, update the matching table(s) — anything unlisted requires authentication but no specific role.
