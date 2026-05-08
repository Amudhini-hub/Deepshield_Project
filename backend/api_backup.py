import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

try:
    import cv2
    import numpy as np

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from backend.config.config import get_config
from backend.crud import rebuild_behavioral_profile
from backend.schemas import (
    BaselineCreateRequest,
    BehavioralAnalysisRequest,
    BehavioralAnalysisResponse,
    BehavioralProfileResponse,
    RefreshTokenRequest,
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    TokenResponse,
    UserCreateRequest,
    UserResponse,
)
from backend.services.authentication import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    get_password_hash,
    verify_password,
)
from backend.services.behavioral_biometrics import BehavioralBiometricsEngine
from backend.services.risk_assessment import RiskAssessmentEngine
from backend.storage import store

# ML services - optional
try:
    from backend.services.deepfake_detection import DeepfakeDetector
    from backend.services.liveness_detection import LivenessDetector

    ML_AVAILABLE = True
except (ImportError, Exception):
    ML_AVAILABLE = False
    DeepfakeDetector = None
    LivenessDetector = None

logger = logging.getLogger(__name__)

config = get_config()
biometric_engine = BehavioralBiometricsEngine(config=config.get_config_dict())
risk_engine = RiskAssessmentEngine(config=config.get_config_dict())

# Initialize ML services only if available
if ML_AVAILABLE:
    try:
        deepfake_detector = DeepfakeDetector(config=config.get_config_dict())
        liveness_detector = LivenessDetector(config=config.get_config_dict())
    except Exception as e:
        logger.warning(f"Could not initialize ML services: {e}")
        ML_AVAILABLE = False
        deepfake_detector = None
        liveness_detector = None
else:
    deepfake_detector = None
    liveness_detector = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

api_router = APIRouter(tags=["deepshield"])


