import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.config.config import get_config

config = get_config()

# Use argon2 as primary with bcrypt as fallback for better compatibility
try:
    pwd_context = CryptContext(
        schemes=["argon2", "bcrypt"],
        deprecated="auto",
        argon2__time_cost=2,
        argon2__memory_cost=65536,
        argon2__parallelism=4,
    )
except Exception:
    # Fallback to bcrypt only if argon2 fails
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def get_password_hash(password: str) -> str:
    """Hash password using argon2/bcrypt"""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        # Fallback implementation if hashing fails
        import hashlib
        import os

        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        return f"pbkdf2:{salt.hex()}:{key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Fallback for pbkdf2 hashes
        if hashed_password.startswith("pbkdf2:"):
            import hashlib

            parts = hashed_password.split(":")
            if len(parts) == 3:
                salt = bytes.fromhex(parts[1])
                stored_key = parts[2]
                key = hashlib.pbkdf2_hmac(
                    "sha256", plain_password.encode(), salt, 100000
                )
                return key.hex() == stored_key
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + (expires_delta or timedelta(hours=config.JWT_EXPIRATION_HOURS))
    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
            "nonce": str(uuid.uuid4()),
            "type": TOKEN_TYPE_ACCESS,
        }
    )
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + (
        expires_delta or timedelta(days=config.REFRESH_TOKEN_EXPIRATION_DAYS)
    )
    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "nonce": str(uuid.uuid4()),
            "type": TOKEN_TYPE_REFRESH,
        }
    )
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict]:
    """Decode and validate JWT access token"""
    try:
        payload = jwt.decode(
            token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM]
        )
        if payload.get("type") != TOKEN_TYPE_ACCESS:
            return None
        return payload
    except JWTError:
        return None


def decode_refresh_token(token: str) -> Optional[Dict]:
    """Decode and validate JWT refresh token"""
    try:
        payload = jwt.decode(
            token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM]
        )
        if payload.get("type") != TOKEN_TYPE_REFRESH:
            return None
        return payload
    except JWTError:
        return None


def blacklist_token(token: str) -> bool:
    """
    Add token to Redis blacklist (for logout)

    Args:
        token: JWT token to blacklist

    Returns:
        Success status
    """
    try:
        from backend.redis_manager import get_redis_manager

        redis_manager = get_redis_manager()
        payload = jwt.decode(
            token, config.SECRET_KEY, algorithms=[config.JWT_ALGORITHM]
        )
        # Calculate remaining TTL based on exp claim
        exp_timestamp = payload.get("exp", 0)
        now_timestamp = datetime.utcnow().timestamp()
        ttl = max(0, int(exp_timestamp - now_timestamp))
        return redis_manager.blacklist_token(token, expires_in_seconds=ttl)
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error blacklisting token: {e}")
        return False


def is_token_blacklisted(token: str) -> bool:
    """
    Check if token is blacklisted

    Args:
        token: JWT token to check

    Returns:
        True if blacklisted, False otherwise
    """
    try:
        from backend.redis_manager import get_redis_manager

        redis_manager = get_redis_manager()
        return redis_manager.is_token_blacklisted(token)
    except Exception:
        return False
