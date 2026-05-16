"""
Configuration module for Deepshield Authentication Framework
Handles all configuration parameters and security settings
"""

import os
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class"""

    # Application settings
    APP_NAME = "Deepshield"
    APP_VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # Security settings
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    REFRESH_TOKEN_EXPIRATION_DAYS = 30

    # Biometric settings
    FACE_RECOGNITION_THRESHOLD = 0.6
    VOICE_RECOGNITION_THRESHOLD = 0.7
    LIVENESS_CONFIDENCE_THRESHOLD = 0.85
    DEEPFAKE_DETECTION_THRESHOLD = 0.8

    # Rate limiting
    MAX_AUTHENTICATION_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    MAX_FAILED_ATTEMPTS_PER_DAY = 10

    # Risk assessment settings
    RISK_SCORE_THRESHOLD = 70  # 0-100 scale
    RISK_LEVELS = {"LOW": (0, 30), "MEDIUM": (30, 70), "HIGH": (70, 100)}

    # Behavioral biometrics
    BEHAVIORAL_BASELINE_SAMPLES = 10
    TYPING_SPEED_THRESHOLD = 0.8
    MOUSE_MOVEMENT_THRESHOLD = 0.75
    INTERACTION_PATTERN_THRESHOLD = 0.8

    # Liveness detection
    LIVENESS_CHALLENGE_TYPES = [
        "eye_gaze",
        "head_movement",
        "blink_detection",
        "random_motion",
    ]
    LIVENESS_VIDEO_DURATION_SECONDS = 5
    LIVENESS_FPS = 30

    # Deepfake detection
    DEEPFAKE_DETECTION_MODELS = ["xception", "resnet", "efficientnet"]
    DEEPFAKE_FRAME_SAMPLING_INTERVAL = 5
    DEEPFAKE_MIN_FRAMES = 10

    # Anti-spoofing
    ANTI_SPOOFING_METHODS = [
        "texture_analysis",
        "frequency_analysis",
        "motion_detection",
    ]
    PRINT_ATTACK_THRESHOLD = 0.75
    REPLAY_ATTACK_THRESHOLD = 0.75

    # ── Database: explicit URL takes priority; otherwise build from components ──

    # Individual connection parts (legacy DB_* names kept for backward compat)
    DB_USER     = os.getenv("DB_USER",     "deepshield")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "deepshield_password")
    DB_HOST     = os.getenv("DB_HOST",     "localhost")
    DB_PORT     = os.getenv("DB_PORT",     "5432")
    DB_NAME     = os.getenv("DB_NAME",     "deepshield")

    # POSTGRES_* aliases (preferred going forward)
    POSTGRES_USER     = os.getenv("POSTGRES_USER",     DB_USER)
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", DB_PASSWORD)
    POSTGRES_HOST     = os.getenv("POSTGRES_HOST",     DB_HOST)
    POSTGRES_PORT     = int(os.getenv("POSTGRES_PORT", DB_PORT))
    POSTGRES_DB       = os.getenv("POSTGRES_DB",       DB_NAME)

    # Connection pool settings
    DB_POOL_SIZE    = int(os.getenv("DB_POOL_SIZE",    "10"))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))

    # Kept for backward compatibility with existing references to these names
    DATABASE_POOL_SIZE    = DB_POOL_SIZE
    DATABASE_MAX_OVERFLOW = DB_MAX_OVERFLOW

    DATABASE_ECHO = os.getenv("DATABASE_ECHO", "False").lower() == "true"

    # Build DATABASE_URL
    _explicit_url = os.getenv("DATABASE_URL")
    if _explicit_url:
        DATABASE_URL = _explicit_url
    else:
        USE_SQLITE_RUNTIME = (
            os.environ.get("USE_SQLITE_RUNTIME", "false").lower() == "true"
        )
        if USE_SQLITE_RUNTIME:
            DATABASE_URL = "sqlite:///./deepshield.db"
        else:
            DATABASE_URL = (
                f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
                f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
            )

    # Redis settings
    REDIS_HOST     = os.getenv("REDIS_HOST",     "localhost")
    REDIS_PORT     = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB       = int(os.getenv("REDIS_DB",   "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    REDIS_ENABLED  = os.getenv("REDIS_ENABLED",  "True").lower() == "true"

    # Redis cache settings
    REDIS_CACHE_TTL_SECONDS  = int(os.getenv("REDIS_CACHE_TTL_SECONDS",  "3600"))
    REDIS_SESSION_TTL_HOURS  = int(os.getenv("REDIS_SESSION_TTL_HOURS",  "24"))

    # API settings
    API_HOST    = os.getenv("API_HOST", "0.0.0.0")
    API_PORT    = int(os.getenv("API_PORT", "5000"))
    API_WORKERS = 4
    ENABLE_CORS = True

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE  = "logs/deepshield.log"

    # Privacy and compliance
    DATA_RETENTION_DAYS      = 90
    GDPR_COMPLIANT           = True
    ENCRYPTION_ALGORITHM     = "AES-256"
    BIOMETRIC_DATA_ENCRYPTION = True
    AUDIT_LOGGING_ENABLED    = True

    # Deployment settings
    ENVIRONMENT     = os.getenv("ENVIRONMENT", "development")
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Return configuration as dictionary"""
        return {
            key: getattr(cls, key)
            for key in dir(cls)
            if not key.startswith("_") and not callable(getattr(cls, key))
        }


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True
    TESTING = False
    JWT_EXPIRATION_HOURS = 48


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False
    TESTING = False
    JWT_EXPIRATION_HOURS = 12
    ENVIRONMENT = "production"


class TestingConfig(Config):
    """Testing configuration"""

    DEBUG = True
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"
    JWT_EXPIRATION_HOURS = 1


def get_config(env: str = None) -> Config:
    """Get appropriate config based on environment"""
    if env is None:
        env = os.getenv("ENVIRONMENT", "development")

    config_mapping = {
        "development": DevelopmentConfig,
        "production":  ProductionConfig,
        "testing":     TestingConfig,
    }

    return config_mapping.get(env, DevelopmentConfig)


def get_database_url() -> str:
    """
    Return a valid SQLAlchemy connection string.

    Priority:
      1. DATABASE_URL env var (used as-is after normalising postgres:// → postgresql://)
      2. Build from POSTGRES_* env vars
      3. Fall back to SQLite for local dev without Docker
    """
    url = os.getenv("DATABASE_URL", "")
    if not url:
        pg_user     = os.getenv("POSTGRES_USER",     os.getenv("DB_USER",     "deepshield"))
        pg_password = os.getenv("POSTGRES_PASSWORD", os.getenv("DB_PASSWORD", "changeme"))
        pg_host     = os.getenv("POSTGRES_HOST",     os.getenv("DB_HOST",     "localhost"))
        pg_port     = os.getenv("POSTGRES_PORT",     os.getenv("DB_PORT",     "5432"))
        pg_db       = os.getenv("POSTGRES_DB",       os.getenv("DB_NAME",     "deepshield"))

        if os.getenv("USE_SQLITE_RUNTIME", "false").lower() == "true":
            url = "sqlite:///./deepshield.db"
        else:
            url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"

    # SQLAlchemy 2.x requires "postgresql://" not the legacy "postgres://"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    return url
