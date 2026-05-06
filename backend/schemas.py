from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class BehavioralEvent(BaseModel):
    type: str
    timestamp: float
    x: Optional[float] = None
    y: Optional[float] = None
    is_error: Optional[bool] = False
    metadata: Optional[Dict[str, str]] = None


class BaselineCreateRequest(BaseModel):
    user_id: str
    events: List[BehavioralEvent]


class BehavioralAnalysisRequest(BaseModel):
    user_id: str
    events: List[BehavioralEvent]


class RiskContext(BaseModel):
    device: Dict[str, Optional[object]] = Field(default_factory=dict)
    location: Dict[str, Optional[object]] = Field(default_factory=dict)
    attempt_history: Dict[str, Optional[object]] = Field(default_factory=dict)


class RiskAssessmentRequest(BaseModel):
    user_id: str
    biometric_analysis: Dict[str, object]
    behavioral_analysis: Dict[str, object]
    context: RiskContext


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class BehavioralProfileResponse(BaseModel):
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


class BehavioralAnalysisResponse(BaseModel):
    user_id: str
    is_legitimate: bool
    confidence: float
    typing_score: float
    mouse_score: float
    interaction_score: float
    anomaly_flags: List[str]
    risk_level: str
    timestamp: str


class RiskAssessmentResponse(BaseModel):
    risk_score: float
    risk_level: str
    confidence: float
    factors: Dict[str, float]
    additional_verification_needed: bool
    recommended_action: str
    timestamp: str