def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = store.get_user_by_id(int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@api_router.post(
    "/users/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(payload: UserCreateRequest) -> UserResponse:
    existing = store.get_user_by_email(payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user = store.create_user(payload.email, get_password_hash(payload.password))
    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
    )


@api_router.post(
    "/users/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    user = store.get_user_by_email(form_data.username)
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    config = get_config()
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=config.JWT_EXPIRATION_HOURS * 3600,
    )


@api_router.post(
    "/users/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh_access_token(payload: RefreshTokenRequest) -> TokenResponse:
    """Get new access token using refresh token"""
    decoded = decode_refresh_token(payload.refresh_token)
    if decoded is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decoded.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = store.get_user_by_id(int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    config = get_config()
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=config.JWT_EXPIRATION_HOURS * 3600,
    )


@api_router.get(
    "/users/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def get_authenticated_user(
    current_user=Depends(get_current_user),
) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
    )


@api_router.post(
    "/baseline",
    response_model=BehavioralProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_baseline(
    payload: BaselineCreateRequest,
    current_user=Depends(get_current_user),
) -> BehavioralProfileResponse:
    if payload.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user mismatch",
        )

    profile = biometric_engine.create_baseline(
        payload.user_id, [event.model_dump() for event in payload.events]
    )
    profile_data = profile.__dict__.copy()
    profile_data["created_at"] = profile.created_at.isoformat()
    store.save_biometric_profile(payload.user_id, profile_data)

    return BehavioralProfileResponse(
        user_id=profile.user_id,
        typing_speed=profile.typing_speed,
        typing_rhythm=profile.typing_rhythm,
        error_rate=profile.error_rate,
        mouse_velocity=profile.mouse_velocity,
        mouse_acceleration=profile.mouse_acceleration,
        click_interval=profile.click_interval,
        interaction_pattern=profile.interaction_pattern,
        created_at=profile.created_at.isoformat(),
        confidence=profile.confidence,
    )


@api_router.post(
    "/analyze",
    response_model=BehavioralAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze_behavior(
    payload: BehavioralAnalysisRequest,
    current_user=Depends(get_current_user),
) -> BehavioralAnalysisResponse:
    if payload.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user mismatch",
        )

    profile_data = store.get_biometric_profile(payload.user_id)
    if profile_data:
        baseline = rebuild_behavioral_profile(profile_data)
        biometric_engine.profiles[payload.user_id] = baseline

    analysis = biometric_engine.analyze_user_behavior(
        payload.user_id, [event.model_dump() for event in payload.events]
    )
    return BehavioralAnalysisResponse(
        user_id=payload.user_id,
        is_legitimate=analysis.is_legitimate,
        confidence=analysis.confidence,
        typing_score=analysis.typing_score,
        mouse_score=analysis.mouse_score,
        interaction_score=analysis.interaction_score,
        anomaly_flags=analysis.anomaly_flags,
        risk_level=analysis.risk_level,
        timestamp=datetime.utcnow().isoformat(),
    )


@api_router.post(
    "/risk",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_200_OK,
)
async def assess_risk(payload: RiskAssessmentRequest) -> RiskAssessmentResponse:
    result = risk_engine.assess_authentication_risk(
        user_id=payload.user_id,
        biometric_analysis=payload.biometric_analysis,
        behavioral_analysis=payload.behavioral_analysis,
        device_context=payload.context.device,
        location_context=payload.context.location,
        attempt_history=payload.context.attempt_history,
    )

    return RiskAssessmentResponse(
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        confidence=result.confidence,
        factors=result.factors,
        additional_verification_needed=result.additional_verification_needed,
        recommended_action=result.recommended_action,
        timestamp=result.timestamp.isoformat(),
    )


@api_router.post("/deepfake/detect", status_code=status.HTTP_200_OK)
async def detect_deepfake(
    file: UploadFile = File(...), current_user=Depends(get_current_user)
) -> dict:
    """Detect deepfakes in uploaded video"""
    if not CV2_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Deepfake detection service not available (OpenCV not installed)",
        )

    try:
        # Read video file
        video_data = await file.read()
        video_path = f"/tmp/{file.filename}"

        with open(video_path, "wb") as f:
            f.write(video_data)

        # Extract frames from video
        cap = cv2.VideoCapture(video_path)
        frames = []
        frame_count = 0

        while frame_count < 30:  # Limit to 30 frames for performance
            ret, frame = cap.read()
            if not ret:
                break
            # Resize for faster processing
            frame = cv2.resize(frame, (640, 480))
            frames.append(frame)
            frame_count += 1

        cap.release()

        if not frames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract frames from video",
            )

        # Run deepfake detection
        result = deepfake_detector.detect_from_frames(frames)

        # Clean up
        import os

        os.remove(video_path)

        return {
            "user_id": current_user.id,
            "is_deepfake": result.is_deepfake,
            "confidence": result.confidence,
            "detection_method": result.detection_method,
            "details": result.details,
            "anomalies": result.anomalies,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in deepfake detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@api_router.post("/liveness/detect", status_code=status.HTTP_200_OK)
async def detect_liveness(
    file: UploadFile = File(...), current_user=Depends(get_current_user)
) -> dict:
    """Detect liveness in uploaded video"""
    if not CV2_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Liveness detection service not available (OpenCV not installed)",
        )

    try:
        # Read video file
        video_data = await file.read()
        video_path = f"/tmp/{file.filename}"

        with open(video_path, "wb") as f:
            f.write(video_data)

        # Extract frames from video
        cap = cv2.VideoCapture(video_path)
        frames = []
        frame_count = 0

        while frame_count < 60:  # Limit to 60 frames for liveness
            ret, frame = cap.read()
            if not ret:
                break
            # Resize for faster processing
            frame = cv2.resize(frame, (640, 480))
            frames.append(frame)
            frame_count += 1

        cap.release()

        if not frames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract frames from video",
            )

        # Run liveness detection
        result = liveness_detector.detect_from_video_frames(frames)

        # Clean up
        import os

        os.remove(video_path)

        return {
            "user_id": current_user.id,
            "is_alive": result.is_alive,
            "confidence": result.confidence,
            "challenge_type": result.challenge_type,
            "details": result.details,
            "frame_count": result.frame_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in liveness detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@api_router.get("/health", status_code=status.HTTP_200_OK)
async def health() -> dict:
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
