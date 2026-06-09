import base64
import logging
import os
import tempfile
import time
from datetime import datetime, timezone

from celery.exceptions import SoftTimeLimitExceeded

from celery.signals import worker_ready
from backend.celery_app import celery_app

logger = logging.getLogger(__name__)


@worker_ready.connect
def prewarm_models(sender, **kwargs):
    """Load all ML models into memory when the worker starts so the first task is fast."""
    logger.info("Pre-warming ML models on worker startup…")
    try:
        _get_deepfake_detector()
        logger.info("Deepfake detector ready.")
    except Exception as exc:
        logger.warning("Deepfake detector pre-warm failed: %s", exc)
    try:
        _get_liveness_detector()
        logger.info("Liveness detector ready.")
    except Exception as exc:
        logger.warning("Liveness detector pre-warm failed: %s", exc)

# Module-level singletons — initialised once per worker process to avoid
# reloading heavy model weights on every task invocation.
_deepfake_detector = None
_liveness_detector = None


def _get_deepfake_detector():
    global _deepfake_detector
    if _deepfake_detector is None:
        from backend.config.config import get_config
        from backend.services.deepfake_detection import DeepfakeDetector
        _deepfake_detector = DeepfakeDetector(config=get_config().get_config_dict())
    return _deepfake_detector


def _get_liveness_detector():
    global _liveness_detector
    if _liveness_detector is None:
        from backend.config.config import get_config
        from backend.services.liveness_detection import LivenessDetector
        _liveness_detector = LivenessDetector(config=get_config().get_config_dict())
    return _liveness_detector


@celery_app.task(
    bind=True,
    max_retries=0,
    time_limit=300,
    soft_time_limit=240,
)
def detect_deepfake_task(self, video_b64: str, user_id: int,
                         generate_heatmap: bool = True) -> dict:
    """Run deepfake detection on a base64-encoded video. Returns a JSON-safe dict."""
    start = time.monotonic()
    logger.info(f"[deepfake] task_id={self.request.id} user_id={user_id} started")

    tmp_fd, video_path = None, None
    try:
        video_bytes = base64.b64decode(video_b64)
        tmp_fd, video_path = tempfile.mkstemp(suffix=".mp4")
        with os.fdopen(tmp_fd, "wb") as f:
            f.write(video_bytes)
        tmp_fd = None  # fd closed by fdopen

        result = _get_deepfake_detector().detect_from_video(
            video_path, max_frames=8, generate_heatmap=generate_heatmap
        )

        duration_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            f"[deepfake] task_id={self.request.id} user_id={user_id} "
            f"completed is_deepfake={result.is_deepfake} duration_ms={duration_ms}"
        )
        return {
            "user_id":             user_id,
            "is_deepfake":         result.is_deepfake,
            "confidence":          result.confidence,
            "detection_method":    result.detection_method,
            "frame_count":         result.frame_count,
            "details":             result.details,
            "anomalies":           result.anomalies,
            "heatmap_frame":       result.heatmap_frame,
            "heatmap_frame_index": result.heatmap_frame_index,
            "timestamp":           datetime.now(timezone.utc).isoformat(),
        }

    except SoftTimeLimitExceeded:
        logger.warning(f"[deepfake] task_id={self.request.id} user_id={user_id} soft time limit exceeded")
        raise
    except Exception as exc:
        logger.error(f"[deepfake] task_id={self.request.id} user_id={user_id} failed: {exc}")
        raise
    finally:
        if tmp_fd is not None:
            try:
                os.close(tmp_fd)
            except OSError:
                pass
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception:
                pass


@celery_app.task(
    bind=True,
    max_retries=0,
    time_limit=120,
    soft_time_limit=90,
)
def detect_liveness_task(self, video_b64: str, user_id: int) -> dict:
    """Run liveness detection on a base64-encoded video. Returns a JSON-safe dict."""
    start = time.monotonic()
    logger.info(f"[liveness] task_id={self.request.id} user_id={user_id} started")

    tmp_fd, video_path = None, None
    try:
        video_bytes = base64.b64decode(video_b64)
        tmp_fd, video_path = tempfile.mkstemp(suffix=".mp4")
        with os.fdopen(tmp_fd, "wb") as f:
            f.write(video_bytes)
        tmp_fd = None

        result = _get_liveness_detector().detect_from_video(video_path, max_frames=20)

        duration_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            f"[liveness] task_id={self.request.id} user_id={user_id} "
            f"completed is_alive={result.is_alive} duration_ms={duration_ms}"
        )
        return {
            "user_id": user_id,
            "is_alive": result.is_alive,
            "confidence": result.confidence,
            "challenge_type": result.challenge_type,
            "frame_count": result.frame_count,
            "details": result.details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except SoftTimeLimitExceeded:
        logger.warning(f"[liveness] task_id={self.request.id} user_id={user_id} soft time limit exceeded")
        raise
    except Exception as exc:
        logger.error(f"[liveness] task_id={self.request.id} user_id={user_id} failed: {exc}")
        raise
    finally:
        if tmp_fd is not None:
            try:
                os.close(tmp_fd)
            except OSError:
                pass
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception:
                pass
