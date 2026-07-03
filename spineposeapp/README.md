# SpinePose

Clinical-grade AI-powered posture and spine analysis platform for doctors and physiotherapists. Capture multi-view patient photos, run pose detection, compute posture metrics, and review annotated frames with a 3D digital twin.

## Features

- **Doctor accounts** — registration, login, profile management
- **Patient management** — CRUD, search, risk levels, scan history
- **5-step scan wizard** — environment setup, camera placement, patient prep, capture, analysis
- **Multi-view capture** — Front, Side, Back, Adams (+ optional Face) via file upload or live camera
- **AI pose pipeline** — MediaPipe Pose Landmarker with spine landmark mapping
- **Posture metrics** — kyphosis, lordosis, pelvic tilt, forward head posture, and more
- **Results dashboard** — annotated frames, digital twin viewer, metric panels
- **Async processing** — Celery workers with live progress updates
- **Object storage** — scan frames and assets in MinIO (S3-compatible)
- **Production hardening** — rate limiting, structured logging, Caddy reverse proxy, DB backups, Flower monitoring

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2 (async), Alembic |
| Task queue | Celery + Redis |
| Database | PostgreSQL 16 |
| Storage | MinIO |
| Pose detection | MediaPipe Pose Landmarker |
| Frontend | Vue 3, Vite, Pinia, Vue Router, Tailwind CSS |
| Reverse proxy | Caddy |
| Containers | Docker Compose |

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows, macOS, or Linux)
- 8 GB+ RAM recommended (MediaPipe + Open3D in the backend image)
- Ports available: **80**, **443**, **3000**, **5432**, **6379**, **8000**, **9000**, **9001**, **5555**

## Quick Start

### 1. Configure environment

```powershell
cd spineposeapp
copy .env.example .env
```

Edit `.env` and set at minimum:

- `POSTGRES_PASSWORD` — database password
- `JWT_SECRET` — long random string (64+ characters for production)
- `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` — object storage credentials

### 2. Start the stack

```powershell
docker compose up -d
```

First startup builds images and runs database migrations automatically.

### 3. Open the app

| Service | URL |
|---------|-----|
| **Web app (Caddy)** | http://localhost |
| **Web app (direct)** | http://localhost:3000 |
| **API docs** | http://localhost:8000/docs |
| **API health** | http://localhost:8000/health |
| **MinIO console** | http://localhost:9001 |
| **Flower (Celery)** | http://localhost:5555 |

### 4. Register and scan

1. Go to **Register** and create a doctor account (password needs 8+ chars, one uppercase, one digit).
2. Add a patient from **Patients**.
3. Start **New Scan** → select patient → complete the wizard → capture frames.
4. Wait for processing, then view **Scan Results** with metrics and keypoint overlays.

## Docker Services

| Service | Purpose |
|---------|---------|
| `postgres` | Primary database |
| `redis` | Celery broker and cache |
| `minio` | Scan frame and asset storage |
| `backend` | FastAPI REST API |
| `celery_worker` | Scan processing pipeline |
| `flower` | Celery task monitor |
| `frontend` | Vue SPA (nginx) |
| `caddy` | Reverse proxy (ports 80/443) |
| `db_backup` | Scheduled Postgres backups to MinIO |

## Data Persistence

Application data is stored on the host under `./data/`:

```
data/
  postgres/   # Patients, doctors, scans, metrics
  minio/      # Uploaded scan images
  redis/      # Redis AOF persistence
```

- **`docker compose build`** and **`docker compose up -d`** keep this data.
- **Do not run** `docker compose down -v` unless you intend to wipe Caddy certificates and other named volumes.
- Tests use a separate database (`spinepose_test`) so running pytest does not erase production data.

## Environment Variables

See [`.env.example`](.env.example) for the full list. Key options:

| Variable | Description |
|----------|-------------|
| `DETECTOR_MODEL` | `spinepose_v2`, `yolo_v8`, or `yolo_custom` |
| `MODEL_WEIGHTS_PATH` | Optional custom model weights path |
| `KEYPOINT_CONFIDENCE_THRESHOLD` | Minimum landmark confidence (default `0.50`) |
| `MINIO_PUBLIC_ENDPOINT` | Browser-reachable MinIO host (default `localhost:9000`) |
| `CORS_ORIGINS` | Allowed frontend origins |
| `CADDY_DOMAIN` / `ACME_EMAIL` | Enable HTTPS with Let's Encrypt in production |

## Development

### Rebuild after code changes

```powershell
# Backend / worker
docker compose build backend celery_worker
docker compose up -d backend celery_worker

# Frontend
docker compose build frontend
docker compose up -d frontend
```

The backend mounts `./backend` into the container for live code edits; restart the backend container after Python changes if needed.

### Run database migrations

```powershell
docker compose exec backend alembic upgrade head
```

### View logs

```powershell
docker compose logs -f backend
docker compose logs -f celery_worker
```

## Testing

```powershell
docker compose exec backend pytest tests/ -v
```

50 tests cover auth, patients, scans, pipeline, dashboard, and settings. Tests run against `spinepose_test`, not the production `spinepose` database.

## Scan Pipeline

1. Frames uploaded to MinIO (front, side, back, adams, optional face)
2. Celery worker downloads frames and runs **MediaPipe Pose Landmarker**
3. Landmarks normalized → 3D reconstruction → spine curve fit → metric computation
4. Results stored in PostgreSQL; `frame_landmarks` saved per view for UI overlays

Re-process an old scan by submitting a **new scan** — scans processed before the MediaPipe integration may lack per-view keypoints.

## Project Structure

```
spineposeapp/
├── backend/           # FastAPI app, pipeline, Celery tasks, tests
│   ├── app/
│   │   ├── pipeline/  # Pose inference, metrics, 3D reconstruction
│   │   ├── routers/   # API routes
│   │   ├── services/  # Business logic
│   │   └── workers/   # Celery scan tasks
│   └── tests/
├── frontend/          # Vue 3 SPA
├── caddy/             # Reverse proxy config
├── scripts/           # DB backup scripts, Postgres init
├── data/              # Persistent volumes (gitignored)
├── docker-compose.yml
└── .env.example
```

Design and API specifications: [`../decs/SpinePose_Dev_Prompt.md`](../decs/SpinePose_Dev_Prompt.md)

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Registration / API fails with 502 | Restart frontend after backend rebuild (`docker compose up -d frontend`) |
| Scan images not loading | Ensure `MINIO_PUBLIC_ENDPOINT=localhost:9000` in `.env` |
| No keypoints on results | Submit a new scan with a clearly visible person in frame |
| Port already in use | Stop other stacks: `docker compose -p spineposeapp down` or free the port |
| Postgres won't start | Delete corrupted `./data/postgres` only if you accept data loss, then `docker compose up -d` |

## Production Notes

- Set strong secrets in `.env` (never commit `.env`)
- Configure `CADDY_DOMAIN` and `ACME_EMAIL` for HTTPS
- Adjust `BACKUP_RETENTION_DAYS` and `BACKUP_INTERVAL_SECONDS` for your RPO/RTO
- Pin image tags and review rate limits in `app/utils/rate_limit.py`

## License

Capstone / educational project — see repository root for license terms if applicable.
