# SpinePose — Project Documentation

Clinical-grade AI-powered posture and spine analysis platform for doctors and physiotherapists. Capture multi-view patient photos, run pose detection, compute posture metrics, and review annotated frames with a 3D digital twin.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Features](#2-features)
3. [Architecture](#3-architecture)
4. [Tech Stack](#4-tech-stack)
5. [Project Structure](#5-project-structure)
6. [Getting Started (Development)](#6-getting-started-development)
7. [Production Deployment](#7-production-deployment)
8. [Environment Variables](#8-environment-variables)
9. [Authentication & Roles](#9-authentication--roles)
10. [User Workflows](#10-user-workflows)
11. [REST API Reference](#11-rest-api-reference)
12. [Scan Processing Pipeline](#12-scan-processing-pipeline)
13. [AI Models & Metrics](#13-ai-models--metrics)
14. [Admin Panel](#14-admin-panel)
15. [Data Persistence & Backups](#15-data-persistence--backups)
16. [Development Guide](#16-development-guide)
17. [Testing](#17-testing)
18. [Troubleshooting](#18-troubleshooting)
19. [Security Notes](#19-security-notes)

---

## 1. Overview

SpinePose helps clinicians:

- Register and manage patients
- Capture standardized multi-view posture photos (front, side, back, Adams bend, optional face)
- Process images asynchronously through an AI pose pipeline
- Review computed posture metrics, risk levels, and annotated keypoint overlays
- Export reports and manage research datasets (admin)

The application is containerized with Docker Compose and consists of a **Vue 3 SPA**, a **FastAPI backend**, **Celery workers**, **PostgreSQL**, **Redis**, and **MinIO** object storage.

---

## 2. Features

### Doctor-facing

| Feature | Description |
|---------|-------------|
| Account management | Register, login, profile update, password change |
| Patient CRUD | Search, risk levels, scan history per patient |
| 5-step scan wizard | Environment setup → camera placement → patient prep → capture → analysis |
| Multi-view capture | Front, Side, Back, Upper body, Adams, optional Face (upload or camera) |
| Async scan processing | Celery worker with live progress messages |
| Results dashboard | Annotated frames, metric panels, digital twin keypoints |
| Detector settings | Per-doctor preference for `spinepose_v2` or `yolo_v8` |
| Reports | Scan history and export |

### Admin-facing

| Feature | Description |
|---------|-------------|
| Analytics dashboard | Doctor counts, scan activity, recent registrations |
| Doctor management | List, edit, activate/deactivate accounts |
| Research datasets | Upload images, manual label adjustment, export CSV |
| Dataset recompute | Re-run keypoint detection on research items |

### Platform

- JWT authentication with bcrypt password hashing
- Rate limiting (login: 5/min, global: 100/min)
- Structured logging (structlog)
- Scheduled PostgreSQL backups to MinIO
- Optional Flower monitoring for Celery
- Caddy or Apache reverse proxy for production

---

## 3. Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Browser   │────▶│ Reverse Proxy│────▶│  Frontend   │
│  (Vue SPA)  │     │ Apache/Caddy │     │ nginx :3000 │
└─────────────┘     └──────┬───────┘     └──────┬──────┘
                           │                     │
                           │              /api/* proxy
                           ▼                     ▼
                    ┌─────────────┐     ┌─────────────┐
                    │   Backend   │────▶│   MinIO     │
                    │ FastAPI     │     │  (frames)   │
                    │   :8000     │     └─────────────┘
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────────┐
        │ Postgres │ │  Redis   │ │ Celery Worker│
        │   :5432  │ │  :6379   │ │ (AI pipeline)│
        └──────────┘ └──────────┘ └──────────────┘
```

**Request flow (scan):**

1. Doctor uploads frames via frontend → backend stores in MinIO, creates scan record
2. Backend enqueues `process_scan` Celery task
3. Worker downloads frames, runs pose detection, 3D reconstruction, metrics, AI classifiers
4. Results saved to PostgreSQL; presigned MinIO URLs serve frame images to the browser

---

## 4. Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2 (async), Alembic, Pydantic v2 |
| Task queue | Celery 5 + Redis |
| Database | PostgreSQL 16 |
| Object storage | MinIO (S3-compatible, boto3) |
| Pose detection | MediaPipe Pose Landmarker, Ultralytics YOLOv8 Pose |
| AI classifiers | YOLO classification models (kyphosis, lordosis, scoliosis) |
| 3D / geometry | Open3D, NumPy, SciPy |
| Frontend | Vue 3, Vite, Pinia, Vue Router, Tailwind CSS, Axios |
| Reverse proxy | Caddy (dev/standalone) or Apache (shared server) |
| Containers | Docker Compose |

---

## 5. Project Structure

```
spineposeapp/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, health, startup hooks
│   │   ├── config.py            # Settings from environment
│   │   ├── database.py          # Async SQLAlchemy engine
│   │   ├── models/              # Doctor, Patient, Scan, DatasetItem, etc.
│   │   ├── routers/             # auth, patients, scans, doctors, admin
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── services/            # Business logic
│   │   ├── pipeline/            # AI inference, metrics, 3D reconstruction
│   │   ├── workers/             # Celery scan_tasks
│   │   └── utils/               # Auth, rate limit, logging, exceptions
│   ├── alembic/                 # Database migrations
│   ├── models/                  # YOLO weight files (.pt)
│   ├── tests/                   # pytest suite
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── views/               # Page components
│   │   ├── components/          # Reusable UI (MetricCard, overlays, etc.)
│   │   ├── stores/              # Pinia (auth, patients, scans)
│   │   ├── api/client.js        # Axios API client
│   │   └── router/index.js      # Routes + auth guards
│   ├── Dockerfile               # Multi-stage: Node build → nginx
│   └── nginx.conf
├── caddy/                       # Caddy reverse proxy config
├── scripts/                     # DB backup cron, Postgres init SQL
├── data/                        # Persistent volumes (gitignored)
│   ├── postgres/
│   ├── minio/
│   └── redis/
├── docker-compose.yml           # Development stack
├── docker-compose.override.yml  # Dev hot-reload overrides
├── docker-compose.prod.yml      # Production stack
├── .env.example
├── README.md
└── documentation.md
```

---

## 6. Getting Started (Development)

### Prerequisites

- Docker Desktop (8 GB+ RAM recommended)
- Ports: 80, 443, 3000, 5432, 6379, 8000, 9000, 9001, 5555

### Setup

```bash
cd spineposeapp
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD, JWT_SECRET, MINIO credentials
docker compose up -d
```

Migrations run automatically on backend startup (`alembic upgrade head`).

### URLs (development)

| Service | URL |
|---------|-----|
| Web app (Caddy) | http://localhost |
| Web app (direct) | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |
| MinIO console | http://localhost:9001 |
| Flower | http://localhost:5555 |

### First use

1. Open http://localhost/register
2. Create a doctor account (password: 8+ chars, 1 uppercase, 1 digit)
3. Add a patient → start a new scan → capture frames → view results

---

## 7. Production Deployment

### Docker Compose (production)

```bash
cd spineposeapp
cp .env.example .env
# Configure production secrets (see Environment Variables)
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### Production port map (default in `docker-compose.prod.yml`)

| Service | Host port | Container port |
|---------|-----------|----------------|
| Frontend | 3000 | 3000 |
| Backend API | 8001 | 8000 |
| PostgreSQL | 5433 | 5432 |
| Redis | 6380 | 6379 |
| MinIO API | 9002 | 9000 |
| MinIO Console | 9003 | 9001 |
| Flower (optional) | 5556 | 5555 |
| Caddy | 80, 443 | 80, 443 |

> Adjust ports if they conflict with other containers on the host.

### Apache reverse proxy (shared server)

When Apache already uses port 80/443, **stop Caddy** and proxy through Apache:

```bash
docker compose -f docker-compose.prod.yml stop caddy
```

Example HTTP vhost (`/etc/apache2/sites-available/spine-analysis.pak.net.pk.conf`):

```apache
<VirtualHost *:80>
    ServerName spine-analysis.pak.net.pk
    ServerAlias www.spine-analysis.pak.net.pk

    ProxyPreserveHost On
    ProxyRequests Off

    ProxyPass        /api/          http://127.0.0.1:8001/api/
    ProxyPassReverse /api/          http://127.0.0.1:8001/api/
    ProxyPass        /health        http://127.0.0.1:8001/health
    ProxyPassReverse /health        http://127.0.0.1:8001/health
    ProxyPass        /docs           http://127.0.0.1:8001/docs
    ProxyPassReverse /docs           http://127.0.0.1:8001/docs
    ProxyPass        /openapi.json   http://127.0.0.1:8001/openapi.json
    ProxyPassReverse /openapi.json   http://127.0.0.1:8001/openapi.json
    ProxyPass        /              http://127.0.0.1:3000/
    ProxyPassReverse /              http://127.0.0.1:3000/
</VirtualHost>
```

Enable SSL with certbot:

```bash
sudo certbot --apache -d spine-analysis.pak.net.pk -d www.spine-analysis.pak.net.pk
```

### Production `.env` essentials

```env
POSTGRES_PASSWORD=<alphanumeric only — no @ # : / ?>
JWT_SECRET=<64+ random characters>
MINIO_ROOT_USER=...
MINIO_ROOT_PASSWORD=...
MINIO_PUBLIC_ENDPOINT=spine-analysis.pak.net.pk:9002
CORS_ORIGINS=https://spine-analysis.pak.net.pk
CADDY_DOMAIN=          # leave empty when using Apache
ACME_EMAIL=            # leave empty when using Apache
LOG_LEVEL=INFO
```

**Important:** Do **not** set `DATABASE_URL` manually in `.env`. Docker Compose injects it from `POSTGRES_PASSWORD`. Special characters in the password break URL parsing.

---

## 8. Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `POSTGRES_PASSWORD` | Yes | PostgreSQL password (URL-safe characters only) |
| `JWT_SECRET` | Yes | JWT signing key (64+ chars in production) |
| `JWT_ALGORITHM` | No | Default `HS256` |
| `JWT_EXPIRE_MINUTES` | No | Default `1440` (24 h) |
| `MINIO_ROOT_USER` | Yes | MinIO access key |
| `MINIO_ROOT_PASSWORD` | Yes | MinIO secret key |
| `MINIO_BUCKET` | No | Default `spinepose-scans` |
| `MINIO_PUBLIC_ENDPOINT` | Yes (prod) | Host:port browsers use for presigned frame URLs |
| `MINIO_SECURE` | No | `true` if MinIO served over HTTPS |
| `CORS_ORIGINS` | Yes | Comma-separated allowed frontend origins |
| `DETECTOR_MODEL` | No | `spinepose_v2`, `yolo_v8`, or `yolo_custom` |
| `MODEL_WEIGHTS_PATH` | No | Custom model weights path |
| `KEYPOINT_CONFIDENCE_THRESHOLD` | No | Default `0.50` |
| `SCOLIOSIS_*` / `KEYPOINT_SCOLIOSIS_*` | No | Scoliosis screening thresholds |
| `LOG_LEVEL` | No | Default `INFO` |
| `CELERY_CONCURRENCY` | No | Worker processes (default `2`) |
| `CADDY_DOMAIN` / `ACME_EMAIL` | No | Caddy HTTPS (skip if using Apache) |
| `BACKUP_*` | No | DB backup schedule and retention |

Compose also sets (do not override in `.env`):

- `DATABASE_URL` — `postgresql+asyncpg://spinepose:${POSTGRES_PASSWORD}@postgres:5432/spinepose`
- `REDIS_URL` — `redis://redis:6379/0`
- `MINIO_ENDPOINT` — `minio:9000`

---

## 9. Authentication & Roles

### Registration

- Endpoint: `POST /api/v1/auth/register`
- Password rules: minimum 8 characters, at least one uppercase letter, one digit
- New accounts receive role **`doctor`** by default

### Login

- Endpoint: `POST /api/v1/auth/login` (OAuth2 form: `username` = email, `password`)
- Rate limited: **5 requests/minute**
- Returns JWT bearer token stored in browser `localStorage` as `sp_token`

### Roles

| Role | Access |
|------|--------|
| `doctor` | Dashboard, patients, scans, settings |
| `admin` | All doctor features + `/admin/*` routes and API |

### Creating the first admin

There is **no default admin account**. After registering:

```bash
docker compose -f docker-compose.prod.yml exec postgres psql -U spinepose -d spinepose -c \
  "UPDATE doctors SET role = 'admin' WHERE email = 'your@email.com';"
```

Log out and back in. Admins are redirected to `/admin/dashboard`.

---

## 10. User Workflows

### Doctor workflow

```
Register/Login → Dashboard → Add Patient → New Scan
    → Scan Setup (height, weight, camera params)
    → Capture Views (front, side, back, adams, optional face)
    → Processing (poll status)
    → Scan Results (metrics, overlays, digital twin)
    → Export Report
```

### Scan views

| View | Purpose |
|------|---------|
| Front | Pelvis, leg, shoulder symmetry |
| Side | Sagittal curves (kyphosis, lordosis), forward head |
| Back | Spine drift, scapula asymmetry |
| Upper body | Additional upper-body landmarks |
| Adams | Scoliosis screening (forward bend) |
| Face | Optional jaw/head metrics |

### Admin workflow

```
Login as admin → Admin Dashboard
    → Manage Doctors (list, edit, activate/deactivate)
    → Research Datasets (upload, label, export, recompute)
```

---

## 11. REST API Reference

Base URL: `/api/v1`  
Interactive docs: `/docs` (Swagger UI)

### Auth — `/api/v1/auth`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/register` | No | Register doctor |
| POST | `/login` | No | Login (form-encoded) |
| GET | `/me` | Yes | Current doctor profile |
| PUT | `/me` | Yes | Update profile |
| POST | `/change-password` | Yes | Change password |
| POST | `/forgot-password` | No | Request reset (logs token) |

### Patients — `/api/v1/patients`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List patients (search, pagination) |
| POST | `/` | Create patient |
| GET | `/{id}` | Patient detail |
| PUT | `/{id}` | Update patient |
| DELETE | `/{id}` | Delete patient |

### Scans — `/api/v1/scans`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/` | Create scan + upload frames (multipart) |
| GET | `/` | List scans |
| GET | `/{id}` | Scan detail with metrics |
| GET | `/{id}/status` | Processing status + progress |
| POST | `/{id}/recompute-keypoints` | Re-run keypoint detection |
| POST | `/{id}/reset-keypoints` | Reset to auto-detected keypoints |

### Doctor settings — `/api/v1`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/settings` | Detector settings |
| PUT | `/settings/detector` | Update preferred detector |

### Admin — `/api/v1/admin` (admin role required)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/analytics/summary` | Platform analytics |
| GET | `/doctors` | List all doctors |
| GET | `/doctors/{id}` | Doctor detail |
| PUT | `/doctors/{id}` | Update doctor |
| PATCH | `/doctors/{id}/status` | Activate/deactivate |
| GET/POST | `/datasets` | Research datasets CRUD |
| GET/POST | `/dataset-items` | Dataset image items |
| GET | `/dataset-items/export` | CSV export |

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | `{"status":"ok","detector_model":"..."}` |

---

## 12. Scan Processing Pipeline

Celery task: `process_scan(scan_id)` in `app/workers/scan_tasks.py`

```
1. Load scan record → status: processing
2. Download frames from MinIO (front, side, back, upper_body, adams, face)
3. Run pose detector (MediaPipe or YOLO per scan.detector_model)
4. Normalize keypoints → KeypointNormalizer
5. 3D reconstruction → Reconstructor3D
6. Spine curve fit → SpineCurveModel
7. Per-view metrics:
   - PelvisMetrics, LegMetrics, HeadShoulderMetrics, SpineBackMetrics
8. compute_all() → full metrics JSON with normal ranges
9. merge_ai_classifications():
   - Kyphosis classifier (side view)
   - Lordosis classifier (side view)
   - Scoliosis YOLO detector (back view)
   - Keypoint scoliosis screening (back + Adams)
10. derive_overall_risk() → normal | monitor | elevated
11. Upload digital twin keypoints JSON to MinIO
12. Save results → status: completed
```

On failure: status `failed`, error message stored, Celery retries up to 3 times.

---

## 13. AI Models & Metrics

### Pose detectors

| Model ID | Backend | Description |
|----------|---------|-------------|
| `spinepose_v2` | MediaPipe Pose Landmarker Heavy | Default; bundled in Docker image |
| `yolo_v8` | Ultralytics YOLOv8n-pose | Alternative detector |
| `yolo_custom` | Custom YOLO weights | Requires `MODEL_WEIGHTS_PATH` |

### AI classifiers (bundled weights in `backend/models/`)

| Model | View | Output |
|-------|------|--------|
| `yolo26n-cls-kyphosis.pt` | Side | Kyphosis classification |
| `yolo26n-cls-lordosis.pt` | Side | Lordosis classification |
| `yolo26n-scoliosis.pt` | Back | Scoliosis object detection |

### Metric categories

**Spinal curves**

- Thoracic kyphosis (°)
- Lumbar lordosis (°)

**Pelvis & lower body**

- Pelvic tilt sagittal (°)
- Pelvic obliquity (mm)
- Knee flexion left/right (°)
- HKA angle left/right (°)

**Head & shoulders**

- Forward head posture (mm)
- Shoulder height asymmetry (mm)
- Jaw deviation (mm)

**Spine & back**

- Spine drift (mm)
- Scapula asymmetry index
- Vertebral rotation index
- Keypoint scoliosis composite score

**AI classification**

- Kyphosis, lordosis, scoliosis screening results

Each metric includes `availability` status when landmarks or views are missing.

---

## 14. Admin Panel

Routes (frontend):

| Path | Description |
|------|-------------|
| `/admin/dashboard` | Analytics summary |
| `/admin/doctors` | Doctor list |
| `/admin/doctors/:id/edit` | Edit doctor |
| `/admin/research/dataset` | Research dataset list |
| `/admin/research/dataset/:id/adjust` | Manual keypoint labeling |

Access requires `role = admin` on the authenticated doctor account.

---

## 15. Data Persistence & Backups

### Host directories

```
spineposeapp/data/
├── postgres/    # Doctors, patients, scans, metrics
├── minio/       # Scan frame images, twin JSON, backups
└── redis/       # Celery broker AOF
```

- `docker compose up -d` preserves data across restarts
- **Do not** run `docker compose down -v` unless you intend to wipe Caddy certs and named volumes

### Automated backups

The `db_backup` service runs scheduled `pg_dump` uploads to MinIO bucket `backups`.

| Variable | Default |
|----------|---------|
| `BACKUP_INTERVAL_SECONDS` | 86400 (daily) |
| `BACKUP_RETENTION_DAYS` | 7 |
| `MINIO_BACKUP_BUCKET` | backups |

### Test database

pytest uses `spinepose_test` (created by `scripts/postgres/init-databases.sql`) — isolated from production data.

---

## 16. Development Guide

### Hot reload (development only)

`docker-compose.override.yml` enables:

- Backend volume mount `./backend:/app`
- uvicorn `--reload`
- `LOG_LEVEL=DEBUG`

### Rebuild after changes

```bash
# Backend / worker
docker compose build backend celery_worker
docker compose up -d backend celery_worker

# Frontend
docker compose build frontend
docker compose up -d frontend
```

### Migrations

```bash
# Create migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Apply
docker compose exec backend alembic upgrade head
```

### Logs

```bash
docker compose logs -f backend
docker compose logs -f celery_worker
```

---

## 17. Testing

```bash
docker compose exec backend pytest tests/ -v
```

Test coverage includes: auth, patients, scans, pipeline, dashboard, admin, dataset, kyphosis/scoliosis classifiers.

Tests run against `spinepose_test`, not the production `spinepose` database.

---

## 18. Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Backend unhealthy: `...@postgres` hostname | `@` in `POSTGRES_PASSWORD` | Use alphanumeric password; remove manual `DATABASE_URL` from `.env` |
| Backend unhealthy: password authentication failed | Postgres data initialized with different password | Wipe `./data/postgres` or `ALTER USER` to match `.env` |
| Caddy: port 80 already in use | Apache owns port 80 | `docker compose stop caddy`; use Apache vhost |
| Scan images not loading | Wrong `MINIO_PUBLIC_ENDPOINT` | Set to public host:port (e.g. `domain:9002`) |
| 502 on API after rebuild | Frontend nginx stale upstream | `docker compose up -d frontend` |
| No keypoints on results | Old scan or poor image quality | Submit new scan with clear full-body visibility |
| Admin pages 403 | Account role is `doctor` | `UPDATE doctors SET role='admin'` in Postgres |
| Celery tasks not running | Worker down or Redis unreachable | Check `celery_worker` and `redis` containers |

### Diagnostic commands

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs backend --tail 50
docker compose -f docker-compose.prod.yml config | grep DATABASE_URL
curl -f http://localhost:8001/health
```

---

## 19. Security Notes

- Never commit `.env` to version control
- Use 64+ character `JWT_SECRET` in production
- Use URL-safe passwords for PostgreSQL (no `@`, `#`, `:`, `/`, `?`)
- Restrict host ports at firewall: expose only 80/443 (Apache) and 9002 (MinIO frames if needed)
- Lock down 5433, 6380, 8001, 9003, 5556 to admin IPs
- Login rate limited to 5/minute
- MinIO credentials must match between `.env` and initialized MinIO data
- HTTPS via certbot/Apache or Caddy + Let's Encrypt

---

## Related Documents

- [README.md](README.md) — Quick start
- [.env.example](.env.example) — All environment variables
- [../decs/SpinePose_Dev_Prompt.md](../decs/SpinePose_Dev_Prompt.md) — Design specification

---

## License

Capstone / educational project. See repository root for license terms.
