"""
HuggingFace-based deepfake detector.
Uses dima806/deepfake_vs_real_image_detection (ViT fine-tuned on deepfake datasets).
Loaded lazily; failure is non-fatal — the ensemble falls back to timm models.
"""

import logging
import threading
from typing import List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_hf_pipe = None
MODEL_ID = "dima806/deepfake_vs_real_image_detection"


def get_pipeline():
    global _hf_pipe
    if _hf_pipe is None:
        with _LOCK:
            if _hf_pipe is None:
                from transformers import pipeline
                import torch
                device = 0 if torch.cuda.is_available() else -1
                logger.info("Loading HuggingFace deepfake model: %s", MODEL_ID)
                _hf_pipe = pipeline(
                    "image-classification",
                    model=MODEL_ID,
                    device=device,
                )
                logger.info("HuggingFace deepfake model ready (device=%s)", device)
    return _hf_pipe


def infer_frames(frames_bgr: List[np.ndarray]) -> Tuple[Optional[float], List[float]]:
    """
    Run HF classifier over a list of BGR frames.
    Only frames with a detected face are passed to the model — center-square crops
    from no-face frames score ~99% fake and corrupt the mean.
    Returns (mean_fake_prob, per_frame_probs) or (None, []) on failure.
    """
    try:
        import cv2
        from PIL import Image
        from backend.ml.preprocessing import _crop_to_face, _largest_face_roi

        pipe = get_pipeline()

        # Build list of PIL face-crops, skipping frames where no face is found
        pil_frames = []
        for f in frames_bgr:
            if _largest_face_roi(f) is not None:
                crop = _crop_to_face(f)
                pil_frames.append(Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)))

        if not pil_frames:
            # No face detected in any frame — fall back to full frames
            logger.warning("[hf_detector] no face detected in %d frames, using full frames", len(frames_bgr))
            pil_frames = [
                Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
                for f in frames_bgr
            ]

        logger.info("[hf_detector] running inference on %d/%d frames with face", len(pil_frames), len(frames_bgr))

        results = pipe(pil_frames)
        # pipeline returns list-of-lists when given a list of images
        if results and not isinstance(results[0], list):
            results = [[r] for r in results]

        per_frame = [_fake_prob(r) for r in results]
        mean_prob = float(np.mean(per_frame)) if per_frame else 0.5
        logger.info("[hf_detector] mean fake prob=%.3f over %d frames", mean_prob, len(per_frame))
        return mean_prob, per_frame

    except Exception as exc:
        logger.warning("[hf_detector] inference failed: %s", exc)
        return None, []


def _fake_prob(frame_results: list) -> float:
    """Extract fake probability from one frame's pipeline output."""
    for r in frame_results:
        label = r["label"].lower()
        score = float(r["score"])
        if "fake" in label:
            return score
        if "real" in label:
            return 1.0 - score
    # Fallback: assume top result is the fake class
    return float(frame_results[0]["score"]) if frame_results else 0.5
