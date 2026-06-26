# SpinePose — Full-Stack Development Prompt
# For use with Claude Code or Cursor

---

## How to Use This Prompt

Paste this entire file as your opening prompt in Claude Code or Cursor.
Work through the six stages in order. Each stage has explicit acceptance criteria —
do not proceed until they all pass.

This prompt is the technical implementation specification for the SpinePose UI
designed in Google Stitch. Every page name, route, component name, and color token
in this document maps directly to the Stitch design. When in doubt, the Stitch
design is the source of truth for layout and visual decisions; this document is
the source of truth for data, API contracts, and business logic.

---

## Project Summary

SpinePose is a clinical-grade AI-powered posture and spine analysis platform.
Doctors and physiotherapists use it to:

- Register and manage their account and clinic profile
- Create and manage patient records
- Initiate posture scan sessions using RGB-D depth cameras
- Process frames through an AI keypoint detection pipeline to compute 12+ spine
  and posture metrics (kyphosis, lordosis, pelvic tilt, forward head posture, etc.)
- View 3D digital twin visualizations and longitudinal scan history
- Export PDF reports

The detection model (SpinePose v2 or YOLO) is controlled by a single environment
variable. There are no phases, no code branches, and no feature flags — just one
codebase that loads whichever model is configured at startup.

---

## Technology Stack

| Layer              | Choice                              | Reason                                              |
|--------------------|-------------------------------------|-----------------------------------------------------|
| Runtime            | Python 3.12                         | Required by SpinePose v2 and Open3D environments    |
| API framework      | FastAPI                             | Async, OpenAPI docs, same language as AI pipeline   |
| Task queue         | Celery + Redis                      | Async scan processing without blocking the API      |
| Database           | PostgreSQL 16                       | Relational audit trail; JSONB for metric blobs      |
| ORM + migrations   | SQLAlchemy 2.x (async) + Alembic    | Async queries, versioned schema migrations          |
| Auth               | JWT (python-jose) + bcrypt          | Stateless, standard for SPAs                        |
| Frontend           | Vue 3 + Vite + Pinia + Vue Router   | Integrated from Stitch-generated HTML (Stage 4)     |
| Object storage     | MinIO (S3-compatible, self-hosted)  | Raw RGBD frame and digital twin asset storage       |
| Cache / broker     | Redis 7                             | Celery broker + session cache + status polling      |
| Containers         | Docker Compose                      | Single-command local stack                          |

---

## Design System Alignment

The frontend must implement these tokens exactly as specified in the Stitch brief.
They are listed here so the backend, error messages, and API responses are named
consistently with the UI.

```
Base background:     #0A0A0A
Surface (cards):     #1A1A1A
Raised (inputs):     #2A2A2A
Accent yellow:       #E8D600   ← primary CTA, active nav, abnormal metric values
Accent yellow light: #F5EE80
Accent yellow faint: #FDFBE6
Primary text:        #FFFFFF
Secondary text:      rgba(255,255,255,0.65)
Tertiary text:       rgba(255,255,255,0.35)
Border subtle:       rgba(255,255,255,0.06)
Border raised:       rgba(255,255,255,0.10)
Status red:          #DC2626   ← errors, high-risk flags
Status green:        #16A34A   ← success, normal-range metrics
Status amber:        #D97706   ← warnings, medium-risk
Status blue:         #2563EB   ← informational, YOLO model badge

Fonts: Inter (UI), JetBrains Mono (metric values, IDs, monospace numbers)
```

---

## Repository Structure

Create this exact layout before writing any code.

```
spineposeapp/
├── docker-compose.yml
├── docker-compose.override.yml       # dev: hot reload, debug ports
├── .env.example
├── .gitignore
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   │
│   └── app/
│       ├── main.py                   # FastAPI app factory
│       ├── config.py                 # Settings via pydantic-settings
│       ├── database.py               # Async SQLAlchemy engine + session
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── doctor.py
│       │   ├── patient.py
│       │   └── scan.py
│       │
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── doctor.py
│       │   ├── patient.py
│       │   └── scan.py
│       │
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── doctors.py
│       │   ├── patients.py
│       │   └── scans.py
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── auth_service.py
│       │   ├── patient_service.py
│       │   ├── scan_service.py
│       │   └── storage_service.py    # MinIO wrapper
│       │
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── base.py               # DetectorBase abstract interface
│       │   ├── loader.py             # reads DETECTOR_MODEL env var, returns detector
│       │   ├── spinepose_detector.py # SpinePose v2 implementation
│       │   ├── yolo_detector.py      # YOLO implementation
│       │   ├── keypoint_normalizer.py
│       │   ├── reconstructor_3d.py
│       │   ├── spine_curve_model.py
│       │   └── metric_engine.py
│       │
│       ├── workers/
│       │   ├── __init__.py
│       │   └── scan_tasks.py
│       │
│       └── utils/
│           ├── __init__.py
│           ├── dependencies.py       # get_db, get_current_doctor
│           └── exceptions.py
│
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.js
        ├── App.vue
        ├── router/
        │   └── index.js
        ├── stores/
        │   ├── auth.js
        │   ├── patients.js
        │   └── scans.js
        ├── api/
        │   └── client.js
        ├── components/               # Reusable components from Stitch brief
        │   ├── MetricCard.vue
        │   ├── PatientRow.vue
        │   ├── ScanStatusBadge.vue
        │   ├── RiskLevelBadge.vue
        │   ├── QualityBadge.vue
        │   ├── RangeBar.vue
        │   ├── DigitalTwinViewer.vue
        │   └── ScanMetricsPanel.vue
        └── views/                    # One view per Stitch page
            ├── LoginView.vue          # Page 1
            ├── RegisterView.vue       # Page 2
            ├── ForgotPasswordView.vue # Page 3
            ├── DashboardView.vue      # Page 4
            ├── PatientsView.vue       # Page 5
            ├── PatientFormView.vue    # Page 6
            ├── PatientProfileView.vue # Page 7
            ├── ScanSetupView.vue      # Page 8
            ├── ScanCaptureView.vue    # Page 9
            ├── ScanProcessingView.vue # Page 10
            ├── ScanResultsView.vue    # Page 11
            ├── ReportExportView.vue   # Page 12
            ├── ScanHistoryView.vue    # Page 13
            ├── ReportsLibraryView.vue # Page 14
            ├── SettingsView.vue       # Page 15
            └── HelpView.vue           # Page 16
```

---

## Stage 1 — Docker Compose + Infrastructure

**Goal:** `docker compose up` starts the entire stack. All health checks pass.
No application code is required at this stage.

### docker-compose.yml

