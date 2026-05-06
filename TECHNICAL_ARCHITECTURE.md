# DeepShield - Technical Architecture & System Design

## System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER (Web/Mobile)                         │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ React Frontend (Web)    │  React Native/Flutter (Mobile)          │  │
│  │ - Login UI              │  - Camera Capture                       │  │
│  │ - Video Capture         │  - Biometric Collection                 │  │
│  │ - Form Interactions     │  - Touch Dynamics                       │  │
│  │ - Real-time Guidance    │  - Device Sensors (Accelerometer)       │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│  Local Encryption: TweetNaCl.js | HTTPS/TLS 1.3 | Certificate Pinning    │
└──────────────────────────────────────────────────────────────────────────┘
                                      ↓↓↓
┌──────────────────────────────────────────────────────────────────────────┐
│                      NETWORK & SECURITY LAYER                            │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  API Gateway (Kong/Traefik)                                      │   │
│  │  ├─ Rate Limiting (sliding window)                              │   │
│  │  ├─ DDoS Protection (WAF rules)                                 │   │
│  │  ├─ Request Validation                                         │   │
│  │  ├─ SSL/TLS Termination                                        │   │
│  │  └─ Load Balancing (multiple replicas)                         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
                                      ↓↓↓
┌──────────────────────────────────────────────────────────────────────────┐
│                   BACKEND API LAYER (FastAPI/Uvicorn)                    │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                    REQUEST HANDLING                               │  │
│  │  ├─ Input Validation (Pydantic)                                  │  │
│  │  ├─ JWT Validation                                               │  │
│  │  ├─ CORS Validation                                              │  │
│  │  └─ Request Signing Verification (HMAC-SHA256)                  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                  AUTHENTICATION ORCHESTRATOR                      │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │  │
│  │  │ Login Handler│  │Session Module│  │ Device Mgmt  │           │  │
│  │  ├─ Email Validate
├──────────────┤  ├─ Session Create  │
│  │ ├─ Password Hash  │  │ Refresh Token  │  ├─ Fingerprint│           │  │
│  │  ├─ User Lookup   │  │ Session Track  │  ├─ Register  │           │  │
│  │  └─ MFA Check     │  │ Token Rotate   │  └─ Validate  │           │  │
│  │                   │  │                │                │           │  │
│  │                   │  │ Session Cache  │  Device Cache  │           │  │
│  │                   │  │ (Redis)        │  (Redis)       │           │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
                                      ↓↓↓
┌──────────────────────────────────────────────────────────────────────────┐
│          BIOMETRIC VERIFICATION LAYER (Processing & Analysis)            │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐   │
│  │ DEEPFAKE DETECTOR │  │ LIVENESS CHECKER  │  │ BEHAVIORAL ANALYST│   │
│  │                   │  │                   │  │                   │   │
│  │ Input: Video      │  │ Input: Video      │  │ Input: Events     │   │
│  ├─ Frame Extract    │  ├─ Passive Analysis│  ├─ Typing Pattern   │   │
│  ├─ Preprocess       │  │  - RPPG Analysis │  ├─ Mouse Movement  │   │
│  │  (Normalize)      │  │  - Pupil Track   │  ├─ Click Patterns  │   │
│  ├─ FFT Analysis     │  │  - Micro-expr    │  ├─ Navigation Flow │   │
│  ├─ Artifact Detect  │  ├─ Active Challenges    ├─ Form Behavior   │   │
│  │  (Compression)    │  │  - Head Movement │  ├─ Touch Dynamics  │   │
│  ├─ Ensemble Methods │  │  - Eye Gaze      │  └─ Device Sensors  │   │
│  │  - XceptionNet    │  │  - Blink Count   │                     │   │
│  │  - MesoNet        │  ├─ Temporal Check │  Template Storage    │   │
│  │  - EfficientNet   │  │  (Consistency)  │  ├─ Encrypted Hash   │   │
│  │  - ViT            │  │                 │  ├─ User Baseline    │   │
│  ├─ Confidence Score │  ├─ Confidence     │  ├─ Version Control  │   │
│  │  (0.0 - 1.0)      │  │  Score          │  └─ Expiration Mgmt  │   │
│  └─────────┬─────────┘  └─────────┬───────┘  └────────┬──────────┘   │
│            │                      │                    │                │
│       Result:                Result:              Result:              │
│  ├─ is_deepfake    ├─ is_alive         ├─ is_legitimate          │  │
│  ├─ confidence     ├─ challenge_type   ├─ deviation_score        │  │
│  ├─ anomalies      ├─ anomalies        ├─ risk_flags             │  │
│  └─ frame_count    └─ frame_count      └─ confidence             │  │
└──────────────────────────────────────────────────────────────────────────┘
                                      ↓↓↓
