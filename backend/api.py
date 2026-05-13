"""
DeepShield API Router
Complete REST API implementation for authentication, biometrics, and risk assessment
"""

import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

try:
    import cv2
    import numpy as np

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

import backend.crud as crud
from backend.config.config import get_config
from backend.crud import rebuild_behavioral_profile
from backend.database import get_db
from backend.models import User
from backend.schemas import (
    BaselineCreateRequest,
    BehavioralAnalysisRequest,
    BehavioralAnalysisResponse,
    BehavioralProfileResponse,
    LogoutRequest,
    RefreshTokenRequest,
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    TokenResponse,
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from backend.services.authentication import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    verify_password,
)
from backend.services.behavioral_biometrics import BehavioralBiometricsEngine
from backend.services.risk_assessment import RiskAssessmentEngine

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
deepfake_detector = None
liveness_detector = None
if ML_AVAILABLE:
    try:
        deepfake_detector = DeepfakeDetector(config=config.get_config_dict())
        liveness_detector = LivenessDetector(config=config.get_config_dict())
        logger.info("ML services initialized successfully")
    except Exception as e:
        logger.warning(f"Could not initialize ML services: {e}")
        ML_AVAILABLE = False

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login", auto_error=False)
api_router = APIRouter(tags=["deepshield"])

# Token blacklist for logout (in production, use Redis)
TOKEN_BLACKLIST = set()


# ==================== DEPENDENCY INJECTION ====================


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Get currently authenticated user from token"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if token is blacklisted (Redis or in-memory fallback)
    from backend.services.authentication import is_token_blacklisted
    if is_token_blacklisted(token) or token in TOKEN_BLACKLIST:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = crud.get_user(db, int(user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# ==================== USER AUTHENTICATION ENDPOINTS ====================


@api_router.post(
    "/users/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register_user(
    payload: UserCreateRequest, db: Session = Depends(get_db)
) -> UserResponse:
    """Register a new user with email and password."""
    try:
        existing = crud.get_user_by_email(db, payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email {payload.email} is already registered",
            )

        user = crud.create_user(db, payload.email, payload.password)

        # Log the registration
        crud.create_audit_log(
            db,
            str(user.id),
            "USER_REGISTERED",
            {"email": user.email, "timestamp": datetime.utcnow().isoformat()},
        )

        logger.info(f"User registered: {payload.email}")
        return UserResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registering user",
        )


@api_router.post(
    "/users/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login user",
)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> TokenResponse:
    """Authenticate user and return JWT tokens."""
    try:
        user = crud.get_user_by_email(db, form_data.username)
        if user is None or not verify_password(
            form_data.password, user.hashed_password
        ):
            logger.warning(f"Failed login attempt for {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated",
            )

        # Create tokens
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        # Log the login
        crud.create_audit_log(
            db, str(user.id), "USER_LOGIN", {"timestamp": datetime.utcnow().isoformat()}
        )

        logger.info(f"User logged in: {user.email}")
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=config.JWT_EXPIRATION_HOURS * 3600,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during authentication",
        )


@api_router.post(
    "/users/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
async def refresh_access_token(
    payload: RefreshTokenRequest, db: Session = Depends(get_db)
) -> TokenResponse:
    """Get a new access token using a valid refresh token."""
    try:
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

        user = crud.get_user(db, int(user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated",
            )

        # Create new tokens
        access_token = create_access_token({"sub": str(user.id)})
        new_refresh_token = create_refresh_token({"sub": str(user.id)})

        logger.info(f"Token refreshed for user: {user.id}")
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=config.JWT_EXPIRATION_HOURS * 3600,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refreshing token",
        )


@api_router.post(
    "/users/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout user",
)
async def logout_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
) -> dict:
    """Logout user by invalidating token."""
    try:
        # Blacklist the token using Redis
        if token:
            from backend.services.authentication import blacklist_token
            blacklist_token(token)
            # Also add to in-memory fallback
            TOKEN_BLACKLIST.add(token)
        
        crud.create_audit_log(
            db,
            str(current_user.id),
            "USER_LOGOUT",
            {"timestamp": datetime.utcnow().isoformat()},
        )

        logger.info(f"User logged out: {current_user.email}")
        return {
            "status": "success",
            "message": "User logged out successfully",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error logging out user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during logout",
        )


