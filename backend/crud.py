from datetime import datetime
from sqlalchemy.orm import Session

from backend.models import BiometricProfile, User
from backend.services.behavioral_biometrics import BehavioralProfile
from backend.services.authentication import get_password_hash


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, email: str, password: str) -> User:
    hashed_password = get_password_hash(password)
    user = User(email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_biometric_profile(db: Session, user_id: str) -> BiometricProfile | None:
    return db.query(BiometricProfile).filter(BiometricProfile.user_id == user_id).order_by(BiometricProfile.created_at.desc()).first()


def save_biometric_profile(db: Session, user_id: str, profile_data: dict) -> BiometricProfile:
    record = get_biometric_profile(db, user_id)
    if record:
        record.profile_data = profile_data
    else:
        record = BiometricProfile(user_id=user_id, profile_data=profile_data)
        db.add(record)
    db.commit()
    db.refresh(record)
    return record


def rebuild_behavioral_profile(data: dict) -> BehavioralProfile:
    created_at = data.get("created_at")
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at)
        except ValueError:
            created_at = datetime.utcnow()

    return BehavioralProfile(
        user_id=data.get("user_id"),
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