┌──────────────────────────────────────────────────────────────────────────┐
│                    RISK ASSESSMENT & DECISION ENGINE                     │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                     RISK FACTOR ANALYSIS                          │  │
│  │  ┌──────────────────────────────────────────────────────────────┐ │  │
│  │  │ 1. BIOMETRIC RISK (30%)                                    │ │  │
│  │  │    ├─ Face confidence vs baseline                          │ │  │
│  │  │    ├─ Voice confidence vs baseline                         │ │  │
│  │  │    ├─ Liveness confidence                                  │ │  │
│  │  │    └─ Deepfake probability                                 │ │  │
│  │  └──────────────────────────────────────────────────────────────┘ │  │
│  │  ┌──────────────────────────────────────────────────────────────┐ │  │
│  │  │ 2. BEHAVIORAL RISK (25%)                                   │ │  │
│  │  │    ├─ Typing pattern deviation                             │ │  │
│  │  │    ├─ Mouse movement deviation                             │ │  │
│  │  │    ├─ Navigation pattern deviation                         │ │  │
│  │  │    └─ Interaction time anomalies                           │ │  │
│  │  └──────────────────────────────────────────────────────────────┘ │  │
│  │  ┌──────────────────────────────────────────────────────────────┐ │  │
│  │  │ 3. CONTEXTUAL RISK (25%)                                   │ │  │
│  │  │    ├─ Geolocation (impossible travel detection)            │ │  │
│  │  │    ├─ Device fingerprint mismatch                          │ │  │
│  │  │    ├─ Network/VPN detection                                │ │  │
│  │  │    ├─ Time-of-access anomaly                               │ │  │
│  │  │    ├─ Proxy/Bot detection                                  │ │  │
│  │  │    └─ IP reputation scoring                                │ │  │
│  │  └──────────────────────────────────────────────────────────────┘ │  │
│  │  ┌──────────────────────────────────────────────────────────────┐ │  │
│  │  │ 4. HISTORICAL RISK (20%)                                   │ │  │
│  │  │    ├─ Failed attempt frequency                             │ │  │
│  │  │    ├─ Account lockout history                              │ │  │
│  │  │    ├─ Unusual activity patterns                            │ │  │
│  │  │    ├─ Transaction history anomalies                        │ │  │
│  │  │    └─ Regulatory/Policy violations                         │ │  │
│  │  └──────────────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                   ADAPTIVE DECISION LOGIC                         │  │
│  │                                                                   │  │
│  │  Risk Score Calculation (Weighted Ensemble):                     │  │
│  │  ├─ Calculate component scores (each 0-100)                     │  │
│  │  ├─ Apply weights (biometric=30%, behavioral=25%, etc.)         │  │
│  │  ├─ Aggregate: total_score = Σ(weight × component_score)       │  │
│  │  ├─ Normalize to 0-100 range                                    │  │
│  │  └─ Apply user-specific threshold adjustment                   │  │
│  │                                                                   │  │
│  │  Decision Rules:                                                │  │
│  │  ├─ Score 0-30 (LOW):      Auto-approve + Log                  │  │
│  │  ├─ Score 30-70 (MEDIUM):  Step-up authentication required     │  │
│  │  ├─ Score 70-90 (HIGH):    Multi-factor + manual review        │  │
│  │  └─ Score 90+ (CRITICAL):  Deny + escalate + alert             │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
                                      ↓↓↓
┌──────────────────────────────────────────────────────────────────────────┐
│                   DECISION & SESSION CREATION                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ APPROVAL                   │ ESCALATION            │ DENIAL        │  │
│  │                            │                       │               │  │
│  │ ├─ Generate JWT Token      │ ├─ Flag for review    │ ├─ Log event  │  │
│  │ ├─ Create Session          │ ├─ Send to analysts   │ ├─ Alert user │  │
│  │ ├─ Store device FP         │ ├─ Wait for approval  │ ├─ Block user │  │
│  │ ├─ Log success             │ ├─ Temporary session  │ ├─ Increment  │  │
│  │ ├─ Update baseline         │ ├─ Limited access     │ │  failures   │  │
│  │ └─ Notify user             │ └─ Timeout action     │ ├─ Lockout if │  │
│  │                            │                       │ │  threshold  │  │
│  │ Return: 200 OK             │ Return: 202 Accepted │ │ met         │  │
│  │ + Access Token             │ + Review Token       │ └─ Return: 401│  │
│  │ + Refresh Token            │                       │  + Reason     │  │
│  │ + Session Info             │                       │               │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
                                      ↓↓↓
