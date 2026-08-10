# Distributor Management System

A web-based ERP for a Rajasthan steel & hardware trading business: master data (companies, categories, materials, suppliers, customers), stock, purchase and sales workflows, payments, dispatch, an append-only financial ledger, reports, role-based access control, and an audit log.

## Architecture

- **Backend**: Django 6 + Django REST Framework, PostgreSQL, JWT authentication (`djangorestframework-simplejwt`).
- **Frontend**: React 19 + Vite, plain CSS (no UI framework), `react-router-dom`, `axios`.
- **Roles**: Admin (Django superuser), Manager, Staff (Django Groups). See `backend/accounts/permissions.py` for the exact permission matrix enforced on every endpoint — the frontend's role-based navigation is UX only and never the actual security boundary.

## Prerequisites

- Python 3.13+
- Node.js 18+ and npm
- PostgreSQL running locally (or reachable), with a database and user already created

## Backend setup

```bash
cd backend
python -m pip install -r requirements.txt
```

Create `backend/.env` (never committed — already in `.gitignore`) with:

```
SECRET_KEY=<a long random string>
DEBUG=True
ALLOWED_HOSTS=

CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

DB_NAME=<your database name>
DB_USER=<your database user>
DB_PASSWORD=<your database password>
DB_HOST=localhost
DB_PORT=5432
```

Then:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py setup_roles      # creates the Manager/Staff Groups (idempotent)
python manage.py runserver        # http://localhost:8000
```

### Backend environment variables

| Variable | Purpose | Local default |
|---|---|---|
| `SECRET_KEY` | Django signing key; also the JWT signing key (no separate `SIGNING_KEY` is configured) | — required |
| `DEBUG` | Django debug mode | `False` if unset |
| `ALLOWED_HOSTS` | Comma-separated hostnames | empty |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins allowed to call the API | empty (no origin allowed) |
| `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD` | Production HTTPS hardening | all off/0 unless explicitly set — **do not enable locally** |
| `LOG_TO_FILE`, `LOG_FILE_PATH` | Optional rotating file logging alongside the console handler | `LOG_TO_FILE` off |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection | — required |

## Frontend setup

```bash
cd frontend
npm install
```

Create `frontend/.env` (never committed) with:

```
VITE_API_BASE_URL=http://localhost:8000/api
```

Then:

```bash
npm run dev        # http://localhost:5173
```

## Development workflow

Run both servers side by side (backend on 8000, frontend on 5173) and log in with a superuser created via `createsuperuser`, or a Manager/Staff account created afterward through the Users screen (Admin only) or `python manage.py shell`.

## Authentication

- `POST /api/auth/login/` → `{access, refresh, user}`. Access tokens last 15 minutes, refresh tokens 7 days, with rotation and blacklist-after-rotation enabled.
- `POST /api/auth/refresh/`, `POST /api/auth/logout/` (blacklists the refresh token), `GET /api/auth/me/`.
- The frontend stores both tokens in `localStorage` and transparently refreshes the access token on a 401 via an axios interceptor (`frontend/src/api/client.js`).

## Roles

| Role | Identity | Notes |
|---|---|---|
| Admin | `is_superuser=True` | Full access; only role that can delete master data, manage users, or read the audit log |
| Manager | member of the `Manager` Group | Business + financial operations: confirm/cancel Purchase & Sales, Payment, Ledger/Reports read |
| Staff | member of the `Staff` Group | Day-to-day operations: create/edit drafts, Dispatch, read-only Stock/Reports (stock report only) |

User management (`/api/users/`) can only create or modify Manager/Staff accounts — Admin accounts are managed outside the API via `createsuperuser` or Django Admin, by design.

## API base URL

Every backend endpoint is mounted under `/api/` (see `backend/config/urls.py`). The frontend never hardcodes this — it reads `VITE_API_BASE_URL` from its `.env`.

## Client setup requirements

To run this application at a client site you need: a PostgreSQL server, Python 3.13+, Node.js 18+ (only for building the frontend — the built static files can be served by anything afterward), and a `.env` file on each side populated per the tables above. See `DEPLOYMENT_CHECKLIST.md` for what else is required before a production deployment — production deployment is intentionally **not** covered by this document and has not been performed.
