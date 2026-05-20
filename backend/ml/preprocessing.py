"""
Frame extraction and preprocessing pipeline for deepfake detection.

Two public entry points:
  extract_frames()    — BGR numpy arrays from a video file
  preprocess_batch()  — (N, 3, H, W) tensor ready for model inference
"""

import logging
from typing import List, Optional, Tuple

import cv2
import numpy as np
import torch
from PIL import Image
from torchvision import transforms

logger = logging.getLogger(__name__)

# Haar cascade shared across calls within the same process
_face_cascade: Optional[cv2.CascadeClassifier] = None


def _get_face_cascade() -> cv2.CascadeClassifier:
    global _face_cascade
    if _face_cascade is None:
        _face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
    return _face_cascade


# ---------------------------------------------------------------------------
# Frame extraction
# ---------------------------------------------------------------------------

def extract_frames(
    video_path: str,
    max_frames: int = 20,
    target_fps: int = 5,
) -> List[np.ndarray]:
    """
    Sample up to *max_frames* BGR frames evenly from *video_path*.

    Near-black / corrupted frames (mean pixel < 5) are skipped.
    Raises ValueError if the file cannot be opened.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    try:
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total <= 0:
            total = max_frames * 10  # cautious fallback when metadata is absent

        step = max(1, total // max_frames)
        frames: List[np.ndarray] = []
        pos = 0

        while len(frames) < max_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
            ret, frame = cap.read()
            if not ret:
                break
            if np.mean(frame) >= 5:          # skip near-black frames
                frames.append(frame)
            pos += step
    finally:
        cap.release()

    return frames


# ---------------------------------------------------------------------------
# Face detection / crop helpers
# ---------------------------------------------------------------------------

def _largest_face_roi(
    frame_bgr: np.ndarray,
) -> Optional[Tuple[int, int, int, int]]:
    """Return (x, y, w, h) for the largest face in *frame_bgr*, or None."""
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    faces = _get_face_cascade().detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
    )
    if len(faces) == 0:
        return None
    return max(faces, key=lambda f: f[2] * f[3])  # largest by area


def _crop_to_face(frame_bgr: np.ndarray, padding: float = 0.2) -> np.ndarray:
    """
    Crop around the largest detected face (with padding).
    Falls back to a centre square crop when no face is detected.
    """
    h, w = frame_bgr.shape[:2]
    roi = _largest_face_roi(frame_bgr)

    if roi is not None:
        x, y, fw, fh = roi
        pad_x = int(fw * padding)
        pad_y = int(fh * padding)
        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(w, x + fw + pad_x)
        y2 = min(h, y + fh + pad_y)
        return frame_bgr[y1:y2, x1:x2]

    # Centre square crop
    side = min(h, w)
    cy, cx = h // 2, w // 2
    half = side // 2
    return frame_bgr[cy - half : cy + half, cx - half : cx + half]


# ---------------------------------------------------------------------------
# Tensor preprocessing
# ---------------------------------------------------------------------------

def _make_transform(target_size: Tuple[int, int]) -> transforms.Compose:
    return transforms.Compose([
        transforms.Resize(target_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ])


def preprocess_frame(
    frame_bgr: np.ndarray,
    target_size: Tuple[int, int],
) -> torch.Tensor:
    """
    Crop face (or centre), resize, normalise → (1, 3, H, W) float tensor.
    """
    cropped = _crop_to_face(frame_bgr)
    rgb = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    tensor = _make_transform(target_size)(pil)
    return tensor.unsqueeze(0)  # (1, 3, H, W)


def preprocess_batch(
    frames: List[np.ndarray],
    target_size: Tuple[int, int],
    device: torch.device,
) -> torch.Tensor:
    """
    Preprocess all frames and stack into a single (N, 3, H, W) tensor on *device*.
    """
    tensors = [preprocess_frame(f, target_size).squeeze(0) for f in frames]
    return torch.stack(tensors).to(device)