┌──────────────────────────────────────────────────────────────────────────┐
│              DATA & PERSISTENCE LAYER (PostgreSQL + Redis)               │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                    RELATIONAL DATABASE                            │  │
│  │                   (PostgreSQL Primary)                            │  │
│  │                                                                   │  │
│  │  ├─ Users (id, email, username, status, created_at)            │  │
│  │  ├─ Biometric Templates (user_id, template_type, encrypted)    │  │
│  │  ├─ Authentication Sessions (user_id, status, tokens)          │  │
│  │  ├─ Verification Results (session_id, type, confidence)        │  │
│  │  ├─ Risk Assessments (session_id, score, factors)              │  │
│  │  ├─ Behavioral Baselines (user_id, profiles, confidence)       │  │
│  │  ├─ Registered Devices (user_id, fingerprint, trusted)         │  │
│  │  ├─ Audit Logs (user_id, action, status, timestamp)           │  │
│  │  └─ Model Metadata (model_name, version, accuracy)             │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                      IN-MEMORY CACHE                              │  │
│  │                    (Redis High-Speed)                             │  │
│  │                                                                   │  │
│  │  ├─ Session Cache: {user_id} → session_data (TTL: 24h)          │  │
│  │  ├─ User Cache: {user_id} → user_profile (TTL: 1h)             │  │
│  │  ├─ Behavioral Cache: {user_id} → baseline (TTL: 30d)          │  │
│  │  ├─ Device Cache: {device_fp} → device_info (TTL: 90d)         │  │
│  │  ├─ Rate Limit Counters: {ip} → attempts (TTL: sliding)        │  │
│  │  ├─ Lockout Tracking: {user_id} → lockout_end (TTL: 15m)       │  │
│  │  ├─ Model Cache: ml_model_{name} → model_bin (persistent)      │  │
│  │  └─ Config Cache: system_config → settings (TTL: 1h)           │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                  REPLICATION & BACKUP                             │  │
│  │                                                                   │  │
│  │  ├─ PostgreSQL Streaming Replication (Primary → Replicas)       │  │
│  │  ├─ Daily Database Snapshots → S3/GCS                           │  │
│  │  ├─ WAL Archival for PITR (Point-in-Time Recovery)              │  │
│  │  ├─ Redis RDB Snapshots (every 6 hours)                         │  │
│  │  ├─ Cross-region backup replication                             │  │
│  │  └─ Automated backup verification tests                         │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
                                      ↓↓↓
