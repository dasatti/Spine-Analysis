# SpinePose — AI Posture & Spine Analysis Platform

Clinical-grade AI-powered posture and spine analysis platform for doctors and physiotherapists. Capture multi-view patient photos, run pose detection, compute posture metrics, and review annotated frames with a 3D digital twin.

---

## 🎨 Pitch Deck Presentation

A complete executive pitch deck presentation (7 pages) has been created for SpinePose:

1. **Interactive HTML Pitch Deck Presentation**: [`spineposeapp/pitch_deck.html`](spineposeapp/pitch_deck.html)  
   *Open in any web browser for fullscreen animated slides with keyboard navigation (Arrow Keys ← →).*
2. **Markdown Pitch Deck Presentation**: [`spineposeapp/pitch_deck_presentation.md`](spineposeapp/pitch_deck_presentation.md)  
   *Includes full slide notes, clinical metrics reference table, system architecture blueprints, and Mermaid diagrams.*

---

## 🚀 Key Features

- **Doctor accounts** — registration, login, profile management, role-based access.
- **Patient management** — CRUD, search, risk levels, scan history.
- **5-step scan wizard** — environment setup, camera placement, patient prep, capture, analysis.
- **Multi-view capture** — Front, Side, Back, Adams Bend (+ optional Face) via file upload or live camera.
- **AI pose pipeline** — MediaPipe Pose Landmarker Heavy with spine landmark mapping + custom YOLO classifiers.
- **12+ Posture metrics** — thoracic kyphosis, lumbar lordosis, pelvic tilt, forward head posture, Cobb angle proxy, HKA angle, lateral spine drift, scapular asymmetry.
- **Results dashboard** — annotated frames, 3D digital twin viewer, metric panels, risk indicators (`Normal`, `Monitor`, `Elevated`).
- **Async processing** — Celery workers with Redis broker and live status polling.
- **Object storage** — scan frames and digital twin assets stored in MinIO (S3-compatible).
- **Admin Research Studio** — analytics dashboard, doctor management, research dataset labeling tool with manual landmark adjustment and CSV export.
- **Production hardening** — rate limiting, structured logging, Caddy/Apache reverse proxy, DB backups, Flower monitoring.

---

## 🛠️ Technology Stack

| Layer | Technology | Description |
|-------|------------|-------------|
| **Backend API** | Python 3.12, FastAPI, Async SQLAlchemy 2, Alembic | High-concurrency async REST framework |
| **Task Queue** | Celery 5 + Redis 7 | Asynchronous AI scan processing pipeline |
| **Database** | PostgreSQL 16 | Relational data audit trail + JSONB metrics |
| **Storage** | MinIO | Self-hosted S3 object storage for raw frames & 3D assets |
| **AI Inference** | MediaPipe Pose Landmarker, Ultralytics YOLOv8 | Anatomical landmark tracking & PyTorch classifiers |
| **3D & Geometry** | Open3D, SciPy, NumPy | Spatial point cloud reconstruction & curve fitting |
| **Frontend** | Vue 3, Vite, Pinia, Vue Router, Tailwind CSS | Reactive Single Page Application |
| **Reverse Proxy** | Caddy / Apache | HTTPS termination, rate limiting, static asset proxy |
| **Containers** | Docker Compose | One-command local and production infrastructure |

---

## 📐 System Architecture

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

---

## ⚡ Quick Start

```powershell
cd spineposeapp
copy .env.example .env
# Edit .env for POSTGRES_PASSWORD, JWT_SECRET, MINIO credentials
docker compose up -d
```

Open:
- **Web App**: http://localhost
- **API Docs**: http://localhost:8000/docs
- **Interactive Pitch Deck**: [`spineposeapp/pitch_deck.html`](spineposeapp/pitch_deck.html)

---

## 📚 Project Documentation

- [`spineposeapp/README.md`](spineposeapp/README.md) — Application quick start guide
- [`spineposeapp/documentation.md`](spineposeapp/documentation.md) — Full technical architecture and API specs
- [`decs/SpinePose_Dev_Prompt.md`](decs/SpinePose_Dev_Prompt.md) — Technical implementation specification
- [`spineposeapp/pitch_deck.html`](spineposeapp/pitch_deck.html) — Interactive 7-slide Pitch Deck
- [`spineposeapp/pitch_deck_presentation.md`](spineposeapp/pitch_deck_presentation.md) — Markdown Pitch Deck Document
