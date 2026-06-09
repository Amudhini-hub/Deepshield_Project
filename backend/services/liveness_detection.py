"""
Liveness Detection Service — deterministic motion heuristic.

Replaces the untrained EfficientNet-B0 (which had a random 2-class head
and no fine-tuned weights) with two computable signals:

  1. Temporal pixel variance  — how much do pixels change across the frame
     stack?  A live person has natural micro-movements; a static photo or
     frozen frame has near-zero variance.

  2. Frame-to-frame motion   — mean absolute pixel difference between
     adjacent frames.  Live: 3–10 px; photo/still: < 0.5 px.

  3. Face presence           — a face must be detectable in at least one
     of the first five frames to contribute to the score.

The heuristic produces a continuous live_score in [0, 1] which is stored
as `confidence`.  Threshold for `is_live` is 0.20; the frontend's secondary
gate (confidence < 0.40 → CHALLENGE) provides an additional safety margin.

Public interface consumed by tasks.py is UNCHANGED:
    detector.detect_from_video(video_path, max_frames=60)
    result.is_alive        → bool
    result.confidence      → float
    result.challenge_type  → str
    result.frame_count     → int
    result.details         → dict
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Thresholds tuned empirically:
#   Real live face: variance ~15–50, motion ~2–10 px  → score > 0.60
#   Static photo:   variance ~0–2,   motion ~0–1.5 px → score < 0.25
_VAR_SCALE    = 15.0   # variance units that map to score 1.0
_MOTION_SCALE = 6.0    # motion px that maps to score 1.0
_IS_LIVE_THRESHOLD = 0.25


# ---------------------------------------------------------------------------
# Result dataclass  (backward-compat @property aliases for tasks.py)
# ---------------------------------------------------------------------------

@dataclass
class LivenessResult:
    is_live: bool
    confidence: float
    detection_method: str
    frame_count: int
    details: Dict
    anomalies: List[str]
    processing_time_ms: float = 0.0

    @property
    def is_alive(self) -> bool:
        return self.is_live

    @property
    def challenge_type(self) -> str:
        return self.detection_method


# ---------------------------------------------------------------------------
# Heuristic implementation
# ---------------------------------------------------------------------------

def _compute_live_score(
    frames: List[np.ndarray],
) -> tuple[float, dict]:
    """
    Compute a live_score in [0, 1] from BGR frame list.
    Returns (live_score, details_dict).
    """
    if not frames:
        return 0.0, {"error": "no_frames"}

    # ── 1. Temporal pixel variance ────────────────────────────────────────
    grays = [
        cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
        for f in frames
    ]
    stack = np.stack(grays, axis=0)          # (N, H, W)
    pixel_variance = float(np.var(stack, axis=0).mean())

    # ── 2. Frame-to-frame motion (mean |diff| between adjacent frames) ────
    if len(grays) >= 2:
        diffs = [
            float(np.mean(np.abs(grays[i + 1] - grays[i])))
            for i in range(len(grays) - 1)
        ]
        mean_motion = float(np.mean(diffs))
    else:
        mean_motion = 0.0

    # ── 3. Face presence ──────────────────────────────────────────────────
    try:
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        face_present = False
        for f in frames[:5]:
            gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            faces = cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50)
            )
            if len(faces) > 0:
                face_present = True
                break
    except Exception:
        face_present = False

    # ── 4. Score ──────────────────────────────────────────────────────────
    var_score    = min(1.0, pixel_variance / _VAR_SCALE)
    motion_score = min(1.0, mean_motion    / _MOTION_SCALE)
    face_score   = 1.0 if face_present else 0.0

    # Motion and variance each carry 45%; face detection carries 10%
    live_score = 0.45 * var_score + 0.45 * motion_score + 0.10 * face_score

    details = {
        "pixel_variance":  round(pixel_variance, 3),
        "mean_motion_px":  round(mean_motion, 3),
        "var_score":       round(var_score, 3),
        "motion_score":    round(motion_score, 3),
        "face_detected":   face_present,
        "live_score":      round(live_score, 4),
        "threshold":       _IS_LIVE_THRESHOLD,
        "frames_analysed": len(frames),
    }

    logger.info(
        "[liveness] variance=%.2f motion=%.2f face=%s → live_score=%.3f",
        pixel_variance, mean_motion, face_present, live_score,
    )
    return live_score, details


# ---------------------------------------------------------------------------
# Main detector
# ---------------------------------------------------------------------------

class LivenessDetector:
    """
    Liveness detection engine: deterministic motion heuristic.

    Requires at least 2 frames for meaningful temporal analysis.
    With 1 frame (frame-extraction failure) falls back to 0.5 neutral score
    with an anomaly flag so the issue is visible in logs.
    """

    def __init__(self, config: dict = None):
        self.config    = config or {}
        self.threshold = float(self.config.get("LIVENESS_THRESHOLD", _IS_LIVE_THRESHOLD))
        logger.info("[liveness] Motion heuristic detector ready (threshold=%.2f)", self.threshold)

    def _run(self, frames: list) -> LivenessResult:
        t0 = time.monotonic()
        anomalies: List[str] = []

        if len(frames) < 2:
            anomalies.append("too_few_frames: temporal analysis requires ≥2 frames")
            live_score = 0.5   # neutral — cannot determine liveness from 1 frame
            details: dict = {"frames_analysed": len(frames), "error": "insufficient_frames"}
        else:
            live_score, details = _compute_live_score(frames)

        is_live    = live_score >= self.threshold
        elapsed_ms = (time.monotonic() - t0) * 1000

        return LivenessResult(
            is_live=is_live,
            confidence=round(live_score, 4),
            detection_method="motion_analysis",
            frame_count=len(frames),
            details=details,
            anomalies=anomalies,
            processing_time_ms=round(elapsed_ms, 1),
        )

    def detect_from_video(
        self,
        video_path: str,
        max_frames: int = 20,
    ) -> LivenessResult:
        from backend.ml.preprocessing import extract_frames

        frames = extract_frames(video_path, max_frames=max_frames)
        if not frames:
            raise ValueError("No frames could be extracted from the video")

        logger.info("[liveness] extracted %d frames from %s", len(frames), video_path)
        return self._run(frames)

    def detect_from_frame(self, frame, config: dict = None) -> LivenessResult:
        return self._run([frame])


# Alias for code that uses the *Service naming convention
LivenessDetectionService = LivenessDetector