┌──────────────────────────────────────────────────────────────────────────┐
│              AUDIT, COMPLIANCE & MONITORING LAYER                        │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                    AUDIT & COMPLIANCE                              │  │
│  │                                                                   │  │
│  │  Audit Logging (to PostgreSQL + S3):                             │  │
│  │  ├─ WHAT: Action type (login, verify, deny)                     │  │
│  │  ├─ WHO: User ID, device fingerprint, IP                        │  │
│  │  ├─ WHEN: Timestamp with timezone                               │  │
│  │  ├─ WHERE: Geolocation, network info                            │  │
│  │  ├─ HOW: Method (face, voice, behavioral)                       │  │
│  │  ├─ RESULT: Success/failure/escalation                          │  │
│  │  ├─ WHY: Risk factors, context                                  │  │
│  │  └─ RETENTION: 90 days active, 2 years archive                  │  │
│  │                                                                   │  │
│  │  GDPR Compliance:                                                │  │
│  │  ├─ Consent tracking & management                                │  │
│  │  ├─ Right to access (data export)                               │  │
│  │  ├─ Right to deletion (secure erasure)                          │  │
│  │  ├─ Data minimization (auto-deletion after retention)           │  │
│  │  └─ Privacy impact assessment (DPIA)                            │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                   MONITORING & OBSERVABILITY                       │  │
│  │                                                                   │  │
│  │  Metrics Collection (Prometheus):                                │  │
│  │  ├─ Authentication success rate                                  │  │
│  │  ├─ Deepfake detection accuracy                                  │  │
│  │  ├─ API response times (p50, p95, p99)                          │  │
│  │  ├─ Database query latency                                       │  │
│  │  ├─ Cache hit rate                                               │  │
│  │  ├─ Error rates by endpoint                                      │  │
│  │  ├─ ML model inference time                                      │  │
│  │  └─ System resource usage (CPU, memory)                          │  │
│  │                                                                   │  │
│  │  Logging (ELK Stack):                                            │  │
│  │  ├─ Application logs (FastAPI)                                   │  │
│  │  ├─ Access logs (Nginx/Kong)                                     │  │
│  │  ├─ Security logs (auth attempts, failed verifications)         │  │
│  │  ├─ ML processing logs                                           │  │
│  │  ├─ Database logs (slow queries)                                 │  │
│  │  └─ Aggregated log search & analysis                             │  │
│  │                                                                   │  │
│  │  Alerting (Alert Manager):                                       │  │
│  │  ├─ High error rate (> 5% in 5min)                              │  │
│  │  ├─ Service unavailability                                       │  │
│  │  ├─ High fraud rate anomaly                                      │  │
│  │  ├─ Database replication lag                                     │  │
│  │  ├─ Certificate expiration warning                               │  │
│  │  └─ Escalate to incident management                              │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Component Interaction Flow

### 1. Authentication Request Flow
```
Client Request
    ↓
API Gateway (Rate Limit, CORS Check)
    ↓
Request Validation (Input Sanitization)
    ↓
JWT Token Validation (if token present)
    ↓
Route to Handler
    ├─ Login Handler
    ├─ Register Handler
    ├─ Verify Handler (biometric upload)
    └─ Token Refresh Handler
    ↓
Business Logic Execution
    ├─ Database Query
    ├─ Cache Check/Update
    └─ External API Calls
    ↓
Response Generation
    ├─ Serialize Response
    ├─ Sign Response
    └─ Encrypt Sensitive Data
    ↓
Response to Client (with Security Headers)
```

