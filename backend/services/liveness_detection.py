"""
Liveness Detection Service
EfficientNet-B0 PyTorch model — detects whether a face is live (not a photo/replay/mask).

Public interface consumed by tasks.py:
    detector.detect_from_video(video_path, max_frames=60)
    result.is_alive        → bool   (alias for is_live)
    result.confidence      → float
    result.challenge_type  → str    (alias for detection_method)
    result.frame_count     → int
    result.details         → dict
"""

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import torch
import torch.nn.functional as F

logger = logging.getLogger(__name__)

_EFFICIENTNET_B0_SIZE = (224, 224)


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
# Main detector
# ---------------------------------------------------------------------------

class LivenessDetector:
    """
    Liveness detection engine: EfficientNet-B0 (224×224).

    Class 0 = spoof, class 1 = live.
    Falls back to a neutral score (0.5) if the model fails entirely.
    """

    def __init__(self, config: dict = None):
        self.config = config or {}

        self.threshold    = float(self.config.get("LIVENESS_THRESHOLD", 0.5))
        self.weights_dir  = self.config.get("DEEPFAKE_MODEL_WEIGHTS_DIR", "./ml_models")
        self.weights_file = self.config.get("LIVENESS_MODEL_WEIGHTS", "")

        self._load_model()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        from backend.ml.model_loader import ModelLoader

        self.device = ModelLoader.get_device()
        self.model  = ModelLoader.get_efficientnet_b0()

        if self.weights_file:
            weights_path = os.path.join(self.weights_dir, self.weights_file)
            ModelLoader.load_weights("efficientnet_b0", weights_path)

    # ------------------------------------------------------------------
    # Inference helper
    # ------------------------------------------------------------------

    def _infer(self, batch: torch.Tensor) -> Optional[float]:
        """
        Run EfficientNet-B0 on *batch*.
        Returns mean live-class probability (class index 1), or None on error.
        """
        try:
            with torch.no_grad():
                logits = self.model(batch)           # (N, 2)
                probs  = F.softmax(logits, dim=1)    # (N, 2)
                live_p = probs[:, 1]                 # class 1 = live
                return float(live_p.mean().item())
        except Exception as exc:
            logger.warning("[liveness] inference failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Shared pipeline
    # ------------------------------------------------------------------

    def _run(self, frames: list) -> LivenessResult:
        """Core pipeline: preprocess *frames* → infer → return LivenessResult."""
        from backend.ml.preprocessing import preprocess_batch

        t0        = time.monotonic()
        anomalies: List[str] = []

        batch = preprocess_batch(frames, _EFFICIENTNET_B0_SIZE, self.device)
        score = self._infer(batch)

        if score is None:
            score = 0.5
            anomalies.append("model_failed: using neutral fallback score")

        is_live    = score >= self.threshold
        elapsed_ms = (time.monotonic() - t0) * 1000

        return LivenessResult(
            is_live=is_live,
            confidence=round(score, 4),
            detection_method="efficientnet_b0",
            frame_count=len(frames),
            details={
                "live_score":      round(score, 4),
                "threshold":       self.threshold,
                "frames_analysed": len(frames),
            },
            anomalies=anomalies,
            processing_time_ms=round(elapsed_ms, 1),
        )

    # ------------------------------------------------------------------
    # Public interface  (signatures MUST NOT change — called by tasks.py)
    # ------------------------------------------------------------------

    def detect_from_video(
        self,
        video_path: str,
        max_frames: int = 20,
    ) -> LivenessResult:
        """
        Run liveness detection on *video_path*.

        Args:
            video_path: Absolute path to the video file.
            max_frames: Maximum frames to sample (tasks.py passes 60).

        Returns:
            LivenessResult with verdict, score, and timing.

        Raises:
            ValueError: No frames could be extracted.
        """
        from backend.ml.preprocessing import extract_frames

        frames = extract_frames(video_path, max_frames=max_frames)
        if not frames:
            raise ValueError("No frames could be extracted from the video")

        return self._run(frames)

    def detect_from_frame(self, frame, config: dict = None) -> LivenessResult:
        """Single-frame convenience wrapper."""
        return self._run([frame])


# Alias for code that uses the *Service naming convention
LivenessDetectionService = LivenessDetector
