"""
CRUD operations for DeepShield database models
Provides database abstraction layer for user and biometric data
"""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.models import AuditLog, BiometricProfile, User
from backend.services.authentication import get_password_hash, verify_password
from backend.services.behavioral_biometrics import BehavioralProfile

logger = logging.getLogger(__name__)


# ==================== USER CRUD OPERATIONS ====================


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email address"""
    try:
        return db.query(User).filter(User.email == email).first()
    except Exception as e:
        logger.error(f"Error getting user by email {email}: {e}")
        return None


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    try:
        return db.query(User).filter(User.id == user_id).first()
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return None


def create_user(db: Session, email: str, password: str) -> User:
    """Create new user with email and password"""
    try:
        hashed_password = get_password_hash(password)
        user = User(email=email, hashed_password=hashed_password, is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"User created: {email}")
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise


def update_user(
    db: Session,
    user_id: int,
    email: Optional[str] = None,
    password: Optional[str] = None,
) -> Optional[User]:
    """Update user email and/or password"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        if email:
            # Check if email already exists
            existing = (
                db.query(User).filter(User.email == email, User.id != user_id).first()
            )
            if existing:
                raise ValueError(f"Email {email} already in use")
            user.email = email

        if password:
            user.hashed_password = get_password_hash(password)

        db.commit()
        db.refresh(user)
        logger.info(f"User {user_id} updated")
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user {user_id}: {e}")
        raise


def deactivate_user(db: Session, user_id: int) -> bool:
    """Deactivate user account"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        user.is_active = False
        db.commit()
        logger.info(f"User {user_id} deactivated")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deactivating user {user_id}: {e}")
        raise


def activate_user(db: Session, user_id: int) -> bool:
    """Reactivate user account"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        user.is_active = True
        db.commit()
        logger.info(f"User {user_id} activated")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error activating user {user_id}: {e}")
        raise


def delete_user(db: Session, user_id: int) -> bool:
    """Hard delete user (permanent removal)"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # Delete associated biometric profiles
        db.query(BiometricProfile).filter(
            BiometricProfile.user_id == str(user_id)
        ).delete()

        # Delete associated audit logs
        db.query(AuditLog).filter(AuditLog.user_id == str(user_id)).delete()

        # Delete user
        db.delete(user)
        db.commit()
        logger.info(f"User {user_id} permanently deleted")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user {user_id}: {e}")
        raise


def list_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """List all users with pagination"""
    try:
        return db.query(User).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return []


def verify_user_password(db: Session, user_id: int, password: str) -> bool:
    """Verify user password"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        return verify_password(password, user.hashed_password)
    except Exception as e:
        logger.error(f"Error verifying password for user {user_id}: {e}")
        return False


# ==================== BIOMETRIC PROFILE CRUD ====================


def get_biometric_profile(db: Session, user_id: str) -> Optional[BiometricProfile]:
    """Get latest biometric profile for user"""
    try:
        return (
            db.query(BiometricProfile)
            .filter(BiometricProfile.user_id == user_id)
            .order_by(BiometricProfile.created_at.desc())
            .first()
        )
    except Exception as e:
        logger.error(f"Error getting biometric profile for {user_id}: {e}")
        return None


def get_biometric_profiles_history(
    db: Session, user_id: str, limit: int = 10
) -> List[BiometricProfile]:
    """Get biometric profile history for user"""
    try:
        return (
            db.query(BiometricProfile)
            .filter(BiometricProfile.user_id == user_id)
            .order_by(BiometricProfile.created_at.desc())
            .limit(limit)
            .all()
        )
    except Exception as e:
        logger.error(f"Error getting biometric history for {user_id}: {e}")
        return []


def save_biometric_profile(
    db: Session, user_id: str, profile_data: dict
) -> BiometricProfile:
    """Create or update biometric profile"""
    try:
        record = (
            db.query(BiometricProfile)
            .filter(BiometricProfile.user_id == user_id)
            .first()
        )

        if record:
            record.profile_data = profile_data
        else:
            record = BiometricProfile(user_id=user_id, profile_data=profile_data)
            db.add(record)

        db.commit()
        db.refresh(record)
        logger.info(f"Biometric profile saved for user: {user_id}")
        return record
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving biometric profile for {user_id}: {e}")
        raise


def delete_biometric_profile(db: Session, user_id: str) -> bool:
    """Delete biometric profile for user"""
    try:
        result = (
            db.query(BiometricProfile)
            .filter(BiometricProfile.user_id == user_id)
            .delete()
        )
        db.commit()
        logger.info(f"Biometric profile deleted for user: {user_id}")
        return result > 0
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting biometric profile for {user_id}: {e}")
        raise


# ==================== AUDIT LOG CRUD ====================


def create_audit_log(
    db: Session, user_id: str, event_type: str, payload: dict = None
) -> AuditLog:
    """Create audit log entry"""
    try:
        log = AuditLog(user_id=user_id, event_type=event_type, payload=payload or {})
        db.add(log)
        db.commit()
        db.refresh(log)
        logger.info(f"Audit log created: {event_type} for user {user_id}")
        return log
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating audit log: {e}")
        raise


def get_audit_logs(db: Session, user_id: str, limit: int = 100) -> List[AuditLog]:
    """Get audit logs for user"""
    try:
        return (
            db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
    except Exception as e:
        logger.error(f"Error getting audit logs for {user_id}: {e}")
        return []


def delete_audit_logs_older_than(db: Session, days: int) -> int:
    """Delete audit logs older than specified days (for cleanup)"""
    try:
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = db.query(AuditLog).filter(AuditLog.created_at < cutoff_date).delete()
        db.commit()
        logger.info(f"Deleted {result} audit logs older than {days} days")
        return result
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting old audit logs: {e}")
        raise


# ==================== HELPER FUNCTIONS ====================


def rebuild_behavioral_profile(data: dict) -> BehavioralProfile:
    """Convert database dict to BehavioralProfile object"""
    created_at = data.get("created_at")
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at)
        except ValueError:
            created_at = datetime.utcnow()

    return BehavioralProfile(
        user_id=data.get("user_id", ""),
        typing_speed=data.get("typing_speed", 0.0),
        typing_rhythm=data.get("typing_rhythm", 0.0),
        error_rate=data.get("error_rate", 0.0),
        mouse_velocity=data.get("mouse_velocity", 0.0),
        mouse_acceleration=data.get("mouse_acceleration", 0.0),
        click_interval=data.get("click_interval", 0.0),
        interaction_pattern=data.get("interaction_pattern", {}),
        created_at=created_at,
        confidence=data.get("confidence", 0.0),
    )
