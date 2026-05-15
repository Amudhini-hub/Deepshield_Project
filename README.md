# DeepShield

**AI-powered identity fraud prevention for banking — IOB Cybernova Hackathon 2026**
*Team Innovate X*

DeepShield is a Security-as-a-Service platform that detects deepfakes, verifies liveness, and scores authentication risk in under 800ms. Banks plug in via a single REST API — no SDK, no PII storage.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js Frontend                     │
│  Landing · Live Demo · Dashboard · Integration Guide   │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP (NEXT_PUBLIC_API_URL)
┌───────────────────────▼─────────────────────────────────┐
│                  FastAPI Backend                         │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Deepfake   │  │  Liveness    │  │  Behavioural  │  │
│  │  Detection  │  │  Detector    │  │  Biometrics   │  │
│  │ MobileNetV2 │  │ MobileNetV2  │  │  Keystroke +  │  │
│  │ + Ensemble  │  │ + Cascades   │  │  Mouse model  │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
│                                                          │
│  JWT Auth · Redis sessions · Rate limiting · Audit log  │
└────────────┬────────────────────┬────────────────────────┘
             │                    │
     ┌───────▼──────┐    ┌────────▼────────┐
     │   PostgreSQL  │    │      Redis      │
     │   (SQLite in  │    │  Sessions +     │
     │    dev/test)  │    │  Model cache    │
     └──────────────┘    └─────────────────┘
```

---

## Quick start — Backend

**Requirements:** Python 3.9+, Redis (optional but recommended)

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

The API is now live at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./deepshield.db` | Database connection string |
| `SECRET_KEY` | (required in prod) | JWT signing secret |
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
npm run dev          # http://localhost:3000
```

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Backend API base URL |

Set the production URL in `frontend/.env.production` before deploying.

---

## Demo walkthrough

1. Open `http://localhost:3000`
2. Click **Live demo →** in the nav
3. Click **Quick demo →** — a temporary account is created automatically
4. Allow webcam access and click **Start 5-second analysis**
5. DeepShield records, sends to the backend, and returns:
   - Deepfake probability score
   - Liveness confidence
   - Risk decision: **ALLOW / CHALLENGE / BLOCK**

> If the backend returns "ML services unavailable", run `python initialize_ml_models.py` and restart.

---

## API overview

Base URL: `http://localhost:8000/api/v1`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/users/register` | — | Register a new user |
| `POST` | `/users/login` | — | Get JWT tokens |
| `POST` | `/deepfake/detect` | Bearer | Detect deepfakes in video upload |
| `POST` | `/liveness/detect` | Bearer | Verify liveness in video upload |
| `POST` | `/analyze` | Bearer | Behavioural biometrics analysis |
| `POST` | `/risk` | Bearer | Composite risk score |
| `GET`  | `/analytics/summary` | — | Dashboard analytics |
| `GET`  | `/health` | — | Health check |
| `GET`  | `/health/status` | — | Detailed component status |

Full reference with request/response schemas: [http://localhost:8000/docs](http://localhost:8000/docs)
Or visit the **Integration** page in the frontend.

---

## Detection pipeline

```
Video upload
     │
     ▼
Frame extraction (OpenCV)
     │
     ├──▶ Neural network inference  (MobileNetV2 — 50% weight)
     ├──▶ FFT frequency analysis    (15% weight)
     ├──▶ Compression artifact scan (15% weight)
     ├──▶ Face blend detection      (10% weight)
     └──▶ Face consistency check    (10% weight)
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

## Docker

```bash
# Backend only
docker build -t deepshield-api .
docker run -p 8000:8000 deepshield-api

# Full stack
docker compose up
```

---

## CI/CD

GitHub Actions pipeline on every push to `main` / `develop`:

1. **Test** — pytest on Python 3.9 + 3.11 with Redis service
2. **Security scan** — Bandit (SAST) + Safety (dependency CVEs)
3. **Load test** — 5 concurrent users, 30 seconds (main branch only)
4. **Deploy staging** — Docker → ECR → ECS (`develop` branch)
5. **Deploy production** — Docker → ECR → ECS (`main` branch)

Secrets required: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `ECR_REPOSITORY`, `ECS_CLUSTER`, `ECS_SERVICE`

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4, recharts, react-webcam |
| Backend | FastAPI, SQLAlchemy, Pydantic v2 |
| ML | TensorFlow / TF Hub (MobileNetV2), OpenCV, NumPy, SciPy |
| Auth | JWT (python-jose), bcrypt, Redis token blacklist |
| Infrastructure | AWS ECS (Fargate), ECR, PostgreSQL, Redis |
| CI/CD | GitHub Actions, Docker, Bandit, Safety, pytest-cov |

---

## Team

**Team Innovate X** — IOB Cybernova Hackathon 2026