### 2. Biometric Verification Flow
```
Frontend Upload (Video/Voice File)
    ↓
Backend Receive & Validate
    ├─ File type check
    ├─ Size validation
    └─ Virus scan (ClamAV)
    ↓
Process Queue (Celery Task)
    ↓
Pre-processing
    ├─ Codec detection & conversion
    ├─ Frame extraction
    └─ Normalization
    ↓
Parallel Processing (GPU)
    ├─ Deepfake Detection Engine
    │   ├─ FFT Analysis
    │   ├─ Artifact Detection
    │   └─ Ensemble Methods
    ├─ Liveness Detection Engine
    │   ├─ Movement Analysis
    │   ├─ Physiological Signals
    │   └─ Temporal Consistency
    └─ Behavioral Analysis Engine
        ├─ Pattern Extraction
        ├─ Template Comparison
        └─ Anomaly Detection
    ↓
Aggregate Results
    ├─ Confidence Scoring
    ├─ Anomaly Flagging
    └─ Store Results in DB
    ↓
Risk Assessment
    ├─ Multi-factor scoring
    ├─ Threshold evaluation
    └─ Decision generation
    ↓
Session Action
    ├─ Create Session (Low Risk)
    ├─ Request More Verification (Medium Risk)
    └─ Deny & Alert (High Risk)
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER (Production)                  │
├─────────────────────────────────────────────────────────────────────┤
│  Ingress Controller (Kong/Traefik)                                  │
│  ├─ TLS Termination                                                 │
│  ├─ Rate Limiting                                                   │
│  └─ Request Routing                                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Namespace: deepshield-prod                                         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Backend Deployment (3 replicas)                                │ │
│  │ ├─ Pod 1: FastAPI Server + Gunicorn Workers                   │ │
│  │ ├─ Pod 2: FastAPI Server + Gunicorn Workers                   │ │
│  │ └─ Pod 3: FastAPI Server + Gunicorn Workers                   │ │
│  │ Health Check: /health endpoint                                 │ │
│  │ Resource Limits: 2CPU, 4GB RAM per pod                         │ │
│  │ Auto-scaling: 3-10 replicas based on CPU                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Frontend Deployment (3 replicas)                               │ │
│  │ ├─ Pod 1: Nginx serving React build                           │ │
│  │ ├─ Pod 2: Nginx serving React build                           │ │
│  │ └─ Pod 3: Nginx serving React build                           │ │
│  │ Health Check: GET /index.html                                  │ │
│  │ Resource Limits: 500m CPU, 256MB RAM per pod                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Celery Workers (2 replicas)                                    │ │
│  │ ├─ Worker 1: Video Processing + Inference                     │ │
│  │ └─ Worker 2: Video Processing + Inference                     │ │
│  │ GPU Support: NVIDIA CUDA-enabled                               │ │
│  │ Resource Limits: 4CPU, 8GB RAM + 1 GPU per pod                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ StatefulSet: PostgreSQL Primary                               │ │
│  │ ├─ 1 Primary (Read + Write)                                   │ │
│  │ └─ Persistent Volume (100GB SSD)                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Deployment: PostgreSQL Read Replicas                           │ │
│  │ ├─ Replica 1 (for read load balancing)                         │ │
│  │ └─ Replica 2 (for backup/failover)                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ StatefulSet: Redis Cluster                                     │ │
│  │ ├─ Master 1 (3 replicas each for HA)                           │ │
│  │ ├─ Master 2                                                     │ │
│  │ ├─ Master 3                                                     │ │
│  │ └─ Persistent Volumes (20GB each)                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Services (Internal)                                             │ │
│  │ ├─ backend-service (ClusterIP)                                 │ │
│  │ ├─ frontend-service (ClusterIP)                                │ │
│  │ ├─ postgres-service (ClusterIP, port 5432)                     │ │
│  │ └─ redis-service (ClusterIP, port 6379)                        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ ConfigMaps & Secrets                                           │ │
│  │ ├─ configmap-deepshield (database URL, log levels)            │ │
│  │ └─ secret-deepshield (JWT keys, DB password)                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│  Monitoring & Logging                                               │
│  ├─ Prometheus (Metrics Collection)                                 │
│  ├─ Grafana (Dashboards & Visualization)                            │
│  ├─ ELK Stack (Elasticsearch, Logstash, Kibana)                    │
│  ├─ Jaeger (Distributed Tracing)                                    │
│  └─ AlertManager (Alert Routing)                                    │
└─────────────────────────────────────────────────────────────────────┘
                            ↓ External
┌─────────────────────────────────────────────────────────────────────┐
│              External Services & Infrastructure                      │
├─────────────────────────────────────────────────────────────────────┤
│  ├─ AWS S3 (Biometric data, backups, audit logs)                   │
│  ├─ CloudFlare CDN (Static assets, DDoS protection)                │
│  ├─ SendGrid (Email notifications)                                  │
│  ├─ Twilio (SMS notifications)                                      │
│  ├─ MaxMind (Geolocation services)                                  │
│  ├─ Certificate Authority (SSL/TLS certificates)                    │
│  └─ Third-party Analytics (Mixpanel, Segment)                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema (Optimized)

### Core Tables
```sql
-- USERS TABLE
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active', -- active, suspended, locked
    mfa_enabled BOOLEAN DEFAULT FALSE,
    consent_given BOOLEAN DEFAULT FALSE,
    consent_timestamp TIMESTAMP,
    failed_attempts INT DEFAULT 0,
    locked_until TIMESTAMP,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    
    INDEX idx_email (email),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- BIOMETRIC TEMPLATES TABLE (Encrypted)
CREATE TABLE biometric_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_type VARCHAR(50) NOT NULL, -- face, voice, facial_expr
    encrypted_template BYTEA NOT NULL, -- AES-256-GCM encrypted
    template_version INT DEFAULT 1,
    confidence_baseline FLOAT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE (user_id, template_type, is_active),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);

-- AUTHENTICATION SESSIONS TABLE
CREATE TABLE authentication_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_token VARCHAR(512) NOT NULL, -- hashed
    status VARCHAR(20) DEFAULT 'pending', -- pending, verified, failed, escalated
    ip_address INET NOT NULL,
    user_agent TEXT,
    device_fingerprint VARCHAR(255),
    geolocation JSONB, -- {latitude, longitude, country, city}
    is_mobile BOOLEAN,
    verification_methods JSONB DEFAULT '[]', -- [face, liveness, behavioral]
    risk_score FLOAT,
    risk_level VARCHAR(20),
    challenge_sent_at TIMESTAMP,
    verified_at TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '24 hours'),
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_expires_at (expires_at)
);

