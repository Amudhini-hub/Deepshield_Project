from typing import Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


# ==================== Error Response Models ====================

class ErrorResponse(BaseModel):
    """Standard error response"""
    status_code: int
    detail: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    path: Optional[str] = None


class ValidationErrorDetail(BaseModel):
    """Validation error detail"""
    field: str
    message: str


class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    status_code: int = 422
    detail: str = "Validation error"
    errors: List[ValidationErrorDetail]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ==================== Behavioral Models ====================

class BehavioralEvent(BaseModel):
    """Single behavioral event (keyboard, mouse, interaction)"""
    type: str  # 'keystroke', 'keypress', 'mouse_move', 'mousemove', 'click', 'scroll'
    timestamp: float
    x: Optional[float] = None
    y: Optional[float] = None
    is_error: Optional[bool] = False
    metadata: Optional[Dict[str, str]] = None
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        allowed = {
            'keystroke', 'keypress',
            'mouse_move', 'mousemove',
            'click', 'scroll', 'focus', 'blur'
        }
        if v not in allowed:
            raise ValueError(f'type must be one of {allowed}')
        return v


class BaselineCreateRequest(BaseModel):
    """Create behavioral baseline from events"""
    user_id: str
    events: List[BehavioralEvent] = Field(..., min_items=1, max_items=1000)
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not v or len(v) == 0:
            raise ValueError('user_id cannot be empty')
        return v


class BehavioralAnalysisRequest(BaseModel):
    """Request behavioral analysis"""
    user_id: str
    events: List[BehavioralEvent] = Field(..., min_items=1, max_items=1000)
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not v or len(v) == 0:
            raise ValueError('user_id cannot be empty')
        return v


class BehavioralProfileResponse(BaseModel):
    """User behavioral profile"""
    user_id: str
    typing_speed: float
    typing_rhythm: float
    error_rate: float
    mouse_velocity: float
    mouse_acceleration: float
    click_interval: float
    interaction_pattern: Dict[str, object]
    created_at: str
    confidence: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "typing_speed": 65.5,
                "typing_rhythm": 0.85,
                "error_rate": 0.03,
                "mouse_velocity": 150.2,
                "mouse_acceleration": 45.1,
                "click_interval": 0.25,
                "interaction_pattern": {"dominant_hand": "right"},
                "created_at": "2026-05-06T10:30:00",
                "confidence": 0.92
            }
        }


class BehavioralAnalysisResponse(BaseModel):
    """Result of behavioral analysis"""
    user_id: str
    is_legitimate: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    typing_score: float = Field(..., ge=0.0, le=1.0)
    mouse_score: float = Field(..., ge=0.0, le=1.0)
    interaction_score: float = Field(..., ge=0.0, le=1.0)
    anomaly_flags: List[str]
    risk_level: str  # LOW, MEDIUM, HIGH
    timestamp: str


class RiskContext(BaseModel):
    """Context for risk assessment"""
    device: Dict[str, Optional[object]] = Field(default_factory=dict)
    location: Dict[str, Optional[object]] = Field(default_factory=dict)
    attempt_history: Dict[str, Optional[object]] = Field(default_factory=dict)


class RiskAssessmentRequest(BaseModel):
    """Request risk assessment"""
    user_id: str
    biometric_analysis: Dict[str, object]
    behavioral_analysis: Dict[str, object]
    context: RiskContext


class RiskAssessmentResponse(BaseModel):
    """Risk assessment result"""
    risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_level: str  # LOW, MEDIUM, HIGH
    confidence: float = Field(..., ge=0.0, le=1.0)
    factors: Dict[str, float]
    additional_verification_needed: bool
    recommended_action: str
    timestamp: str


# ==================== User Authentication Models ====================

class UserCreateRequest(BaseModel):
    """User registration request"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 chars)")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        # Password must contain uppercase, lowercase, digit
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain uppercase, lowercase, and digit')
        return v


class UserResponse(BaseModel):
    """User response (public data only)"""
    id: int
    email: EmailStr
    is_active: bool
    created_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "is_active": True,
                "created_at": "2026-05-06T10:30:00"
            }
        }


class UserUpdateRequest(BaseModel):
    """Update user profile"""
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if v is None:
            return v
        # Password must contain uppercase, lowercase, digit
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain uppercase, lowercase, and digit')
        return v


class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until token expires
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGc...",
                "refresh_token": "eyJhbGc...",
                "token_type": "bearer",
                "expires_in": 86400
            }
        }


class RefreshTokenRequest(BaseModel):
    """Request new access token using refresh token"""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request"""
    refresh_token: Optional[str] = None