@api_router.get(
    "/users/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_authenticated_user(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get profile information of currently authenticated user."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
    )


@api_router.put(
    "/users/profile",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user profile",
)
async def update_user_profile(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Update user email and/or password."""
    try:
        user = crud.update_user(
            db, current_user.id, email=payload.email, password=payload.password
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        crud.create_audit_log(
            db,
            str(user.id),
            "USER_UPDATED",
            {
                "fields": [k for k, v in payload.model_dump().items() if v],
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        logger.info(f"User profile updated: {user.email}")
        return UserResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating profile",
        )


# ==================== BEHAVIORAL BIOMETRICS ENDPOINTS ====================


@api_router.post(
    "/baseline",
    response_model=BehavioralProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create behavioral baseline",
)
async def create_baseline(
    payload: BaselineCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BehavioralProfileResponse:
    """Create behavioral baseline from user events."""
    try:
        if payload.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create baseline for another user",
            )

        profile = biometric_engine.create_baseline(
            payload.user_id, [event.model_dump() for event in payload.events]
        )
        profile_data = profile.__dict__.copy()
        profile_data["created_at"] = profile.created_at.isoformat()

        crud.save_biometric_profile(db, payload.user_id, profile_data)

        crud.create_audit_log(
            db,
            payload.user_id,
            "BASELINE_CREATED",
            {
                "confidence": profile.confidence,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        logger.info(f"Behavioral baseline created for user: {payload.user_id}")
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating baseline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating baseline",
        )


@api_router.post(
    "/analyze",
    response_model=BehavioralAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze user behavior",
)
async def analyze_behavior(
    payload: BehavioralAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BehavioralAnalysisResponse:
    """Analyze user behavior against their baseline."""
    try:
        if payload.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot analyze behavior for another user",
            )

        profile_data = crud.get_biometric_profile(db, payload.user_id)
        if profile_data and profile_data.profile_data:
            baseline = rebuild_behavioral_profile(profile_data.profile_data)
            biometric_engine.profiles[payload.user_id] = baseline

        analysis = biometric_engine.analyze_user_behavior(
            payload.user_id, [event.model_dump() for event in payload.events]
        )

        logger.info(f"Behavioral analysis completed for user: {payload.user_id}")
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing behavior: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error analyzing behavior",
        )


# ==================== RISK ASSESSMENT ENDPOINTS ====================


@api_router.post(
    "/risk",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Assess authentication risk",
)
async def assess_risk(payload: RiskAssessmentRequest) -> RiskAssessmentResponse:
    """Assess risk based on biometric and behavioral analysis."""
    try:
        result = risk_engine.assess_authentication_risk(
            user_id=payload.user_id,
            biometric_analysis=payload.biometric_analysis,
            behavioral_analysis=payload.behavioral_analysis,
            device_context=payload.context.device,
            location_context=payload.context.location,
            attempt_history=payload.context.attempt_history,
        )

        logger.info(f"Risk assessment completed for user: {payload.user_id}")
        return RiskAssessmentResponse(
            risk_score=result.risk_score,
            risk_level=result.risk_level,
            confidence=result.confidence,
            factors=result.factors,
            additional_verification_needed=result.additional_verification_needed,
            recommended_action=result.recommended_action,
            timestamp=result.timestamp.isoformat(),
        )
    except Exception as e:
        logger.error(f"Error assessing risk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error assessing risk",
        )


# ==================== ML DETECTION ENDPOINTS ====================


@api_router.post(
    "/deepfake/detect",
    status_code=status.HTTP_200_OK,
    summary="Detect deepfakes in video",
)
async def detect_deepfake(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Detect deepfakes in uploaded video file."""
    if not CV2_AVAILABLE or not ML_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Deepfake detection service not available",
        )

    video_path = None
    try:
        video_data = await file.read()
        if not video_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty video file",
            )

        video_path = f"/tmp/{file.filename}"
        with open(video_path, "wb") as f:
            f.write(video_data)

        cap = cv2.VideoCapture(video_path)
        frames = []
        frame_count = 0

        while frame_count < 30:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.resize(frame, (640, 480))
            frames.append(frame)
            frame_count += 1

        cap.release()

        if not frames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract frames from video",
            )

        result = deepfake_detector.detect_from_frames(frames)

        crud.create_audit_log(
            db,
            str(current_user.id),
            "DEEPFAKE_DETECTION",
            {
                "is_deepfake": result.is_deepfake,
                "confidence": result.confidence,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        logger.info(
            f"Deepfake detection for user {current_user.id}: {result.is_deepfake}"
        )
        return {
            "user_id": current_user.id,
            "is_deepfake": result.is_deepfake,
            "confidence": result.confidence,
            "detection_method": result.detection_method,
            "details": result.details,
            "anomalies": result.anomalies,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in deepfake detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deepfake detection failed: {str(e)}",
        )
    finally:
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception as e:
                logger.warning(f"Failed to clean up video file: {e}")


@api_router.post(
    "/liveness/detect",
    status_code=status.HTTP_200_OK,
    summary="Detect liveness in video",
)
async def detect_liveness(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Detect liveness in uploaded video file."""
    if not CV2_AVAILABLE or not ML_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Liveness detection service not available",
        )

    video_path = None
    try:
        video_data = await file.read()
        if not video_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty video file",
            )

        video_path = f"/tmp/{file.filename}"
        with open(video_path, "wb") as f:
            f.write(video_data)

        cap = cv2.VideoCapture(video_path)
        frames = []
        frame_count = 0

        while frame_count < 60:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.resize(frame, (640, 480))
            frames.append(frame)
            frame_count += 1

        cap.release()

        if not frames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract frames from video",
            )

        result = liveness_detector.detect_from_video_frames(frames)

        crud.create_audit_log(
            db,
            str(current_user.id),
            "LIVENESS_DETECTION",
            {
                "is_alive": result.is_alive,
                "confidence": result.confidence,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        logger.info(f"Liveness detection for user {current_user.id}: {result.is_alive}")
        return {
            "user_id": current_user.id,
            "is_alive": result.is_alive,
            "confidence": result.confidence,
            "challenge_type": result.challenge_type,
            "details": result.details,
            "frame_count": result.frame_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in liveness detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Liveness detection failed: {str(e)}",
        )
    finally:
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception as e:
                logger.warning(f"Failed to clean up video file: {e}")


# ==================== HEALTH & STATUS ENDPOINTS ====================


@api_router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
)
async def health() -> dict:
    """API health check endpoint."""
    return {
        "status": "ok",
        "service": "deepshield",
        "version": config.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "ml_services": "available" if ML_AVAILABLE else "unavailable",
    }


@api_router.get(
    "/health/status",
    status_code=status.HTTP_200_OK,
    summary="Detailed health status",
)
async def detailed_health_status() -> dict:
    """Get detailed health status of all services."""
    from backend.redis_manager import get_redis_manager
    
    redis_manager = get_redis_manager()
    redis_stats = redis_manager.get_redis_stats()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "service": "deepshield",
        "version": config.APP_VERSION,
        "components": {
            "api": {"status": "healthy"},
            "database": {"status": "healthy" if health_check() else "unhealthy"},
            "redis": redis_stats,
            "ml_services": "available" if ML_AVAILABLE else "unavailable",
        },
        "environment": config.ENVIRONMENT,
        "debug_mode": config.DEBUG,
    }


@api_router.get(
    "/metrics/redis",
    status_code=status.HTTP_200_OK,
    summary="Redis metrics",
    tags=["monitoring"]
)
async def redis_metrics(current_user: User = Depends(get_current_user)) -> dict:
    """Get Redis server metrics (requires authentication)."""
    from backend.redis_manager import get_redis_manager
    
    redis_manager = get_redis_manager()
    stats = redis_manager.get_redis_stats()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "redis": stats,
    }
