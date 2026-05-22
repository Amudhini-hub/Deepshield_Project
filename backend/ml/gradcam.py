"""
Grad-CAM heatmap generation for deepfake detection.

Public API
----------
GradCAM(model, target_layer_name)
    .generate(input_tensor, target_class=1)  -> (H, W) float32 ndarray in [0,1] or None
    .overlay_on_frame(frame_bgr, heatmap)    -> BGR ndarray
    .cleanup()                               -> removes hooks, frees references

generate_ensemble_heatmap(frame, xception_model, efficientnet_model, device)
    -> annotated BGR ndarray (xception 0.6 + efficientnet 0.4 weighted blend)

Layer names (confirmed via named_modules() on timm 1.0.27):
    legacy_xception   -> "conv4"
    efficientnet_b4   -> "conv_head"
"""

import logging
from typing import List, Optional

import cv2
import numpy as np
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)

_XCEPTION_TARGET     = "conv4"
_EFFICIENTNET_TARGET = "conv_head"
_XCEPTION_SIZE       = (299, 299)
_EFFICIENTNET_SIZE   = (380, 380)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _overlay_heatmap(frame_bgr: np.ndarray, heatmap: np.ndarray) -> np.ndarray:
    """Resize *heatmap* to *frame_bgr* size and blend with JET colormap."""
    h, w = frame_bgr.shape[:2]
    resized  = cv2.resize(heatmap, (w, h), interpolation=cv2.INTER_LINEAR)
    colored  = cv2.applyColorMap(np.uint8(resized * 255), cv2.COLORMAP_JET)
    return cv2.addWeighted(colored, 0.4, frame_bgr, 0.6, 0)


# ---------------------------------------------------------------------------
# GradCAM
# ---------------------------------------------------------------------------

class GradCAM:
    """
    Single-layer Grad-CAM wrapper.

    Registers forward + backward hooks on *target_layer_name* at construction.
    MUST call .cleanup() after use to prevent hook accumulation in long-running
    Celery workers.
    """

    def __init__(self, model: nn.Module, target_layer_name: str) -> None:
        self._model             = model
        self._target_layer_name = target_layer_name
        self._gradients:  Optional[torch.Tensor] = None
        self._activations: Optional[torch.Tensor] = None
        self._hooks: List[torch.utils.hooks.RemovableHook] = []
        self._layer_found = False

        for name, module in model.named_modules():
            if name != target_layer_name:
                continue

            self._layer_found = True

            # Capture in closures — avoid late-binding issues with loop variable
            def _fwd_hook(mod, inp, out):           # noqa: ARG001
                self._activations = out.detach()

            def _bwd_hook(mod, grad_in, grad_out):  # noqa: ARG001
                self._gradients = grad_out[0].detach()

            self._hooks.append(module.register_forward_hook(_fwd_hook))
            self._hooks.append(module.register_full_backward_hook(_bwd_hook))
            break

        if not self._layer_found:
            logger.warning(
                "[gradcam] Target layer '%s' not found in model — heatmap will be skipped",
                target_layer_name,
            )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate(
        self,
        input_tensor: torch.Tensor,
        target_class: int = 1,
    ) -> Optional[np.ndarray]:
        """
        Run Grad-CAM on *input_tensor* (shape 1 × 3 × H × W).

        Returns a (H′, W′) float32 ndarray normalised to [0, 1],
        or None if the target layer was not found or produced a zero map.

        NOTE: Do NOT call this inside torch.no_grad() — gradients are required.
              torch.enable_grad() is used internally to ensure correctness.
        """
        if not self._layer_found:
            return None

        self._gradients  = None
        self._activations = None

        try:
            with torch.enable_grad():
                self._model.zero_grad()
                logits = self._model(input_tensor)          # (1, num_classes)
                score  = logits[:, target_class].sum()
                score.backward()
        except Exception as exc:
            logger.warning("[gradcam] Forward/backward failed on '%s': %s",
                           self._target_layer_name, exc)
            return None
        finally:
            # Leave model parameters clean for subsequent no_grad inference
            self._model.zero_grad()

        if self._gradients is None or self._activations is None:
            logger.warning(
                "[gradcam] Hooks on '%s' did not fire — heatmap skipped",
                self._target_layer_name,
            )
            return None

        # Pool gradients: mean over spatial dims → (C,)
        weights = self._gradients.squeeze(0).mean(dim=(-2, -1))     # (C,)
        # Weighted sum over channels → (H, W)
        cam = (weights[:, None, None] * self._activations.squeeze(0)).sum(dim=0)
        cam = torch.relu(cam).cpu().numpy().astype(np.float32)

        if cam.max() == 0.0:
            logger.warning(
                "[gradcam] All-zero heatmap from '%s' — layer may not be spatial",
                self._target_layer_name,
            )
            return None

        return cam / cam.max()

    def overlay_on_frame(
        self,
        frame_bgr: np.ndarray,
        heatmap: np.ndarray,
    ) -> np.ndarray:
        """Blend *heatmap* onto *frame_bgr* using JET colormap (40 % / 60 % mix)."""
        return _overlay_heatmap(frame_bgr, heatmap)

    def cleanup(self) -> None:
        """Remove all hooks and release tensor references."""
        for handle in self._hooks:
            handle.remove()
        self._hooks.clear()
        self._gradients  = None
        self._activations = None


# ---------------------------------------------------------------------------
# Ensemble helper
# ---------------------------------------------------------------------------

def generate_ensemble_heatmap(
    frame: np.ndarray,
    xception_model: nn.Module,
    efficientnet_model: nn.Module,
    device: torch.device,
) -> np.ndarray:
    """
    Run Grad-CAM with both models on *frame*, blend (xception×0.6 + effnet×0.4),
    and return an annotated BGR frame.

    Always returns a valid BGR frame even if one or both models fail — the
    failing model's contribution is replaced with a zero map.
    """
    from backend.ml.preprocessing import preprocess_frame

    h, w = frame.shape[:2]

    x_tensor  = preprocess_frame(frame, _XCEPTION_SIZE).to(device)     # (1,3,299,299)
    en_tensor = preprocess_frame(frame, _EFFICIENTNET_SIZE).to(device)  # (1,3,380,380)

    gc_x  = GradCAM(xception_model,    _XCEPTION_TARGET)
    gc_en = GradCAM(efficientnet_model, _EFFICIENTNET_TARGET)

    try:
        x_cam  = gc_x.generate(x_tensor)
        en_cam = gc_en.generate(en_tensor)
    finally:
        gc_x.cleanup()
        gc_en.cleanup()

    def _resize_or_zero(cam: Optional[np.ndarray]) -> np.ndarray:
        if cam is None:
            return np.zeros((h, w), dtype=np.float32)
        return cv2.resize(cam, (w, h), interpolation=cv2.INTER_LINEAR)

    blended = _resize_or_zero(x_cam) * 0.6 + _resize_or_zero(en_cam) * 0.4
    if blended.max() > 0:
        blended = blended / blended.max()

    return _overlay_heatmap(frame, blended)
