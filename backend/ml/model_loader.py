"""
Thread-safe singleton model loader for deepfake detection.

Models are loaded once per worker process and kept in a module-level cache.
Call load_weights() after get_*() to apply fine-tuned checkpoint files;
if the file is absent the model stays with its ImageNet pretrained weights.
"""

import logging
import os
import threading
from typing import Optional

import timm
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()


class ModelLoader:
    _models: dict = {}

    # ------------------------------------------------------------------
    # Device
    # ------------------------------------------------------------------

    @classmethod
    def get_device(cls) -> torch.device:
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ------------------------------------------------------------------
    # Model accessors  (double-checked locking for thread safety)
    # ------------------------------------------------------------------

    @classmethod
    def get_xception(cls) -> nn.Module:
        """Return the cached XceptionNet (2-class head, eval mode)."""
        if "xception" not in cls._models:
            with _LOCK:
                if "xception" not in cls._models:
                    logger.info("Loading XceptionNet (random init — no pretrained weights needed)…")
                    # pretrained=False avoids unreliable GitHub CDN download at worker startup.
                    # Fine-tuned weights are loaded separately via load_weights() if available.
                    model = timm.create_model("legacy_xception", pretrained=False, num_classes=2)
                    model.eval()
                    model = model.to(cls.get_device())
                    cls._models["xception"] = model
                    logger.info("XceptionNet ready on %s (random init)", cls.get_device())
        return cls._models["xception"]

    @classmethod
    def get_efficientnet(cls) -> nn.Module:
        """Return the cached EfficientNet-B4 (2-class head, eval mode)."""
        if "efficientnet" not in cls._models:
            with _LOCK:
                if "efficientnet" not in cls._models:
                    logger.info("Loading EfficientNet-B4 with ImageNet pretrained weights…")
                    model = timm.create_model(
                        "efficientnet_b4", pretrained=True, num_classes=2
                    )
                    model.eval()
                    model = model.to(cls.get_device())
                    cls._models["efficientnet"] = model
                    logger.info("EfficientNet-B4 ready on %s", cls.get_device())
        return cls._models["efficientnet"]

    @classmethod
    def get_efficientnet_b0(cls) -> nn.Module:
        """Return the cached EfficientNet-B0 (2-class head, eval mode)."""
        if "efficientnet_b0" not in cls._models:
            with _LOCK:
                if "efficientnet_b0" not in cls._models:
                    logger.info("Loading EfficientNet-B0 with ImageNet pretrained weights…")
                    model = timm.create_model(
                        "efficientnet_b0", pretrained=True, num_classes=2
                    )
                    model.eval()
                    model = model.to(cls.get_device())
                    cls._models["efficientnet_b0"] = model
                    logger.info("EfficientNet-B0 ready on %s", cls.get_device())
        return cls._models["efficientnet_b0"]

    # ------------------------------------------------------------------
    # Fine-tuned weight loading
    # ------------------------------------------------------------------

    @classmethod
    def load_weights(cls, model_name: str, weights_path: str) -> None:
        """
        Load fine-tuned checkpoint weights into a cached model.

        Silently skips if the file does not exist — the model keeps its
        ImageNet pretrained weights.  Uses strict=False so partial
        checkpoints (backbone-only, head-only) are tolerated.
        """
        if not os.path.exists(weights_path):
            logger.info(
                "Fine-tuned weights not found for %s (%s) — using ImageNet pretrained",
                model_name, weights_path,
            )
            return

        model: Optional[nn.Module] = cls._models.get(model_name)
        if model is None:
            logger.warning(
                "load_weights called for '%s' before the model was initialised — skipping",
                model_name,
            )
            return

        try:
            device = cls.get_device()
            # weights_only=True avoids arbitrary pickle code execution (PyTorch ≥ 2.0)
            raw = torch.load(weights_path, map_location=device, weights_only=True)
            # Support both bare state dicts and checkpoint dicts
            state_dict = raw.get("state_dict", raw) if isinstance(raw, dict) else raw
            # Strip common wrapper prefixes (e.g. "backbone.", "model.", "module.")
            # so checkpoints from different training frameworks can be reused.
            model_keys = set(model.state_dict().keys())
            for prefix in ("backbone.", "model.", "module.", "encoder."):
                stripped = {k[len(prefix):]: v for k, v in state_dict.items() if k.startswith(prefix)}
                if stripped and any(k in model_keys for k in stripped):
                    state_dict = stripped
                    logger.debug("Stripped prefix '%s' from checkpoint keys", prefix)
                    break
            missing, unexpected = model.load_state_dict(state_dict, strict=False)
            if missing:
                logger.debug("Missing keys for %s: %s", model_name, missing[:5])
            if unexpected:
                logger.debug("Unexpected keys for %s: %s", model_name, unexpected[:5])
            logger.info(
                "Loaded fine-tuned weights for %s from %s", model_name, weights_path
            )
        except Exception as exc:
            logger.warning(
                "Could not load fine-tuned weights for %s (%s): %s — "
                "continuing with ImageNet pretrained weights",
                model_name, weights_path, exc,
            )
