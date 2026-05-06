"""In-memory storage for Deepshield backend"""

from typing import Dict, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class User:
    id: int
    email: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class InMemoryStore:
    def __init__(self):
        self.users: Dict[int, User] = {}
        self.users_by_email: Dict[str, User] = {}
        self.biometric_profiles: Dict[str, dict] = {}
        self.next_user_id: int = 1

    def create_user(self, email: str, hashed_password: str) -> User:
        user = User(
            id=self.next_user_id,
            email=email,
            hashed_password=hashed_password,
        )
        self.next_user_id += 1
        self.users[user.id] = user
        self.users_by_email[email] = user
        return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.users_by_email.get(email)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.users.get(user_id)

    def save_biometric_profile(self, user_id: str, profile_data: dict) -> dict:
        self.biometric_profiles[user_id] = profile_data
        return profile_data

    def get_biometric_profile(self, user_id: str) -> Optional[dict]:
        return self.biometric_profiles.get(user_id)


# Global store instance
store = InMemoryStore()