-- VERIFICATION RESULTS TABLE
CREATE TABLE verification_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES authentication_sessions(id) ON DELETE CASCADE,
    verification_type VARCHAR(50) NOT NULL, -- deepfake, liveness, behavioral
    confidence FLOAT NOT NULL,
    passed BOOLEAN NOT NULL,
    result_data JSONB,
    anomalies JSONB DEFAULT '[]',
    model_name VARCHAR(100),
    model_version VARCHAR(20),
    processing_time_ms INT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_session_id (session_id),
    INDEX idx_verification_type (verification_type),
    INDEX idx_created_at (created_at)
);

-- RISK ASSESSMENTS TABLE
CREATE TABLE risk_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES authentication_sessions(id) ON DELETE CASCADE,
    biometric_risk FLOAT,
    behavioral_risk FLOAT,
    contextual_risk FLOAT,
    historical_risk FLOAT,
    total_risk_score FLOAT NOT NULL,
    risk_level VARCHAR(20), -- LOW, MEDIUM, HIGH, CRITICAL
    factors JSONB, -- {biometric, behavioral, contextual, historical}
    additional_verification_required BOOLEAN,
    recommended_action VARCHAR(100),
    analyst_review_id UUID,
    analyst_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    
    INDEX idx_session_id (session_id),
    INDEX idx_total_risk_score (total_risk_score),
    INDEX idx_created_at (created_at)
);

-- BEHAVIORAL BASELINES TABLE
CREATE TABLE behavioral_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    typing_profile JSONB, -- {speed, rhythm, error_rate}
    mouse_profile JSONB, -- {velocity, acceleration}
    navigation_profile JSONB, -- {dwell_time, scroll_frequency}
    touch_profile JSONB, -- {pressure, speed, area}
    baseline_samples INT DEFAULT 0,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE (user_id),
    INDEX idx_user_id (user_id)
);

-- REGISTERED DEVICES TABLE
CREATE TABLE registered_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_fingerprint VARCHAR(255) NOT NULL, -- hashed
    device_name VARCHAR(255),
    device_type VARCHAR(50), -- mobile, web, tablet
    os VARCHAR(50),
    os_version VARCHAR(50),
    browser VARCHAR(50),
    is_trusted BOOLEAN DEFAULT FALSE,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    revoked_at TIMESTAMP,
    
    UNIQUE (user_id, device_fingerprint),
    INDEX idx_user_id (user_id),
    INDEX idx_device_fingerprint (device_fingerprint),
    INDEX idx_created_at (created_at)
);

-- AUDIT LOGS TABLE (Time-series, partitioned)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action_type VARCHAR(50) NOT NULL, -- login, verify, challenge, deny, export, delete
    status VARCHAR(20) NOT NULL, -- success, failure, escalation
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    geolocation JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    retention_expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '90 days'),
    
    INDEX idx_user_id (user_id),
    INDEX idx_action_type (action_type),
    INDEX idx_timestamp (timestamp),
    INDEX idx_retention_expires_at (retention_expires_at)
) PARTITION BY RANGE (timestamp); -- Monthly partitions

-- Create monthly partitions for audit logs
CREATE TABLE audit_logs_2024_04 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-04-01') TO ('2024-05-01');
-- ... continue for future months
```

---

## Performance & Scalability Metrics

| Metric | Target | Current | Notes |
|--------|--------|---------|-------|
| Login Initiation | < 200ms | TBD | API response only |
| Risk Assessment | < 500ms | TBD | Per-user scoring |
| Deepfake Detection | < 2000ms | TBD | Adaptive, can be longer |
| Liveness Verification | < 3000ms | TBD | With challenges |
| Behavioral Analysis | < 500ms | TBD | Template comparison |
| Total Auth Time | < 3000ms | TBD | End-to-end |
| API Response (p95) | < 500ms | TBD | All endpoints |
| Database Query (p95) | < 100ms | TBD | Average query |
| Cache Hit Rate | > 80% | TBD | Session cache |
| System Uptime | 99.9% | TBD | SLA target |
| Deepfake Detection FAR | < 0.1% | TBD | False Acceptance |
| Deepfake Detection FRR | < 2% | TBD | False Rejection |
| Authentication Success Rate | > 99% | TBD | Legitimate users |
| Fraud Detection Rate | > 95% | TBD | Actual attacks |

