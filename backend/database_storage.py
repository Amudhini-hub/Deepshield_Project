"""
SQLAlchemy-based Storage Layer for Production
Replaces in-memory storage with persistent database
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import BiometricProfile as BiometricProfileModel
from backend.models import User as UserModel

logger = logging.getLogger(__name__)


class DatabaseStore:
    """Production database storage using SQLAlchemy"""

    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session or SessionLocal()

    # ==================== User Operations ====================

    def create_user(self, email: str, hashed_password: str) -> UserModel:
        """Create a new user"""
        try:
            user = UserModel(
                email=email,
                hashed_password=hashed_password,
                created_at=datetime.utcnow(),
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"User created: {email}")
            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user: {e}")
            raise

    def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """Get user by email"""
        try:
            return self.db.query(UserModel).filter(UserModel.email == email).first()
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[UserModel]:
        """Get user by ID"""
        try:
            return self.db.query(UserModel).filter(UserModel.id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None

    def get_all_users(self) -> list:
        """Get all users"""
        try:
            return self.db.query(UserModel).all()
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []

    def update_user(self, user_id: int, **kwargs) -> Optional[UserModel]:
        """Update user fields"""
        try:
            user = self.get_user_by_id(user_id)
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                self.db.commit()
                self.db.refresh(user)
                logger.info(f"User updated: {user_id}")
                return user
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user: {e}")
            return None

    def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        try:
            user = self.get_user_by_id(user_id)
            if user:
                self.db.delete(user)
                self.db.commit()
                logger.info(f"User deleted: {user_id}")
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting user: {e}")
            return False

    # ==================== Biometric Profile Operations ====================

    def create_biometric_profile(
        self, user_id: str, profile_data: dict
    ) -> BiometricProfileModel:
        """Create a new biometric profile"""
        try:
            profile = BiometricProfileModel(
                user_id=user_id, profile_data=profile_data, created_at=datetime.utcnow()
            )
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
            logger.info(f"Biometric profile created for user: {user_id}")
            return profile
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating biometric profile: {e}")
            raise

    def get_biometric_profile(self, user_id: str) -> Optional[dict]:
        """Get latest biometric profile for user"""
        try:
            profile = (
                self.db.query(BiometricProfileModel)
                .filter(BiometricProfileModel.user_id == user_id)
                .order_by(BiometricProfileModel.created_at.desc())
                .first()
            )
            if profile:
                return profile.profile_data
            return None
        except Exception as e:
            logger.error(f"Error getting biometric profile: {e}")
            return None

    def save_biometric_profile(self, user_id: str, profile_data: dict) -> dict:
        """Save (update or create) biometric profile"""
        try:
            # Check if profile exists
            existing = (
                self.db.query(BiometricProfileModel)
                .filter(BiometricProfileModel.user_id == user_id)
                .first()
            )

            if existing:
                # Update existing
                existing.profile_data = profile_data
                self.db.commit()
                logger.info(f"Biometric profile updated for user: {user_id}")
            else:
                # Create new
                self.create_biometric_profile(user_id, profile_data)

            return profile_data
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving biometric profile: {e}")
            raise

    def get_user_biometric_history(self, user_id: str, limit: int = 10) -> list:
        """Get biometric profile history for a user"""
        try:
            profiles = (
                self.db.query(BiometricProfileModel)
                .filter(BiometricProfileModel.user_id == user_id)
                .order_by(BiometricProfileModel.created_at.desc())
                .limit(limit)
                .all()
            )
            return [p.profile_data for p in profiles]
        except Exception as e:
            logger.error(f"Error getting biometric history: {e}")
            return []

    def delete_biometric_profiles(self, user_id: str) -> bool:
        """Delete all biometric profiles for a user"""
        try:
            self.db.query(BiometricProfileModel).filter(
                BiometricProfileModel.user_id == user_id
            ).delete()
            self.db.commit()
            logger.info(f"Biometric profiles deleted for user: {user_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting biometric profiles: {e}")
            return False

    def close(self):
        """Close database session"""
        self.db.close()


# Global database store instance for backward compatibility
db_store = DatabaseStore()
