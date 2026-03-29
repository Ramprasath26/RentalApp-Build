# RentalApp-Build

A production-ready Django REST API microservice for managing rental properties, tenants, transactions, and utility records. Designed for deployment on Kubernetes (AKS / GKE).

## Features

- **Multi-property management** — residential and commercial properties, units, and tenants
- **Financial ledger** — rent ledger, deposit ledger, transactions with receipt generation
- **Utility tracking** — metered/fixed/shared billing for electricity, water, gas
- **Document management** — file upload for agreements, Aadhar, PAN, GST, receipts, invoices
- **Role-based access** — Owner, Manager, Staff roles
- **Activity audit log** — every create/update/delete/login action is recorded
- **Token authentication** — DRF token auth with rate limiting
- **Health probe** — `GET /healthz` for Kubernetes liveness/readiness checks

## Quick Start (local)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment (copy and edit)
cp .env.example .env

# 3. Run migrations
cd backend && python manage.py migrate

# 4. Create superuser
python manage.py createsuperuser

# 5. Run dev server
python manage.py runserver
```

## Docker

```bash
# Build
docker build -t rentalapp-api:latest .

# Run (SQLite, no migrations)
docker run -p 8000:8000 \
  -e SECRET_KEY=your-secret \
  -e DEBUG=false \
  rentalapp-api:latest

# Run (Postgres, with auto-migrate)
docker run -p 8000:8000 \
  -e SECRET_KEY=your-secret \
  -e DEBUG=false \
  -e DB_NAME=rentaldb \
  -e DB_USER=postgres \
  -e DB_PASSWORD=secret \
  -e DB_HOST=db.example.com \
  -e RUN_MIGRATIONS=true \
  rentalapp-api:latest
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | — | **Required in prod** — Django secret key |
| `DEBUG` | `False` | Enable debug mode |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` | Comma-separated allowed hostnames |
| `DB_NAME` | — | Postgres database name (omit to use SQLite) |
| `DB_USER` | `postgres` | Postgres user |
| `DB_PASSWORD` | — | Postgres password |
| `DB_HOST` | `localhost` | Postgres host |
| `DB_PORT` | `5432` | Postgres port |
| `DB_SSLMODE` | `require` | Postgres SSL mode (`require`, `disable`) |
| `RUN_MIGRATIONS` | `false` | Run `migrate` on container start |
| `CORS_ALLOWED_ORIGINS` | — | Comma-separated CORS origins (prod) |
| `GUNICORN_WORKERS` | `4` | Number of Gunicorn worker processes |
| `GUNICORN_TIMEOUT` | `120` | Gunicorn worker timeout (seconds) |
| `PORT` | `8000` | Listening port |
| `SECURE_SSL_REDIRECT` | `False` | Redirect HTTP→HTTPS |
| `SECURE_HSTS_SECONDS` | `0` | HSTS max-age in seconds |

## API Endpoints

| Prefix | Description |
|---|---|
| `GET /healthz` | Kubernetes liveness / readiness probe — unauthenticated |
| `/api/v1/` | Auth, users, tenants, transactions, documents (common module) |
| `/api/v1/residential/` | Residential property & unit management |
| `/api/v1/commercial/` | Commercial property & tenant management |
| `/api/v1/owner/` | Owner profiles and summaries |
| `/admin/` | Django back-office admin UI |

All endpoints except `/healthz` and the login endpoint require `Authorization: Token <token>`.

## Kubernetes Probes

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8000
  initialDelaySeconds: 15
  periodSeconds: 20

readinessProbe:
  httpGet:
    path: /healthz
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
```

### Migration init-container pattern

```yaml
initContainers:
  - name: migrate
    image: rentalapp-api:latest
    command: ["python", "manage.py", "migrate", "--noinput"]
    env:
      # same SECRET_KEY + DB_* env vars as the main container
```

## Security Highlights

- `SECRET_KEY` is **required** at startup when `DEBUG=False`
- PostgreSQL connections use SSL (`DB_SSLMODE=require`) by default
- CORS origins are entirely env-driven in production — no hardcoded localhost
- Security headers: `X-Frame-Options: DENY`, `Content-Type-Options: nosniff`, configurable HSTS
- Session and CSRF cookies are `Secure` in production
- Rate limiting: anonymous 60/min · authenticated 1000/day · auth endpoints 5/min
- Container runs as non-root `appuser`

## Project Structure

```
RentalApp-Build/
├── backend/
│   ├── manage.py
│   ├── config/
│   │   ├── settings.py        # All configuration via env vars
│   │   ├── urls.py            # URL routing incl. /healthz
│   │   ├── health.py          # Lightweight health probe view
│   │   ├── wsgi.py
│   │   └── asgi.py
│   └── apps/
│       ├── common/            # Auth, users, tenants, transactions, documents
│       ├── residential/       # Residential property management
│       ├── commercial/        # Commercial property management
│       └── owner/             # Owner management
├── Dockerfile                 # Multi-stage python:3.12-alpine build
├── .dockerignore
├── entrypoint.sh              # collectstatic → optional migrate → gunicorn
├── requirements.txt           # Runtime Python dependencies
├── sonar-project.properties   # SonarQube/SonarCloud config
└── logo.png

```

## License

Private — all rights reserved.