```yaml
services:

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: spinepose
      POSTGRES_USER: spinepose
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U spinepose"]
      interval: 5s
      timeout: 5s
      retries: 10
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10
    ports:
      - "6379:6379"

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    env_file: .env
    environment:
      DATABASE_URL: postgresql+asyncpg://spinepose:${POSTGRES_PASSWORD}@postgres:5432/spinepose
      REDIS_URL: redis://redis:6379/0
      MINIO_ENDPOINT: minio:9000
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_started
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.workers.scan_tasks worker --loglevel=info --concurrency=2
    env_file: .env
    environment:
      DATABASE_URL: postgresql+asyncpg://spinepose:${POSTGRES_PASSWORD}@postgres:5432/spinepose
      REDIS_URL: redis://redis:6379/0
      MINIO_ENDPOINT: minio:9000
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
  minio_data:
```

### .env.example

```env
# ── Infrastructure ────────────────────────────────────────────────
POSTGRES_PASSWORD=changeme_dev
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
MINIO_BUCKET=spinepose-scans
MINIO_SECURE=false

# ── Auth ──────────────────────────────────────────────────────────
JWT_SECRET=replace_with_64_random_chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# ── CORS ──────────────────────────────────────────────────────────
CORS_ORIGINS=http://localhost:3000

# ── AI Detection Model ────────────────────────────────────────────
# Set to: spinepose_v2  OR  yolo_v8  OR  yolo_custom
DETECTOR_MODEL=spinepose_v2

# Path to model weights file — required for whichever model is active
# SpinePose:  /path/to/spinepose_v2_weights.pth
# YOLO:       /path/to/yolo_pose.pt
MODEL_WEIGHTS_PATH=

# ── Quality Gate ──────────────────────────────────────────────────
KEYPOINT_CONFIDENCE_THRESHOLD=0.50

# ── Logging ───────────────────────────────────────────────────────
LOG_LEVEL=INFO
```

### backend/Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx libglib2.0-0 libgomp1 git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
```

### backend/pyproject.toml

```toml
[project]
name = "spinepose-backend"
version = "1.0.0"
requires-python = ">=3.12"

