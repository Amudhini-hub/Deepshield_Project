"""
Deepfake Detection Service
XceptionNet + EfficientNet-B4 ensemble via PyTorch / timm.

Public interface is unchanged — backend/tasks.py calls:
    detector.detect_from_video(video_path, max_frames=30)
and reads result attributes directly (is_deepfake, confidence, …).
"""

import base64
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn.functional as F

logger = logging.getLogger(__name__)

# Input sizes expected by each backbone
_XCEPTION_SIZE     = (299, 299)
_EFFICIENTNET_SIZE = (380, 380)

# Flag model disagreement when |x_score − e_score| exceeds this
_DISAGREEMENT_THRESHOLD = 0.4


# ---------------------------------------------------------------------------
# Result dataclass  (attribute access required by tasks.py)
# ---------------------------------------------------------------------------

@dataclass
class DeepfakeResult:
    is_deepfake: bool
    confidence: float
    detection_method: str
    frame_count: int
    details: Dict
    anomalies: List[str]
    processing_time_ms: float = 0.0
    heatmap_frame: Optional[str] = None        # base64 JPEG
    heatmap_frame_index: Optional[int] = None


# ---------------------------------------------------------------------------
# Main detector
# ---------------------------------------------------------------------------

class DeepfakeDetector:
    """
    Deepfake detection engine: XceptionNet (weight 0.6) +
    EfficientNet-B4 (weight 0.4) ensemble.

    Models are loaded once per process by ModelLoader and cached.
    If one model fails at runtime, the other carries full weight.
    Both models fail → RuntimeError (Celery retries the task).
    """

    def __init__(self, config: dict = None):
        self.config = config or {}

        # Config keys come from Config.get_config_dict() — all uppercase
        self.threshold          = float(self.config.get("DEEPFAKE_DETECTION_THRESHOLD", 0.5))
        self.xception_w         = float(self.config.get("DEEPFAKE_ENSEMBLE_XCEPTION_WEIGHT",     0.6))
        self.efficientnet_w     = float(self.config.get("DEEPFAKE_ENSEMBLE_EFFICIENTNET_WEIGHT", 0.4))
        self.weights_dir        = self.config.get("DEEPFAKE_MODEL_WEIGHTS_DIR", "./ml_models")
        self.xception_wfile     = self.config.get("XCEPTION_WEIGHTS_FILE",     "xception_ff++.pth")
        self.efficientnet_wfile = self.config.get("EFFICIENTNET_WEIGHTS_FILE", "efficientnet_b4_ff++.pth")

        self._load_models()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _load_models(self) -> None:
        from backend.ml.model_loader import ModelLoader

        self.device = ModelLoader.get_device()

        self.xception = ModelLoader.get_xception()
        ModelLoader.load_weights(
            "xception",
            os.path.join(self.weights_dir, self.xception_wfile),
        )

        self.efficientnet = ModelLoader.get_efficientnet()
        ModelLoader.load_weights(
            "efficientnet",
            os.path.join(self.weights_dir, self.efficientnet_wfile),
        )

        # HuggingFace fine-tuned model — highest weight in ensemble (actually trained on deepfakes)
        self._hf_available = False
        try:
            from backend.ml.hf_detector import get_pipeline
            get_pipeline()
            self._hf_available = True
            logger.info("[deepfake] HuggingFace model pre-loaded successfully")
        except Exception as exc:
            logger.warning("[deepfake] HuggingFace model unavailable, using timm-only ensemble: %s", exc)

    # ------------------------------------------------------------------
    # Inference helpers
    # ------------------------------------------------------------------

    def _infer(
        self,
        model: torch.nn.Module,
        batch: torch.Tensor,
        name: str,
    ) -> Tuple[Optional[float], List[float]]:
        """
        Run *model* on *batch* inside torch.no_grad().
        Returns (mean_score, per_frame_scores).
        mean_score is None on error; per_frame_scores is [] on error.
        """
        try:
            with torch.no_grad():
                logits = model(batch)                   # (N, 2)
                probs  = F.softmax(logits, dim=1)       # (N, 2)
                fake_p = probs[:, 0]                    # (N,) — class 0 = fake (FF++ Xception convention)
                return float(fake_p.mean().item()), fake_p.cpu().tolist()
        except Exception as exc:
            logger.warning("[deepfake] %s inference failed: %s", name, exc)
            return None, []

    # ------------------------------------------------------------------
    # Public interface  (signature MUST NOT change — called by tasks.py)
    # ------------------------------------------------------------------

    def detect_from_video(
        self,
        video_path: str,
        max_frames: int = 20,
        generate_heatmap: bool = False,
    ) -> DeepfakeResult:
        """
        Run ensemble deepfake detection on *video_path*.

        Args:
            video_path: Absolute path to the video file.
            max_frames: Maximum frames to sample (tasks.py passes 30).

        Returns:
            DeepfakeResult with verdict, per-model scores, and timing.

        Raises:
            ValueError:   No frames could be extracted.
            RuntimeError: Both models failed — Celery will retry.
        """
        from backend.ml.preprocessing import extract_frames, preprocess_batch

        t0 = time.monotonic()
        anomalies: List[str] = []

        # ── 1. Extract frames ────────────────────────────────────────────
        frames = extract_frames(video_path, max_frames=max_frames)
        if not frames:
            raise ValueError("No frames could be extracted from the video")

        face_detected = _any_face_present(frames[:5])

        # ── 2. Build per-model batches (different input sizes) ───────────
        x_batch  = preprocess_batch(frames, _XCEPTION_SIZE,     self.device)
        en_batch = preprocess_batch(frames, _EFFICIENTNET_SIZE,  self.device)

        # ── 3. Inference ────────────────────────────────────────────────
        x_score,  x_frame_scores  = self._infer(self.xception,    x_batch,  "xception")
        en_score, en_frame_scores = self._infer(self.efficientnet, en_batch, "efficientnet")

        # HuggingFace fine-tuned model (highest weight — actually trained on deepfakes)
        hf_score: Optional[float] = None
        hf_frame_scores: List[float] = []
        if self._hf_available:
            try:
                from backend.ml.hf_detector import infer_frames
                hf_score, hf_frame_scores = infer_frames(frames)
            except Exception as exc:
                logger.warning("[deepfake] HF inference failed at task time: %s", exc)

        if hf_score is None and x_score is None and en_score is None:
            raise RuntimeError("All deepfake models failed — cannot produce a result")

        # ── 4. Ensemble ──────────────────────────────────────────────────
        if hf_score is not None:
            # Weights: 75% HF ViT (face-cropped) + 25% XceptionNet (FF++ fine-tuned, class0=fake).
            # HF ViT dominates because it's more reliable with face crops.
            # EfficientNet-B4 excluded (untrained classifier head).
            x_contrib = x_score if x_score is not None else hf_score
            ensemble = hf_score * 0.75 + x_contrib * 0.25
            anomalies_note = f"hf_score={hf_score:.3f}"
            if en_score is not None:
                anomalies_note += f" efficientnet={en_score:.3f}(excluded-untrained-head)"
            if x_score is not None:
                anomalies_note += f" xception={x_score:.3f}"
            logger.info("[deepfake] HF+Xception ensemble: %s → %.3f", anomalies_note, ensemble)
        elif x_score is not None and en_score is not None:
            ensemble = x_score * self.xception_w + en_score * self.efficientnet_w
            if abs(x_score - en_score) > _DISAGREEMENT_THRESHOLD:
                anomalies.append(
                    f"model_disagreement: xception={x_score:.3f} "
                    f"efficientnet={en_score:.3f}"
                )
        elif x_score is not None:
            ensemble = x_score
            anomalies.append("efficientnet_unavailable: using xception only (weight=1.0)")
        else:
            ensemble = en_score  # type: ignore[assignment]
            anomalies.append("xception_unavailable: using efficientnet only (weight=1.0)")

        confidence  = float(ensemble)
        is_deepfake = confidence >= self.threshold
        elapsed_ms  = (time.monotonic() - t0) * 1000

        # ── 5. Optional Grad-CAM heatmap ─────────────────────────────────
        heatmap_frame: Optional[str] = None
        heatmap_frame_index: Optional[int] = None

        if generate_heatmap and frames:
            try:
                import cv2
                from backend.ml.gradcam import generate_ensemble_heatmap

                # Build per-frame ensemble scores to find the most suspicious frame
                per_frame: List[float] = []
                for i in range(len(frames)):
                    xs  = x_frame_scores[i]  if i < len(x_frame_scores)  else None
                    es  = en_frame_scores[i] if i < len(en_frame_scores) else None
                    hfs = hf_frame_scores[i] if i < len(hf_frame_scores) else None
                    if hfs is not None:
                        xs_contrib = xs if xs is not None else hfs
                        score = hfs * 0.75 + xs_contrib * 0.25
                        per_frame.append(score)
                    elif xs is not None and es is not None:
                        per_frame.append(xs * self.xception_w + es * self.efficientnet_w)
                    elif xs is not None:
                        per_frame.append(xs)
                    elif es is not None:
                        per_frame.append(es)
                    else:
                        per_frame.append(0.0)

                idx = int(np.argmax(per_frame)) if per_frame else 0
                annotated = generate_ensemble_heatmap(
                    frames[idx], self.xception, self.efficientnet, self.device
                )
                _, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
                heatmap_frame       = base64.b64encode(buf).decode("utf-8")
                heatmap_frame_index = idx
            except Exception as exc:
                logger.warning("[deepfake] Heatmap generation failed: %s", exc)

        return DeepfakeResult(
            is_deepfake=is_deepfake,
            confidence=round(confidence, 4),
            detection_method="vit_xception_ensemble",
            frame_count=len(frames),
            details={
                "xception_score":     round(x_score,  4) if x_score  is not None else None,
                "efficientnet_score": round(en_score, 4) if en_score is not None else None,
                "ensemble_method":    "weighted_average",
                "frames_analysed":    len(frames),
                "face_detected":      face_detected,
            },
            anomalies=anomalies,
            processing_time_ms=round(elapsed_ms, 1),
            heatmap_frame=heatmap_frame,
            heatmap_frame_index=heatmap_frame_index,
        )

    # keep the old method name alive in case anything else calls it
    def detect_from_frames(self, frames, **_):  # type: ignore[override]
        raise NotImplementedError(
            "detect_from_frames() is no longer supported; use detect_from_video()"
        )


# Alias for code that uses the *Service naming convention
DeepfakeDetectionService = DeepfakeDetector


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _any_face_present(frames: List) -> bool:
    """Return True if a face is visible in at least one of *frames*."""
    try:
        import cv2
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        for frame in frames:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if len(cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))) > 0:
                return True
    except Exception:
        pass
    return False
