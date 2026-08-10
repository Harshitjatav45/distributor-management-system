# Production Deployment Checklist

**Status: preparation only. No production deployment has been performed as part of this work.** Every item below that depends on infrastructure this environment does not have access to is marked **DEFERRED** — it must be completed by whoever holds that infrastructure before going live.

## Domain & DNS — DEFERRED
- Register/confirm the production domain.
- Point DNS (A/CNAME records) at the production server or load balancer.

## HTTPS — DEFERRED
- Obtain a TLS certificate (e.g. Let's Encrypt via the hosting provider, or a purchased cert).
- Once HTTPS is confirmed working end-to-end at the production domain, set in the production `.env`:
  - `SECURE_SSL_REDIRECT=True`
  - `SESSION_COOKIE_SECURE=True`
  - `CSRF_COOKIE_SECURE=True`
  - `SECURE_HSTS_SECONDS=31536000` (start lower, e.g. `300`, and raise it once confirmed safe — HSTS cannot be easily undone for clients that already received it)
  - `SECURE_HSTS_INCLUDE_SUBDOMAINS=True` only if every subdomain also serves HTTPS
  - Do **not** enable any of the above until HTTPS is verified working — enabling `SECURE_SSL_REDIRECT` before HTTPS works will make the site completely unreachable.

## Production server — DEFERRED
- Choose hosting (VM, container platform, PaaS).
- Run Django via a production WSGI/ASGI server (e.g. gunicorn/uvicorn) behind a reverse proxy (nginx) — never `manage.py runserver` in production.
- Serve the frontend's built static output (`npm run build` → `frontend/dist/`) via the same reverse proxy or a static host/CDN.

## Production environment variables — DEFERRED (values), READY (mechanism)
The app already reads every sensitive/environment-specific value from `.env` (see `backend/config/settings.py`) — nothing is hardcoded. What's needed at deploy time:
- A **new**, production-only `SECRET_KEY` (generate fresh — never reuse the development one).
- `DEBUG=False`.
- `ALLOWED_HOSTS` set to the exact production domain(s).
- `CORS_ALLOWED_ORIGINS` set to the exact production frontend origin(s) — never a wildcard.
- Production PostgreSQL credentials (see below).
- `frontend/.env` → `VITE_API_BASE_URL` set to the production API URL, then rebuild (`npm run build`).

## Production SECRET_KEY — DEFERRED
- Rotate to a new value generated on/for the production environment. Because `SIMPLE_JWT` has no separate `SIGNING_KEY`, rotating `SECRET_KEY` invalidates every outstanding JWT — rotate during a maintenance window, not silently.

## PostgreSQL credentials — DEFERRED
- Create a dedicated production database and a least-privilege database user (not `postgres`).
- Set a strong, unique password; store it only in the production `.env` / secrets manager, never in git.

## PostgreSQL SSL — DEFERRED
- If the database is not on the same trusted network as the app server, require SSL on the connection (`sslmode=require` or stricter via `psycopg` connection options) and confirm the provider's CA if using `verify-full`.

## CORS (production) — READY (mechanism), DEFERRED (values)
- Already environment-driven and never wildcards (`CORS_ALLOW_ALL_ORIGINS = False` is hardcoded, by design). Just set `CORS_ALLOWED_ORIGINS` to the real frontend origin(s) at deploy time.

## ALLOWED_HOSTS — READY (mechanism), DEFERRED (values)
- Already environment-driven. Set to the exact production hostname(s); never leave empty or wildcarded in production.

## Backups — DEFERRED
- Set up scheduled PostgreSQL backups (e.g. `pg_dump` on a cron, or the hosting provider's managed backup feature) with a tested restore procedure.
- Decide a retention policy appropriate for financial records (Ledger/Payment/AuditLog).

## Monitoring — DEFERRED
- Set up uptime monitoring for the API and frontend.
- Consider forwarding Django's `LOG_TO_FILE`/console output (see `LOGGING` in `settings.py`) to a log aggregator if the hosting platform doesn't already capture stdout.

## Email provider — NOT IMPLEMENTED, NOT REQUIRED BY CURRENT SCOPE
- No email-sending feature exists in this application (no self-service password reset, no notifications). If one is added later, an SMTP/API provider will need to be chosen and configured then.

## Static/media files — DEFERRED
- Django has no user-uploaded media in this project (no `ImageField`/`FileField` in any model), so no media storage decision is needed today.
- `STATIC_URL` is set; if Django Admin's static assets need collecting for production, run `python manage.py collectstatic` and serve the output via the reverse proxy/CDN.

## Frontend build — READY
- `cd frontend && npm run build` produces static output in `frontend/dist/`. Verified to build cleanly with the current codebase (see final QA section of the project report).

## Backend process — DEFERRED
- Decide the process manager (systemd unit, container restart policy, PaaS process type) that keeps the WSGI/ASGI server running and restarts it on failure/deploy.

## Database migration (production) — READY (mechanism), DEFERRED (execution)
- Standard flow: `python manage.py migrate` against the production database as part of each deploy. No destructive migrations are pending — `makemigrations --check` reports no changes needed beyond what's already in the repo.

---

**Summary**: the application code is deployment-ready in the sense that nothing is hardcoded and every environment-specific value is externalized to `.env`. Everything marked DEFERRED above requires infrastructure access (a domain, a production server, a production database, a hosting/monitoring account) that this work session does not have and was explicitly told not to acquire or simulate.
