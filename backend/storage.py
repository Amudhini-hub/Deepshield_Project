"""Database storage layer for Deepshield backend using SQLAlchemy"""

from typing import Optional
import logging

from backend.database import SessionLocal
from backend.models import User as UserModel, BiometricProfile as BiometricProfileModel

logger = logging.getLogger(__name__)


class DatabaseStore:
    """Database-backed storage using SQLAlchemy ORM"""

    def __init__(self):
        self.SessionLocal = SessionLocal

    def create_user(self, email: str, hashed_password: str) -> UserModel:
        """Create a new user in the database"""
        db = self.SessionLocal()
        try:
            user = UserModel(email=email, hashed_password=hashed_password, is_active=True)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"User created: {email}")
            return user
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user: {e}")
            raise
        finally:
            db.close()

    def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """Get user by email"""
        db = self.SessionLocal()
        try:
            user = db.query(UserModel).filter(UserModel.email == email).first()
            return user
        finally:
            db.close()

    def get_user_by_id(self, user_id: int) -> Optional[UserModel]:
        """Get user by ID"""
        db = self.SessionLocal()
        try:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            return user
        finally:
            db.close()

    def save_biometric_profile(self, user_id: str, profile_data: dict) -> BiometricProfileModel:
        """Save or update biometric profile"""
        db = self.SessionLocal()
        try:
            profile = db.query(BiometricProfileModel).filter(
                BiometricProfileModel.user_id == user_id
            ).first()
            
            if profile:
                profile.profile_data = profile_data
            else:
                profile = BiometricProfileModel(user_id=user_id, profile_data=profile_data)
                db.add(profile)
            
            db.commit()
            db.refresh(profile)
            logger.info(f"Biometric profile saved for user: {user_id}")
            return profile
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving biometric profile: {e}")
            raise
        finally:
            db.close()

    def get_biometric_profile(self, user_id: str) -> Optional[dict]:
        """Get latest biometric profile for user"""
        db = self.SessionLocal()
        try:
            profile = db.query(BiometricProfileModel).filter(
                BiometricProfileModel.user_id == user_id
            ).order_by(BiometricProfileModel.created_at.desc()).first()
            
            return profile.profile_data if profile else None
        finally:
            db.close()


# Global store instance
store = DatabaseStore()
