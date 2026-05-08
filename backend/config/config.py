"""
Configuration module for Deepshield Authentication Framework
Handles all configuration parameters and security settings
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any

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
    RISK_LEVELS = {
        "LOW": (0, 30),
        "MEDIUM": (30, 70),
        "HIGH": (70, 100)
    }
    
    # Behavioral biometrics
    BEHAVIORAL_BASELINE_SAMPLES = 10
    TYPING_SPEED_THRESHOLD = 0.8
    MOUSE_MOVEMENT_THRESHOLD = 0.75
    INTERACTION_PATTERN_THRESHOLD = 0.8
    
    # Liveness detection
    LIVENESS_CHALLENGE_TYPES = ["eye_gaze", "head_movement", "blink_detection", "random_motion"]
    LIVENESS_VIDEO_DURATION_SECONDS = 5
    LIVENESS_FPS = 30
    
    # Deepfake detection
    DEEPFAKE_DETECTION_MODELS = ["xception", "resnet", "efficientnet"]
    DEEPFAKE_FRAME_SAMPLING_INTERVAL = 5
    DEEPFAKE_MIN_FRAMES = 10
    
    # Anti-spoofing
    ANTI_SPOOFING_METHODS = ["texture_analysis", "frequency_analysis", "motion_detection"]
    PRINT_ATTACK_THRESHOLD = 0.75
    REPLAY_ATTACK_THRESHOLD = 0.75
    
    # Database settings
    DB_USER = os.getenv("DB_USER", "deepshield")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "deepshield_password")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "deepshield")
    
    # Build DATABASE_URL from components if not provided
    _custom_db_url = os.getenv("DATABASE_URL")
    if _custom_db_url:
        DATABASE_URL = _custom_db_url
    else:
        # Runtime database selection - only if DATABASE_URL not explicitly set
        USE_SQLITE_RUNTIME = os.environ.get("USE_SQLITE_RUNTIME", "false").lower() == "true"
        if USE_SQLITE_RUNTIME:
            DATABASE_URL = "sqlite:///./deepshield.db"
        else:
            DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "20"))
    DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "40"))
    DATABASE_ECHO = os.getenv("DATABASE_ECHO", "False").lower() == "true"
    
    # API settings
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "5000"))
    API_WORKERS = 4
    ENABLE_CORS = True
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = "logs/deepshield.log"
    
    # Privacy and compliance
    DATA_RETENTION_DAYS = 90
    GDPR_COMPLIANT = True
    ENCRYPTION_ALGORITHM = "AES-256"
    BIOMETRIC_DATA_ENCRYPTION = True
    AUDIT_LOGGING_ENABLED = True
    
    # Deployment settings
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Return configuration as dictionary"""
        return {
            key: getattr(cls, key) for key in dir(cls)
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
        "production": ProductionConfig,
        "testing": TestingConfig
    }
    
    return config_mapping.get(env, DevelopmentConfig)