dependencies = [
  "fastapi==0.115.0",
  "uvicorn[standard]==0.30.6",
  "sqlalchemy[asyncio]==2.0.35",
  "asyncpg==0.29.0",
  "alembic==1.13.3",
  "pydantic==2.9.2",
  "pydantic-settings==2.5.2",
  "python-jose[cryptography]==3.3.0",
  "passlib[bcrypt]==1.7.4",
  "python-multipart==0.0.12",
  "celery[redis]==5.4.0",
  "redis==5.1.0",
  "boto3==1.35.0",
  "numpy==2.1.1",
  "opencv-python-headless==4.10.0.84",
  "open3d==0.18.0",
  "scipy==1.14.1",
  "pillow==10.4.0",
  "httpx==0.27.2",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio", "httpx"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### frontend/Dockerfile

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
```

### frontend/nginx.conf

```nginx
server {
    listen 3000;
    root /usr/share/nginx/html;
    index index.html;

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

**Stage 1 acceptance criteria:**
- `docker compose up --build` starts all 5 services without errors
- `curl http://localhost:8000/health` → `{"status":"ok","detector_model":"spinepose_v2"}`
  (the health endpoint must read and return `DETECTOR_MODEL` from env)
- MinIO console accessible at `http://localhost:9001`
- PostgreSQL accessible at `localhost:5432`

---

## Stage 2 — Database Models + Migrations

**Goal:** All tables exist in PostgreSQL with correct constraints, indexes, and
foreign keys. Alembic migrations are the single source of schema truth.

### app/models/doctor.py

```python
# Table: doctors
# Columns:
#   id              UUID, primary key, default gen_random_uuid()
#   email           VARCHAR(255), unique, not null, indexed
#   hashed_password VARCHAR(255), not null
#   first_name      VARCHAR(100), not null
#   last_name       VARCHAR(100), not null
#   specialty       VARCHAR(100), nullable
#   license_number  VARCHAR(100), nullable
#   clinic_name     VARCHAR(200), nullable
#   country         VARCHAR(100), nullable
#   city            VARCHAR(100), nullable
#   bio             TEXT, nullable
#   avatar_url      VARCHAR(500), nullable
#   is_active       BOOLEAN, default True, not null
#   created_at      TIMESTAMPTZ, default now(), not null
#   updated_at      TIMESTAMPTZ, default now(), not null (auto-update on write)
#
# Relationships:
#   patients → one-to-many (back_populates="doctor")
```

### app/models/patient.py

```python
# Table: patients
# Columns:
#   id                    UUID, primary key
#   doctor_id             UUID, FK → doctors.id, ON DELETE CASCADE, not null, indexed
#   first_name            VARCHAR(100), not null
#   last_name             VARCHAR(100), not null
#   date_of_birth         DATE, not null
#   gender                ENUM('male','female','other'), not null
#   height_cm             FLOAT, not null
#   weight_kg             FLOAT, not null
#   medical_record_number VARCHAR(100), nullable
#   phone                 VARCHAR(50), nullable
#   email                 VARCHAR(255), nullable
#   emergency_contact_name  VARCHAR(200), nullable
#   emergency_contact_phone VARCHAR(50), nullable
#   referring_physician   VARCHAR(200), nullable
#   primary_diagnosis     VARCHAR(500), nullable
#   medical_notes         TEXT, nullable
#   avatar_url            VARCHAR(500), nullable
#   risk_level            ENUM('normal','monitor','elevated'), default 'normal'
#                         — updated by the metric engine after each scan
#   is_active             BOOLEAN, default True, not null
#   created_at            TIMESTAMPTZ, default now(), not null
#   updated_at            TIMESTAMPTZ, default now(), not null
#
# Constraints:
#   UNIQUE (doctor_id, medical_record_number) — MRN unique per doctor, not globally
#
# Relationships:
#   doctor → many-to-one
#   scans  → one-to-many (back_populates="patient")
```

### app/models/scan.py

```python
# Table: scans
# Columns:
#   id                    UUID, primary key
#   patient_id            UUID, FK → patients.id, ON DELETE CASCADE, not null, indexed
#   doctor_id             UUID, FK → doctors.id, ON DELETE SET NULL, nullable, indexed
#                         (denormalised for query performance — always set at creation)
#   status                ENUM('pending','processing','completed','failed'), not null, indexed
#   capture_device        VARCHAR(200), nullable
#   camera_height_cm      FLOAT, nullable
#   camera_distance_cm    FLOAT, nullable
#   patient_height_cm     FLOAT, not null   — calibration value used for this scan
#   patient_weight_kg     FLOAT, not null
#   detector_model        VARCHAR(50), not null
#                         — value of DETECTOR_MODEL at the time the scan was created
#                         — stored so the scan record is self-describing
#   raw_frames_prefix     VARCHAR(500), nullable   — MinIO prefix: scans/{scan_id}/frames/
#   keypoints_json        JSONB, nullable          — raw normalised keypoints output
#   metrics_json          JSONB, nullable          — computed posture metrics (see schema below)
#   digital_twin_url      VARCHAR(500), nullable   — MinIO presigned URL for 3D asset
#   overall_risk          ENUM('normal','monitor','elevated'), nullable
#                         — derived from metrics; written on completion
#   progress_message      VARCHAR(500), nullable   — current processing step, for polling
#   error_message         TEXT, nullable
#   started_at            TIMESTAMPTZ, nullable
#   completed_at          TIMESTAMPTZ, nullable
#   created_at            TIMESTAMPTZ, default now(), not null, indexed DESC
#   updated_at            TIMESTAMPTZ, default now(), not null
#
# Indexes:
#   scans.patient_id
#   scans.doctor_id
#   scans.status
#   scans.created_at DESC
#
# Relationships:
#   patient → many-to-one
#   doctor  → many-to-one
```

### Metrics JSON Schema

The `metrics_json` JSONB column stores this structure. Define it as a TypedDict
in `pipeline/metric_engine.py` for internal use:

```json
{
  "spinal_curves": {
    "thoracic_kyphosis_deg":  { "value": 42.3, "unit": "°",  "availability": "available" },
    "lumbar_lordosis_deg":    { "value": 38.7, "unit": "°",  "availability": "available" }
  },
  "pelvis_lower_body": {
    "pelvic_tilt_sagittal_deg": { "value": 9.2,  "unit": "°",  "availability": "available" },
    "pelvic_obliquity_mm":      { "value": 4.1,  "unit": "mm", "availability": "available" },
    "knee_flexion_left_deg":    { "value": 2.1,  "unit": "°",  "availability": "available" },
    "knee_flexion_right_deg":   { "value": 1.8,  "unit": "°",  "availability": "available" },
    "hka_angle_left_deg":       { "value": 178.4,"unit": "°",  "availability": "available" },
    "hka_angle_right_deg":      { "value": 177.9,"unit": "°",  "availability": "available" }
  },
  "head_shoulders": {
    "forward_head_posture_mm":      { "value": 12.4, "unit": "mm", "availability": "available" },
    "shoulder_height_asymmetry_mm": { "value": 3.1,  "unit": "mm", "availability": "available" },
    "jaw_deviation_mm":             { "value": null,  "unit": "mm", "availability": "unavailable_no_face_data" }
  },
  "spine_back": {
    "spine_drift_mm":            { "value": 5.6,  "unit": "mm",  "availability": "available" },
    "scapula_asymmetry_index":   { "value": 0.03, "unit": "",    "availability": "available" },
    "vertebral_rotation_index":  { "value": 0.01, "unit": "",    "availability": "available" },
    "adams_rib_hump_present":    { "value": false, "unit": "",   "availability": "available" }
  },
  "normal_ranges": {
    "thoracic_kyphosis_deg":        { "min": 20, "max": 45 },
    "lumbar_lordosis_deg":          { "min": 20, "max": 45 },
    "pelvic_tilt_sagittal_deg":     { "min": 0,  "max": 15 },
    "pelvic_obliquity_mm":          { "min": 0,  "max": 10 },
    "knee_flexion_left_deg":        { "min": -5, "max": 5  },
    "knee_flexion_right_deg":       { "min": -5, "max": 5  },
    "hka_angle_left_deg":           { "min": 175,"max": 180 },
    "hka_angle_right_deg":          { "min": 175,"max": 180 },
    "forward_head_posture_mm":      { "min": 0,  "max": 15 },
    "shoulder_height_asymmetry_mm": { "min": 0,  "max": 10 },
    "jaw_deviation_mm":             { "min": 0,  "max": 3  },
    "spine_drift_mm":               { "min": 0,  "max": 10 },
    "scapula_asymmetry_index":      { "min": 0,  "max": 0.1},
    "vertebral_rotation_index":     { "min": 0,  "max": 0.05 }
  }
}
```

The `availability` field uses these exact string values — the Stitch UI renders
specific messages based on them:

| Value | UI display |
|---|---|
| `available` | Show value |
| `unavailable_no_landmark` | "—  Landmark not detected" |
| `unavailable_low_confidence` | "—  Low keypoint confidence" |
| `unavailable_no_face_data` | "—  No face capture" |
| `unavailable_no_depth` | "—  Insufficient depth data" |
| `unavailable_no_sensor` | "—  Requires pressure sensor" |

### Alembic Configuration

- `alembic.ini` reads `DATABASE_URL` from environment (not hardcoded)
- Initial migration: `alembic revision --autogenerate -m "initial_schema"`
- Migration runs automatically on container startup via the Dockerfile CMD

**Stage 2 acceptance criteria:**
- `alembic upgrade head` runs clean from a blank database
- `alembic downgrade -1` then `alembic upgrade head` round-trips without error
- All tables, columns, constraints, and indexes match the specifications above
- The `ENUM` types are created as PostgreSQL native enums (not VARCHAR checks)

---

## Stage 3 — Backend API

**Goal:** A fully tested REST API covering auth, doctor profile, patients, and
scans, with async scan processing via Celery and the pluggable AI pipeline.

### 3.1 App Factory — app/main.py

```python
# Must include:
# - CORS middleware — allow origins from CORS_ORIGINS env var
# - /health endpoint returning {"status":"ok","detector_model":<DETECTOR_MODEL env>}
# - /api/v1 prefix router mounting all domain routers
# - Startup event:
#     1. Create MinIO bucket (MINIO_BUCKET) if it does not exist
#     2. Load and validate the detector via pipeline/loader.py — fail fast at startup
#        if MODEL_WEIGHTS_PATH is set but the file does not exist
# - Global exception handlers:
#     404 → {"code":"NOT_FOUND","message":"..."}
#     422 → {"code":"VALIDATION_ERROR","detail":[...]}
#     500 → {"code":"INTERNAL_ERROR","message":"An unexpected error occurred"}
# - OpenAPI metadata: title="SpinePose API", version="1.0.0"
```

### 3.2 Settings — app/config.py

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str = "spinepose-scans"
    minio_secure: bool = False
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    cors_origins: list[str] = ["http://localhost:3000"]
    detector_model: str = "spinepose_v2"        # spinepose_v2 | yolo_v8 | yolo_custom
    model_weights_path: str | None = None
    keypoint_confidence_threshold: float = 0.50
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### 3.3 Auth Endpoints — /api/v1/auth

#### POST /api/v1/auth/register
Register a new doctor account. Returns the doctor profile and a JWT.

Request body (JSON):
```json
{
  "email": "dr.smith@clinic.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Smith",
  "specialty": "Physiotherapy",
  "license_number": "MED-12345",
  "clinic_name": "City Spine Clinic",
  "country": "UK",
  "city": "London"
}
```

Validation rules:
- Email must be unique → `409 Conflict` with `{"code":"EMAIL_EXISTS",...}` if duplicate
- Password: minimum 8 characters, at least one uppercase letter, at least one digit
- Hash password with bcrypt, cost factor 12

Response `201`:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "doctor": { ... }
}
```

#### POST /api/v1/auth/login
OAuth2 password flow. Accepts `application/x-www-form-urlencoded`.

Fields: `username` (the doctor's email), `password`

Response `200`: Same shape as register.
Errors: `401` invalid credentials, `403` account inactive.

#### GET /api/v1/auth/me
Returns the current doctor's profile. Used by the top-bar avatar and Settings
page (Page 15, Profile tab).

#### PUT /api/v1/auth/me
Update profile fields: first_name, last_name, specialty, license_number,
clinic_name, country, city, bio. Does not update email or password.

This endpoint backs the Settings view (Page 15, Profile tab) "Save" button.

#### POST /api/v1/auth/change-password
```json
{ "current_password": "...", "new_password": "..." }
```
Backs the Settings view (Page 15, Security tab) change password form.

#### POST /api/v1/auth/forgot-password
```json
{ "email": "dr.smith@clinic.com" }
```
Always returns `200` with `{"message":"If that email exists, a reset link has been sent."}`.
Never disclose whether the email exists. In development, log the reset token to
stdout rather than sending email (email integration is out of scope).

This backs the Forgot Password screen (Page 3).

### 3.4 Patient Endpoints — /api/v1/patients

All endpoints require authentication. Doctors see only their own patients.
Every query MUST include a `doctor_id = current_doctor.id` filter.

#### POST /api/v1/patients
Create a patient. Backs the Add New Patient form (Page 6).

Request (JSON):
```json
{
  "first_name": "Ahmed",
  "last_name": "Hassan",
  "date_of_birth": "1985-06-15",
  "gender": "male",
  "height_cm": 175.0,
  "weight_kg": 78.5,
  "medical_record_number": "MRN-001",
  "phone": "+44 7700 900123",
  "email": "ahmed@example.com",
  "emergency_contact_name": "Fatima Hassan",
  "emergency_contact_phone": "+44 7700 900456",
  "referring_physician": "Dr. Jones",
  "primary_diagnosis": "Chronic lower back pain",
  "medical_notes": "Previous L4/L5 disc herniation in 2021"
}
```

Response `201`: Full patient object including `id`, `doctor_id`, `risk_level`,
`scan_count` (0), `created_at`, `updated_at`.

#### GET /api/v1/patients
List patients. Backs the Patient List screen (Page 5).

Query parameters:
- `page` int default 1
- `page_size` int default 20, max 100
- `search` str — searches first_name, last_name, medical_record_number (case-insensitive ILIKE)
- `risk_level` enum — filter by normal / monitor / elevated
- `sort_by` enum — last_name | created_at | last_scan_date, default created_at
- `sort_order` enum — asc | desc, default desc

Response `200`:
```json
{
  "items": [
    {
      "id": "uuid",
      "first_name": "Ahmed",
      "last_name": "Hassan",
      "medical_record_number": "MRN-001",
      "date_of_birth": "1985-06-15",
      "gender": "male",
      "height_cm": 175.0,
      "weight_kg": 78.5,
      "risk_level": "normal",
      "scan_count": 3,
      "last_scan_at": "2025-01-15T10:30:00Z",
      "created_at": "2025-01-01T09:00:00Z"
    }
  ],
  "total": 47,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

#### GET /api/v1/patients/{patient_id}
Full patient detail. Backs the Patient Profile screen (Page 7).

Response includes all patient fields plus:
- `scan_count` int
- `last_scan_at` datetime or null
- `recent_scans` array of the 5 most recent scans (summary: id, status, created_at,
  detector_model, overall_risk, metrics count)

#### PUT /api/v1/patients/{patient_id}
Update patient. All fields optional (PATCH semantics, PUT method).
Backs the Edit Patient form (Page 6 in edit mode) and inline edits on Page 7.

#### DELETE /api/v1/patients/{patient_id}
Soft-delete: sets `is_active = False`. Does not delete scan records.
Returns `204 No Content`.

### 3.5 Scan Endpoints — /api/v1/scans

#### POST /api/v1/scans
Initiate a new scan. Backs the New Scan Setup flow (Page 8) and Capture
screen (Page 9). Called after the capture step when all frames are ready.

Request (multipart/form-data):

| Field | Type | Required | Notes |
|---|---|---|---|
| patient_id | UUID | Yes | Must belong to authenticated doctor |
| capture_device | str | No | e.g. "Intel RealSense D435i" |
| camera_height_cm | float | No | From Step 2 of setup form |
| camera_distance_cm | float | No | From Step 2 of setup form |
| patient_height_cm | float | Yes | Calibration — may differ from stored profile |
| patient_weight_kg | float | Yes | Calibration |
| frame_front | file | Yes | PNG or TIFF, RGBD |
| frame_side | file | Yes | |
| frame_back | file | Yes | |
| frame_adams | file | Yes | Adams forward bend |
| frame_face | file | No | For jaw deviation metric |

Behaviour:
1. Validate patient belongs to authenticated doctor → `404` if not
2. Upload all frames to MinIO under `scans/{scan_id}/frames/`
3. Create scan record with `status=pending`, `detector_model=settings.detector_model`
4. Dispatch `process_scan.delay(scan_id)` Celery task
5. Return `202 Accepted` immediately — do not wait for processing

Response `202`:
```json
{
  "id": "uuid",
  "patient_id": "uuid",
  "status": "pending",
  "detector_model": "spinepose_v2",
  "created_at": "2025-01-15T10:30:00Z"
}
```

#### GET /api/v1/scans/{scan_id}/status
Lightweight polling endpoint. Called every 2 seconds by the Processing screen
(Page 10). Returns quickly — no heavy joins.

Response `200`:
```json
{
  "id": "uuid",
  "status": "processing",
  "progress_message": "Running keypoint detection...",
  "detector_model": "spinepose_v2",
  "started_at": "2025-01-15T10:30:05Z",
  "completed_at": null
}
```

#### GET /api/v1/scans/{scan_id}
Full scan detail with all metrics and presigned frame URLs. Backs the Scan
Results screen (Page 11).

Response `200`:
```json
{
  "id": "uuid",
  "patient_id": "uuid",
  "patient": { "first_name": "Ahmed", "last_name": "Hassan" },
  "status": "completed",
  "detector_model": "spinepose_v2",
  "capture_device": "Intel RealSense D435i",
  "camera_height_cm": 90,
  "camera_distance_cm": 260,
  "patient_height_cm": 175.0,
  "patient_weight_kg": 78.5,
  "overall_risk": "monitor",
  "digital_twin_url": "https://...",
  "metrics": { ... },
  "error_message": null,
  "started_at": "...",
  "completed_at": "...",
  "created_at": "...",
  "frame_urls": {
    "front":  "https://minio-presigned-url-1hr",
    "side":   "https://minio-presigned-url-1hr",
    "back":   "https://minio-presigned-url-1hr",
    "adams":  "https://minio-presigned-url-1hr",
    "face":   null
  }
}
```

All presigned URLs expire in 1 hour.

#### GET /api/v1/scans
List scans with filters. Backs the Scan History screen (Page 13).

Query parameters: `patient_id`, `status`, `detector_model`, `date_from`, `date_to`,
`page`, `page_size`. Only returns scans for patients belonging to the authenticated doctor.

#### GET /api/v1/patients/{patient_id}/scans
Convenience endpoint for the Scan History tab on Page 7 (Patient Profile).
Same response shape as GET /api/v1/scans filtered to one patient.

#### DELETE /api/v1/scans/{scan_id}
Delete scan record AND all associated MinIO objects (frames, digital twin).
Rejected with `409 Conflict` if `status == 'processing'`.
Returns `204 No Content`.

#### GET /api/v1/dashboard/summary
Dashboard summary for the authenticated doctor. Backs Page 4 (Dashboard).

Response `200`:
```json
{
  "total_patients": 47,
  "scans_today": 3,
  "pending_reports": 2,
  "sessions_this_month": 18,
  "recent_activity": [
    {
      "type": "scan_completed",
      "patient_name": "Ahmed Hassan",
      "timestamp": "2025-01-15T10:44:00Z",
      "scan_id": "uuid"
    }
  ],
  "recent_patients": [...]
}
```

### 3.6 Celery Task — process_scan

File: `app/workers/scan_tasks.py`

```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_scan(self, scan_id: str):
    """
    Full scan processing pipeline. Steps in order:

    1.  Load scan record from DB. Set status='processing', started_at=now().
        Set progress_message='Loading scan data...'

    2.  Download all frames from MinIO to a temporary directory.
        Set progress_message='Frames downloaded. Initialising detector...'

    3.  Load detector via pipeline/loader.py — reads DETECTOR_MODEL from settings.
        The same detector instance is used for all views of this scan.
        Set progress_message='Running keypoint detection...'

    4.  Call detector.detect(frame_paths) → raw_keypoints dict (model-specific format).

    5.  Pass raw_keypoints through KeypointNormalizer.normalize() → list[Keypoint].
        Set progress_message='Keypoints normalised. Running 3D reconstruction...'

    6.  Call Reconstructor3D.reconstruct(keypoints, depth_map, calibration)
        → keypoints with x3d, y3d, z3d populated in mm.

    7.  Call SpineCurveModel.fit(keypoints_3d) → SpineCurve object.
        Set progress_message='Fitting spine curve model...'

    8.  Call MetricEngine.compute_all(keypoints_3d, spine_curve, calibration)
        → metrics dict matching the JSONB schema above.
        Set progress_message='Computing posture metrics...'

    9.  Derive overall_risk from metrics:
        - 'elevated' if any metric value is >20% outside its normal range
        - 'monitor'  if any metric value is outside normal range
        - 'normal'   otherwise
        Update patient.risk_level to match (or worsen — never improve automatically).

    10. Generate digital twin:
        - Phase 1 (spinepose_v2): save keypoints as JSON, upload to MinIO as
          scans/{scan_id}/twin/keypoints.json
        - YOLO: same for now; full mesh export is a future enhancement
        Set digital_twin_url to the MinIO object path.

    11. Store keypoints_json and metrics_json on scan record.
        Set status='completed', completed_at=now().
        Set progress_message='Analysis complete.'

    12. Cleanup: delete temp directory.

    On any unhandled exception:
        Set status='failed', error_message=str(exception).
        Re-raise so Celery can retry up to max_retries.
    """
```

### 3.7 AI Pipeline — Pluggable Detector

#### pipeline/base.py

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Keypoint:
    name: str           # e.g. "left_ear", "c7_proxy", "spine_t4"
    x: float            # pixel x in source frame
    y: float            # pixel y in source frame
    confidence: float   # 0.0–1.0
    source_view: str    # "front" | "side" | "back" | "adams" | "face"
    x3d: float | None = None  # mm, filled by Reconstructor3D
    y3d: float | None = None
    z3d: float | None = None

class DetectorBase(ABC):
    """
    All detectors implement this interface.
    The rest of the pipeline never imports SpinePoseDetector or YOLODetector
    directly — always go through loader.py.
    """

    @abstractmethod
    def detect(self, frame_paths: dict[str, str]) -> dict:
        """
        frame_paths keys: "front", "side", "back", "adams", "face" (optional)
        Returns model-specific raw output dict.
        """
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model name for logs and the detector_model DB field."""
        ...
```

#### pipeline/loader.py

```python
from app.config import settings
from .base import DetectorBase

def get_detector() -> DetectorBase:
    """
    Reads settings.detector_model and returns the appropriate detector.
    Called once at worker startup (not per scan) — detectors are expensive to load.

    Supported values of DETECTOR_MODEL:
        spinepose_v2   → SpinePoseDetector
        yolo_v8        → YOLODetector(variant="v8")
        yolo_custom    → YOLODetector(variant="custom")

    Raises ValueError for unknown values so misconfiguration fails at startup,
    not silently at scan time.
    """
    model = settings.detector_model
    if model == "spinepose_v2":
        from .spinepose_detector import SpinePoseDetector
        return SpinePoseDetector(weights_path=settings.model_weights_path)
    elif model in ("yolo_v8", "yolo_custom"):
        from .yolo_detector import YOLODetector
        return YOLODetector(variant=model, weights_path=settings.model_weights_path)
    else:
        raise ValueError(
            f"Unknown DETECTOR_MODEL='{model}'. "
            f"Supported values: spinepose_v2, yolo_v8, yolo_custom"
        )
```

#### pipeline/spinepose_detector.py

```python
# SpinePose v2 — DFKI
# License: CC-BY-NC-4.0 (NON-COMMERCIAL USE ONLY)
# This file must not be used in any commercial product without replacing
# the model with a commercially licensed alternative.
#
# If MODEL_WEIGHTS_PATH is not set or the file does not exist, this detector
# returns zero-confidence stubs for all keypoints so the rest of the pipeline
# can be developed and tested without the actual model weights.
# A prominent WARNING is logged when running in stub mode.

class SpinePoseDetector(DetectorBase):
    def __init__(self, weights_path: str | None):
        if weights_path and os.path.exists(weights_path):
            self._model = self._load_model(weights_path)
            self._stub_mode = False
            logger.info("SpinePose v2 loaded from %s", weights_path)
        else:
            self._stub_mode = True
            logger.warning(
                "SpinePose v2 running in STUB MODE — no weights loaded. "
                "Set MODEL_WEIGHTS_PATH to load real weights. "
                "All keypoints will have confidence=0.0."
            )

    @property
    def model_name(self) -> str:
        return "spinepose_v2"

    def detect(self, frame_paths: dict[str, str]) -> dict:
        if self._stub_mode:
            return self._stub_output(frame_paths)
        # Real implementation: load frames, run SpinePose v2 inference,
        # return raw keypoints dict with x, y, confidence per landmark.
        ...
```

#### pipeline/yolo_detector.py

```python
class YOLODetector(DetectorBase):
    def __init__(self, variant: str, weights_path: str | None):
        if weights_path and os.path.exists(weights_path):
            self._model = self._load_yolo(weights_path)
            self._stub_mode = False
            logger.info("YOLO detector (%s) loaded from %s", variant, weights_path)
        else:
            self._stub_mode = True
            logger.warning(
                "YOLO detector (%s) running in STUB MODE — set MODEL_WEIGHTS_PATH.",
                variant
            )

    @property
    def model_name(self) -> str:
        return "yolo"

    def detect(self, frame_paths: dict[str, str]) -> dict:
        if self._stub_mode:
            return self._stub_output(frame_paths)
        # Real implementation: load frames, run YOLO pose inference.
        ...
```

#### Switching Between Models

To switch the active model, update `.env` and restart:

```env
# Use SpinePose v2 (non-commercial)
DETECTOR_MODEL=spinepose_v2
MODEL_WEIGHTS_PATH=/models/spinepose_v2.pth

# Use YOLO v8 (commercially licensable)
DETECTOR_MODEL=yolo_v8
MODEL_WEIGHTS_PATH=/models/yolo_v8_pose.pt
```

No code change, no redeployment of application code — just a container restart.

#### pipeline/keypoint_normalizer.py

Maps each detector's raw output to the unified `list[Keypoint]` schema.
All downstream code (Reconstructor3D, SpineCurveModel, MetricEngine) consumes
only `list[Keypoint]`, never detector-specific formats.

```python
REQUIRED_LANDMARKS = [
    # Head
    "left_ear", "right_ear",
    # Neck
    "c7_proxy",
    # Shoulders
    "left_shoulder", "right_shoulder",
    # Hips
    "left_hip", "right_hip",
    # Knees
    "left_knee", "right_knee",
    # Ankles
    "left_ankle", "right_ankle",
    # Spine chain (9 points from neck to sacrum)
    "spine_c7", "spine_t1", "spine_t4", "spine_t7",
    "spine_t10", "spine_l1", "spine_l3", "spine_l5", "spine_s1",
    # Face (optional — for jaw deviation)
    "jaw_midpoint", "facial_midline",
]
```

Landmarks below `settings.keypoint_confidence_threshold` are retained in the list
but marked with their actual confidence so MetricEngine can decide availability.

#### pipeline/metric_engine.py

Implement each metric as a standalone pure function. No side effects. No I/O.
Easily unit testable with mock keypoints.

```python
@dataclass
class CalibrationData:
    patient_height_cm: float
    patient_weight_kg: float
    camera_height_cm: float | None
    camera_distance_cm: float | None
    pixels_per_mm: float | None   # computed from patient height in pixels vs declared height

@dataclass
class MetricResult:
    value: float | bool | None
    unit: str
    availability: str   # one of the availability strings defined in Stage 2
    reason: str | None = None

def compute_forward_head_posture(landmarks: list[Keypoint], cal: CalibrationData) -> MetricResult: ...
def compute_shoulder_height_asymmetry(landmarks: list[Keypoint], cal: CalibrationData) -> MetricResult: ...
def compute_spine_drift(landmarks: list[Keypoint], cal: CalibrationData) -> MetricResult: ...
def compute_thoracic_kyphosis(landmarks: list[Keypoint], spine_curve: SpineCurve, cal: CalibrationData) -> MetricResult: ...
def compute_lumbar_lordosis(landmarks: list[Keypoint], spine_curve: SpineCurve, cal: CalibrationData) -> MetricResult: ...
def compute_pelvic_tilt_sagittal(landmarks: list[Keypoint], cal: CalibrationData) -> MetricResult: ...
def compute_pelvic_obliquity(landmarks: list[Keypoint], cal: CalibrationData) -> MetricResult: ...
def compute_knee_flexion(landmarks: list[Keypoint], cal: CalibrationData, side: str) -> MetricResult: ...
def compute_hka_angle(landmarks: list[Keypoint], cal: CalibrationData, side: str) -> MetricResult: ...
def compute_jaw_deviation(landmarks: list[Keypoint], cal: CalibrationData) -> MetricResult: ...
def compute_adams_rib_hump(landmarks: list[Keypoint], depth_map: np.ndarray | None) -> MetricResult: ...
def compute_vertebral_rotation(landmarks: list[Keypoint], depth_map: np.ndarray | None) -> MetricResult: ...

def compute_all(
    landmarks: list[Keypoint],
    spine_curve: SpineCurve,
    calibration: CalibrationData,
    depth_map: np.ndarray | None,
) -> dict:
    """
    Calls all individual metric functions and assembles the metrics_json structure.
    Never raises. Each metric function is called in a try/except so one failing
    metric does not abort the others.
    """
    ...
```

**Stage 3 acceptance criteria:**
- Full auth flow: register → login → /me works end-to-end
- Create patient → list with search/filter → get detail → update → soft-delete
- Create scan (with stub frames) → poll /status → get full results
- Celery task runs, updates scan status through pending → processing → completed
- Changing DETECTOR_MODEL in .env and restarting switches the active model
  (confirmed by the /health endpoint and the `detector_model` field on scan records)
- All endpoints enforce doctor-level data isolation
- OpenAPI docs at /docs show all endpoints with example responses

---

## Stage 4 — Frontend Integration (Vue 3 + Stitch HTML)

**Wait for Stage 3 acceptance before starting Stage 4.**

At this point you will provide your Stitch-generated HTML files. The task is to
convert each HTML file into the corresponding Vue SFC listed in the repository
structure, while preserving the exact visual design.

### 4.1 Project Setup

```bash
cd frontend
npm create vite@latest . -- --template vue
npm install vue-router@4 pinia axios
npm install -D @vitejs/plugin-vue
```

### 4.2 vite.config.js

```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true }
    }
  }
})
```

### 4.3 Conversion Rules (Applied to Every HTML File)

When converting a Stitch HTML file to a Vue SFC:

1. **CSS**: Move all `<style>` content into `<style scoped>`. Preserve every CSS
   variable, every color token, every font reference exactly as written.
   Do not normalise, simplify, or retheme anything.

2. **Data**: Replace every hardcoded string, number, or list with a reactive
   binding from `ref()`, `reactive()`, a Pinia store getter, or a prop.
   The rendered visual output must be identical to the Stitch design when
   populated with real data.

3. **Navigation**: Replace `<a href="...">` with `<RouterLink to="...">`.
   Map each href to the corresponding route defined in Section 4.5.

4. **Forms**: Replace `<form>` submit behaviour with an `async` handler that
   calls the Axios client. Show field-level error messages from API 422 responses
   beneath the relevant input.

5. **Loading states**: Every data-fetching `onMounted` must show the page's
   skeleton or spinner (from the Stitch design) while the request is in flight.
   Never show stale or empty content without a loading indicator.

6. **Do not restyle**: If the Stitch design has a yellow border, keep the yellow
   border. If it has 60px horizontal padding, keep 60px. This is a fidelity-first
   conversion — not a reimplementation.

### 4.4 Component Specifications

These components are referenced by multiple views. Build them before the views.

#### MetricCard.vue
Props: `name`, `value`, `unit`, `normalMin`, `normalMax`, `availability`,
`sourceView`, `group`

- If `availability !== 'available'`: render the `—` state with the reason string
  from the availability lookup table in Stage 2
- If value is outside [normalMin, normalMax]: render value in `#E8D600` (yellow)
  and fill RangeBar in red/amber zone
- If value is within range: render value in `#FFFFFF`, RangeBar in green zone
- `sourceView` renders as a small dim badge ("Side View", "Back View", etc.)
- Uses JetBrains Mono for the value

#### RangeBar.vue
Props: `value`, `min`, `max`, `normalMin`, `normalMax`

Visual: grey track. Colored fill showing patient value position.
Color zones: green (#16A34A) = within normal range, amber (#D97706) = borderline
(within 20% of range boundary), red (#DC2626) = outside normal range.

#### ScanStatusBadge.vue
Props: `status` — one of pending | processing | completed | failed | partial | flagged

Maps to Stitch pill design:
- completed → green (#16A34A) background tint, "Complete"
- processing → blue (#2563EB) pulsing animation, "Processing"
- pending    → dim white, "Pending"
- failed     → red (#DC2626) tint, "Failed"
- partial    → amber (#D97706) tint, "Partial"
- flagged    → red (#DC2626) tint, "Flagged"

#### RiskLevelBadge.vue
Props: `level` — normal | monitor | elevated

normal   → green tint, "Normal"
monitor  → amber tint, "Monitor"
elevated → red tint, "Elevated"

#### DigitalTwinViewer.vue
- Loads Three.js from CDN (`https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js`)
- Props: `keypointsJson` (the scan's `keypoints_json` object), `view` (front|side|back)
- Renders a stick figure from the normalised keypoint coordinates
- OrbitControls for mouse rotation (load from CDN)
- Front / Side / Back toggle buttons below the canvas map to camera preset positions
- Spine curve overlay toggle draws yellow lines through the spine chain keypoints
- If `keypointsJson` is null or empty: shows centered text "3D twin not available
  for this scan" in dim white

#### ScanMetricsPanel.vue
Accepts the full `metrics` object from the scan API response.
Renders four metric groups as defined in the Stitch brief (Page 11):
- Group 1: Spinal Curves (thoracic_kyphosis_deg, lumbar_lordosis_deg)
- Group 2: Pelvis & Lower Body (pelvic_tilt_sagittal_deg, pelvic_obliquity_mm,
  knee_flexion_left_deg, knee_flexion_right_deg, hka_angle_left_deg, hka_angle_right_deg)
- Group 3: Head & Shoulders (forward_head_posture_mm, shoulder_height_asymmetry_mm,
  jaw_deviation_mm)
- Group 4: Spine & Back (spine_drift_mm, scapula_asymmetry_index,
  vertebral_rotation_index, adams_rib_hump_present)

Uses `MetricCard.vue` for each metric. Uses the `normal_ranges` object from the
metrics payload for the RangeBar bounds.

### 4.5 Route Map

```js
// src/router/index.js

const routes = [
  // Unauthenticated
  { path: '/login',          component: LoginView,          meta: { guest: true }  }, // Page 1
  { path: '/register',       component: RegisterView,       meta: { guest: true }  }, // Page 2
  { path: '/forgot-password',component: ForgotPasswordView, meta: { guest: true }  }, // Page 3

  // Authenticated
  { path: '/',               redirect: '/dashboard' },
  { path: '/dashboard',       component: DashboardView,      meta: { auth: true }   }, // Page 4
  { path: '/patients',        component: PatientsView,       meta: { auth: true }   }, // Page 5
  { path: '/patients/new',    component: PatientFormView,    meta: { auth: true }   }, // Page 6 (add)
  { path: '/patients/:id/edit',component: PatientFormView,   meta: { auth: true }   }, // Page 6 (edit)
  { path: '/patients/:id',    component: PatientProfileView, meta: { auth: true }   }, // Page 7
  { path: '/scans/new',       component: ScanSetupView,      meta: { auth: true }   }, // Page 8
  { path: '/scans/:id/capture',component: ScanCaptureView,   meta: { auth: true }   }, // Page 9
  { path: '/scans/:id/processing',component: ScanProcessingView, meta: { auth: true }}, // Page 10
  { path: '/scans/:id',       component: ScanResultsView,    meta: { auth: true }   }, // Page 11
  { path: '/scans/:id/export',component: ReportExportView,   meta: { auth: true }   }, // Page 12
  { path: '/scans',           component: ScanHistoryView,    meta: { auth: true }   }, // Page 13
  { path: '/reports',         component: ReportsLibraryView, meta: { auth: true }   }, // Page 14
  { path: '/settings',        component: SettingsView,       meta: { auth: true }   }, // Page 15
  { path: '/help',            component: HelpView,           meta: { auth: true }   }, // Page 16
]

// Navigation guards:
// meta.auth  → redirect to /login if no valid token
// meta.guest → redirect to /dashboard if already authenticated
```

### 4.6 Pinia Stores

#### stores/auth.js
```js
// State:   token (string|null), doctor (profile object|null)
// Actions: login(email, password), register(payload), logout(), fetchMe(),
//          updateProfile(payload), changePassword(current, next)
// Getters: isAuthenticated, doctorFullName, doctorInitials
// Persist: token stored in localStorage key 'sp_token'
//          hydrated on app load in main.js before router guard runs
```

#### stores/patients.js
```js
// State:   list (array), current (patient|null), pagination, loading
// Actions: fetchList(params), fetchOne(id), create(payload),
//          update(id, payload), softDelete(id)
// Getters: totalCount
```

#### stores/scans.js
```js
// State:   current (scan|null), list (array), polling (bool), loading
// Actions: createScan(formData), pollStatus(scanId), fetchScan(scanId),
//          fetchList(params), deleteScan(scanId)
// Auto-stops polling when status becomes 'completed' or 'failed'.
// On 'failed': stores the error_message and surfaces it on the Processing view.
```

### 4.7 Axios API Client — src/api/client.js

```js
// Base URL: import.meta.env.VITE_API_URL ?? '/api/v1'
//
// Request interceptor:
//   Attach 'Authorization: Bearer <token>' from auth store if present
//
// Response interceptors:
//   401 → authStore.logout() then router.push('/login')
//   422 → parse body.detail into { field: message } map, re-throw as structured error
//         so form components can display field-level messages beneath inputs
//   500 → emit a global error event for a top-level toast component
//
// Export named functions matching each API endpoint:
//   auth:     registerDoctor, loginDoctor, getMe, updateMe, changePassword, forgotPassword
//   patients: createPatient, listPatients, getPatient, updatePatient, deletePatient
//   scans:    createScan, getScan, getScanStatus, listScans, listPatientScans, deleteScan
//   dashboard: getDashboardSummary
```

### 4.8 View-Specific Notes

**ScanSetupView.vue (Page 8)**
- Implements the 5-step progress bar from the Stitch brief
- Steps 1–3 are checklist-gated: cannot advance until all checkboxes are ticked
- Step 4 navigates to ScanCaptureView with `patient_id` as a query param

**ScanCaptureView.vue (Page 9)**
- Collects 4 required + 1 optional file uploads with preview thumbnails
- Shows the pose cards panel matching the Stitch design
- On "Start Analysis": calls `createScan()` then navigates to ScanProcessingView

**ScanProcessingView.vue (Page 10)**
- On mount, starts polling `getScanStatus()` every 2 seconds
- Renders the 4-step progress list from the Stitch brief; maps `progress_message`
  to the current in-progress step
- On status = 'completed': navigate to `/scans/{id}`
- On status = 'failed': show error card with `error_message`, offer retry or cancel

**ScanResultsView.vue (Page 11)**
- Uses `ScanMetricsPanel.vue` for the left column
- Uses `DigitalTwinViewer.vue` for the right column
- Pose thumbnails row uses the presigned `frame_urls` from the API response
- "Export PDF" button navigates to `/scans/{id}/export`

**SettingsView.vue (Page 15)**
- Left sub-nav: Profile · Clinic · Notifications · Device & Camera · Security
- Profile tab: backed by `PUT /api/v1/auth/me`
- Security tab: backed by `POST /api/v1/auth/change-password`
- Device & Camera tab: renders the confidence threshold slider from the Stitch
  design. Note: the threshold is currently backend-only (`KEYPOINT_CONFIDENCE_THRESHOLD`
  env var); the slider shows the current value from a `GET /api/v1/settings` endpoint
  (read-only in this version — a future enhancement allows per-doctor overrides)

**Stage 4 acceptance criteria:**
- `docker compose up` serves the app at http://localhost:3000
- All 16 Stitch pages are reachable and match the design
- Full user journey works: register → login → add patient → new scan →
  processing → results → export
- Scan status polling works on the Processing screen
- DigitalTwinViewer renders a stick figure for completed scans
- Unauthenticated access to protected routes redirects to /login
- Direct URL navigation and browser refresh work on all routes

---

## Stage 5 — Tests

### Backend Tests

```
backend/tests/
├── conftest.py                   # test DB fixture, test client, authed client
├── test_auth.py
│   ├── test_register_success
│   ├── test_register_duplicate_email_409
│   ├── test_register_weak_password_422
│   ├── test_login_success
│   ├── test_login_wrong_password_401
│   ├── test_me_returns_profile
│   └── test_me_unauthenticated_401
├── test_patients.py
│   ├── test_create_patient_201
│   ├── test_list_patients_pagination
│   ├── test_search_patients
│   ├── test_get_own_patient_200
│   ├── test_get_other_doctors_patient_404
│   ├── test_update_patient_200
│   └── test_delete_patient_soft_204
├── test_scans.py
│   ├── test_create_scan_202
│   ├── test_poll_status_returns_progress_message
│   ├── test_get_scan_with_metrics_200
│   ├── test_delete_scan_while_processing_409
│   └── test_list_scans_filtered_by_patient
├── test_dashboard.py
│   └── test_summary_counts_correct
└── test_pipeline/
    ├── test_loader_unknown_model_raises_value_error
    ├── test_loader_spinepose_loads_in_stub_mode
    ├── test_loader_yolo_loads_in_stub_mode
    ├── test_keypoint_normalizer.py
    └── test_metric_engine.py     # one test per metric function with mock landmarks
```

Run inside Docker:
```bash
docker compose exec backend pytest tests/ -v --tb=short
```

---

## Stage 6 — Production Hardening

Implement only after Stages 1–5 are complete and passing.

1. **Rate limiting** — `slowapi`: 5 req/min on `/api/v1/auth/login`,
   100 req/min globally
2. **HTTPS** — Add Caddy or Traefik reverse proxy service in Docker Compose
   with automatic Let's Encrypt certificates
3. **Celery monitoring** — Add Flower service on port 5555
4. **Database backups** — `pg_dump` cron container writing to MinIO `backups/`
   bucket, daily retention
5. **Structured logging** — `structlog` with JSON output to stdout; include
   `scan_id`, `doctor_id`, `detector_model` in every log line emitted from the
   pipeline
6. **GET /api/v1/settings** — read-only endpoint returning current server
   configuration (detector_model, confidence_threshold, model_weights_loaded bool);
   used by the Settings Device & Camera tab

---

## Global Coding Standards

### Python
- Type hints on every function signature — no bare `Any`
- Pydantic v2 for all request/response schemas
- All DB queries via SQLAlchemy 2.x async session — no raw SQL strings
- No blocking calls inside async route handlers — use `asyncio.to_thread()` for
  CPU-bound pipeline code or run it in Celery
- `logging` module only — never `print()`
- Maximum function body: 40 lines; extract helpers beyond that
- Docstrings on all public functions in the pipeline layer

### API design
- All routes under `/api/v1/` prefix
- Error detail always a dict: `{"code": "SNAKE_CASE_CODE", "message": "..."}`
  — never a bare string
- `201` for creation, `202` for async-accepted, `204` for deletion
- Paginated lists always include `total`, `page`, `page_size`, `pages`
- Presigned MinIO URLs always 1-hour expiry

### Security
- Never log request bodies containing passwords or raw frame data
- All patient data queries include `doctor_id = current_doctor.id`
- JWT secret must be ≥ 64 characters in production
- `is_active` check on every authenticated request

### Vue 3
- Composition API with `<script setup>` only — no Options API
- `defineProps()` with runtime type validation on every component
- No inline `style=""` attributes — use scoped CSS or CSS variables
- Every `onMounted` that fetches data shows a loading state first

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `POSTGRES_PASSWORD` | Yes | — | PostgreSQL password |
| `MINIO_ROOT_USER` | Yes | — | MinIO access key |
| `MINIO_ROOT_PASSWORD` | Yes | — | MinIO secret key |
| `MINIO_BUCKET` | No | `spinepose-scans` | Default bucket |
| `MINIO_SECURE` | No | `false` | Use HTTPS for MinIO |
| `JWT_SECRET` | Yes | — | ≥64 random characters |
| `JWT_ALGORITHM` | No | `HS256` | |
| `JWT_EXPIRE_MINUTES` | No | `1440` | 24 hours |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated |
| `DETECTOR_MODEL` | No | `spinepose_v2` | `spinepose_v2` \| `yolo_v8` \| `yolo_custom` |
| `MODEL_WEIGHTS_PATH` | No | — | Absolute path to weights file |
| `KEYPOINT_CONFIDENCE_THRESHOLD` | No | `0.50` | |
| `LOG_LEVEL` | No | `INFO` | |

---

## Quick Start

```bash
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD, MINIO_ROOT_PASSWORD, JWT_SECRET at minimum

docker compose up --build

# Verify:
curl http://localhost:8000/health
# → {"status":"ok","detector_model":"spinepose_v2"}

# App:      http://localhost:3000
# API docs: http://localhost:8000/docs
# MinIO UI: http://localhost:9001
```
