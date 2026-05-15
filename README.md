# DeepShield

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![AWS ECS](https://img.shields.io/badge/AWS-ECS%20Fargate-FF9900?logo=amazon-aws&logoColor=white)
![Tests](https://img.shields.io/badge/tests-92%2F92%20passing-16a34a)
![License](https://img.shields.io/badge/license-MIT-6366f1)

**AI-powered deepfake detection with behavioral biometrics — IOB Cybernova Hackathon 2026**

> DeepShield is a Security-as-a-Service platform that detects deepfakes, verifies liveness, and scores authentication risk in under 800ms. Banks plug in via a single REST API — no SDK, no PII storage.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Next.js Frontend                         │
│   Landing · Live Demo · Dashboard · Integration Guide        │
│   Explainability Panel · Biometrics Trust Score              │
└───────────────────────────┬──────────────────────────────────┘
                            │ NEXT_PUBLIC_API_URL (ALB)
                ┌───────────▼───────────┐
                │  AWS Application      │
                │  Load Balancer        │
                │  deepshield-alb       │
                │  ap-south-1           │
                └───────────┬───────────┘
                            │ port 8000
┌───────────────────────────▼──────────────────────────────────┐
│                  FastAPI Backend (ECS Fargate)                │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   Deepfake   │  │   Liveness   │  │   Behavioural    │   │
│  │  Detection   │  │   Detector   │  │   Biometrics     │   │
│  │ MobileNetV2  │  │ MobileNetV2  │  │  Keystroke +     │   │
│  │  + Ensemble  │  │  + Cascades  │  │  Mouse model     │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│                                                              │
│       JWT Auth · Redis sessions · Rate limiting              │
│       Audit log · Analytics · Risk scoring                   │
└──────────────┬──────────────────────────┬────────────────────┘
               │                          │
       ┌───────▼──────┐          ┌────────▼────────┐
       │  PostgreSQL   │          │     Redis        │
       │  (SQLite in   │          │  Sessions +      │
       │   dev/test)   │          │  Model cache     │
       └──────────────┘          └─────────────────┘
```

---

## Demo walkthrough

1. Open the frontend (`http://localhost:3000` or the live URL)
2. Click **Live demo →** in the navigation bar
3. Click **Quick demo →** — a temporary account is created automatically
4. Allow webcam access and click **▶ Start 5-second analysis**
5. Watch the **live confidence meter** animate in real time during scanning
6. Get your result:
   - **ALLOW** — verified real person
   - **CHALLENGE** — suspicious, MFA triggered
   - **BLOCK** — deepfake detected
7. On a BLOCK result, see the **explainability panel**: animated confidence bar, top 3 detection signals, and a 12-region face heatmap
8. On a BLOCK result, see the **side-by-side frame comparison** with red anomaly overlays
9. Check the **Dashboard** for the behavioral biometrics trust score card

> **Screenshot placeholders** — add `docs/screenshots/demo.png`, `docs/screenshots/dashboard.png`, `docs/screenshots/result-block.png`

---

## Quick start — Backend

**Requirements:** Python 3.9+, Redis (optional)

```bash
# 1. Clone and install
git clone <repo-url>
cd deepshield
pip install -r requirements.txt

# 2. Initialise the database
python init_db.py

# 3. (Optional) Pre-load ML models
python initialize_ml_models.py

# 4. Start the server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API live at `http://localhost:8000` · Swagger docs at `http://localhost:8000/docs`

### Backend environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./deepshield.db` | Database connection string |
| `SECRET_KEY` | — (required in prod) | JWT signing secret |
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `ENVIRONMENT` | `development` | `development` / `production` |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | CORS allowed origins |

---

## Quick start — Frontend

**Requirements:** Node.js 18+

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
npm run build      # production build
```

### Frontend environment variables

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Backend API base URL |

Set the production URL in `frontend/.env.production` before deploying. The CI/CD pipeline updates this automatically with the ALB DNS on each deployment.

---

## Full stack with Docker

```bash
# Full stack (backend + frontend + Redis + Postgres)
docker compose up

# Backend only
docker build -t deepshield-api .
docker run -p 8000:8000 deepshield-api

# Frontend only
docker build -t deepshield-frontend ./frontend
docker run -p 3000:3000 deepshield-frontend
```

---

## API reference

Base URL: `http://localhost:8000/api/v1`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/users/register` | — | Register a new user |
| `POST` | `/users/login` | — | Get JWT access + refresh tokens |
| `POST` | `/users/refresh` | — | Refresh access token |
| `POST` | `/users/logout` | Bearer | Revoke token |
| `POST` | `/deepfake/detect` | Bearer | Detect deepfakes in video upload |
| `POST` | `/liveness/detect` | Bearer | Verify liveness in video upload |
| `POST` | `/biometrics/baseline` | Bearer | Create behavioural baseline |
| `POST` | `/analyze` | Bearer | Behavioural biometrics analysis |
| `POST` | `/risk` | Bearer | Composite risk score |
| `GET`  | `/analytics/summary` | — | Dashboard analytics (7-day) |
| `GET`  | `/health` | — | Fast health check (used by ALB) |
| `GET`  | `/health/status` | — | Detailed component status |

Full interactive reference: `http://localhost:8000/docs`

---

## Detection pipeline

```
Video upload
     │
     ▼
Frame extraction (OpenCV)
     │
     ├──▶ Neural network inference   (MobileNetV2 — 50% weight)
     ├──▶ FFT frequency analysis     (15% weight)
     ├──▶ Compression artifact scan  (15% weight)
     ├──▶ Face blend detection       (10% weight)
     └──▶ Face consistency check     (10% weight)
                    │
                    ▼
          Weighted ensemble score
                    │
          ┌─────────┴──────────┐
       < 0.5                 ≥ 0.5
       REAL ✅             DEEPFAKE 🚫
```

---

## Running tests

```bash
# Unit + integration tests (Python 3.9 and 3.11)
pytest tests/ -v --cov=backend

# Load test (requires running server)
python load_test.py --url http://localhost:8000 --users 10 --duration 30
```

**92/92 tests passing** on Python 3.9 and 3.11.

---

## CI/CD pipeline

GitHub Actions on every push to `main` / `develop`:

1. **Test** — pytest on Python 3.9 + 3.11 with Redis service container
2. **Security scan** — Bandit (SAST) + Safety (dependency CVEs)
3. **Load test** — 5 concurrent users, 30 seconds (`main` only)
4. **Deploy production** — Docker → ECR → ALB → ECS Fargate (`main`)
   - Creates `deepshield-alb` and `deepshield-tg` idempotently
   - Updates `frontend/.env.production` with ALB DNS automatically
   - Smoke-tests `GET /health` through the ALB

### Required GitHub Secrets

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | AWS IAM key |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret |
| `ECR_REPOSITORY` | ECR repo name |
| `AWS_VPC_ID` | VPC where ECS runs |
| `PUBLIC_SUBNET_IDS` | Comma-separated public subnet IDs for ALB |
| `ALB_SECURITY_GROUP_ID` | SG allowing inbound TCP 80 |

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4, Recharts, react-webcam |
| Backend | FastAPI, SQLAlchemy, Pydantic v2, Uvicorn |
| ML | TensorFlow / TF Hub (MobileNetV2), OpenCV, NumPy, SciPy |
| Auth | JWT (python-jose), bcrypt, Redis token blacklist |
| Infrastructure | AWS ECS Fargate, ECR, ALB (ap-south-1), PostgreSQL, Redis |
| CI/CD | GitHub Actions, Docker, Bandit, Safety, pytest-cov |

---

## Team

**Team Innovate X** — IOB Cybernova Hackathon 2026
