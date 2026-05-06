# DeepShield - Advanced Security API

DeepShield is a comprehensive security API platform that provides behavioral biometrics, deepfake detection, and liveness detection capabilities. This system implements production-ready monitoring, alerting, and CI/CD pipelines.

## Features

- **Behavioral Biometrics**: Analyze user behavior patterns for security assessment
- **Deepfake Detection**: ML-powered detection of synthetic media
- **Liveness Detection**: Real-time verification of user presence
- **JWT Authentication**: Secure token-based authentication
- **Comprehensive Monitoring**: System metrics, API performance, and security monitoring
- **Alerting System**: Configurable alerts with email/Slack/Telegram notifications
- **Load Testing**: Built-in performance testing tools
- **CI/CD Pipeline**: Automated testing, security scanning, and deployment

## Quick Start

### Prerequisites

- Python 3.9+
- SQLite (default) or PostgreSQL
- OpenCV-compatible system

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd deepshield
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python init_db.py
```

4. Train ML models (optional):
```bash
python train_ml_models.py
```

5. Start the server:
```bash
python -m uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh

### User Management
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update user profile

### Security Services
- `POST /api/v1/behavioral/baseline` - Establish behavioral baseline
- `POST /api/v1/behavioral/analyze` - Analyze behavioral data
- `POST /api/v1/deepfake/detect` - Deepfake detection
- `POST /api/v1/liveness/check` - Liveness verification
- `POST /api/v1/risk/assessment` - Risk assessment

### Monitoring & Metrics
- `GET /health` - Health check
- `GET /metrics/health` - System health metrics
- `GET /metrics/api` - API performance metrics
- `GET /metrics/security` - Security event metrics
- `GET /metrics` - All metrics combined

### Alerting
- `GET /alerts/active` - Active alerts
- `GET /alerts/history` - Alert history
- `POST /alerts/resolve/{rule_name}` - Resolve alert
- `GET /alerts/rules` - Alert rules configuration

## Monitoring & Alerting

### System Monitoring

The application includes comprehensive monitoring:

- **System Metrics**: CPU, memory, disk usage, network connections
- **API Metrics**: Response times, error rates, endpoint performance
- **Security Metrics**: Authentication failures, risk events

View metrics via the `/metrics` endpoints or access the monitoring dashboard.

### Alerting System

Configurable alerts for:
- High CPU/memory usage
- Low disk space
- Slow API responses
- High error rates
- Security events

#### Alert Configuration

Create `alerts_config.json`:

```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "from_email": "alerts@deepshield.com",
    "to_emails": ["admin@company.com"]
  },
  "slack_webhook": "https://hooks.slack.com/services/...",
  "telegram": {
    "bot_token": "your-bot-token",
    "chat_id": "your-chat-id"
  }
}
```

#### Default Alert Rules

- `high_cpu`: CPU > 90%
- `high_memory`: Memory > 85%
- `low_disk_space`: Disk > 90%
- `high_error_rate`: API errors > 10%
- `slow_response_time`: Avg response > 2000ms
- `high_risk_events`: Risk events > 5/hour

## Load Testing

Run comprehensive load tests:

```bash
# Basic load test
python load_test.py --url http://localhost:8000 --users 10 --duration 60

# Save results to file
python load_test.py --url http://localhost:8000 --users 20 --duration 120 --output results.json
```

The load tester includes:
- Health endpoint stress testing
- API endpoint load testing
- User registration testing
- Concurrent user simulation

## Development

### Project Structure

```
deepshield/
├── backend/
│   ├── api/           # API route handlers
│   ├── models/        # Database models
│   ├── services/      # Business logic
│   ├── config/        # Configuration
│   ├── monitoring.py  # System monitoring
│   ├── alerting.py    # Alert management
│   └── main.py        # FastAPI application
├── ml_models/         # ML model storage
├── tests/            # Test suites
├── metrics/          # Monitoring data
├── logs/             # Application logs
└── docs/             # Documentation
```

### Running Tests

```bash
# Unit tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=backend --cov-report=html

# Load testing
python load_test.py
```

### Code Quality

```bash
# Linting
flake8 backend/ tests/

# Code formatting
black backend/ tests/
isort backend/ tests/
```

## Deployment

### Docker

Build and run with Docker:

```bash
# Build image
docker build -t deepshield .

# Run container
docker run -p 8000:8000 deepshield
```

### Docker Compose

For development with dependencies:

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f deepshield
```

### Production Deployment

The CI/CD pipeline supports:
- Automated testing across Python versions
- Security scanning (Bandit, Safety)
- Load testing validation
- Docker image building
- AWS ECR/ECS deployment

## Configuration

### Environment Variables

```bash
# Database
USE_SQLITE_RUNTIME=true  # Use SQLite instead of PostgreSQL
DATABASE_URL=sqlite:///./deepshield.db

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret

# Application
DEBUG=false
APP_NAME=DeepShield
APP_VERSION=1.0.0

# CORS
ENABLE_CORS=true
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Alert Configuration

See `alerts_config.json` example above for notification setup.

## Security Considerations

- JWT tokens with configurable expiration
- Password hashing with bcrypt
- Rate limiting and request validation
- Comprehensive logging and monitoring
- Security event tracking
- ML model validation and updates

## Performance Optimization

- Lightweight health checks
- Efficient database queries
- Background metric collection
- Configurable alert thresholds
- Load balancing ready
- Caching support (Redis)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Ensure CI/CD passes
5. Submit pull request

## License

[Your License Here]

## Support

For support and questions:
- Documentation: [Link to docs]
- Issues: [GitHub Issues]
- Email: support@deepshield.com