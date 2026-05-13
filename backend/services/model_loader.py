"""
ML Model Loader Service for DeepShield
Loads, caches, and manages pre-trained ML models
"""

import json
import logging
import os
import pickle
from datetime import datetime
from typing import Any, Dict, Optional

import tensorflow as tf
import tensorflow_hub as hub
from tensorflow import keras

from backend.redis_manager import get_redis_manager

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Registry of available models"""

    # Pre-trained models from TensorFlow Hub and other sources
    MODELS = {
        "deepfake_mobilenetv2": {
            "type": "deepfake",
            "url": "https://tfhub.dev/google/tf2-preview/mobilenet_v2/classification/2",
            "input_shape": (224, 224, 3),
            "description": "MobileNetV2 for deepfake detection (fast)",
            "source": "tensorflow_hub",
            "cache_key": "model:deepfake:mobilenetv2",
        },
        "deepfake_efficientnetb0": {
            "type": "deepfake",
            "url": "https://tfhub.dev/google/efficientnet/b0/feature-vector/1",
            "input_shape": (224, 224, 3),
            "description": "EfficientNetB0 for deepfake detection",
            "source": "tensorflow_hub",
            "cache_key": "model:deepfake:efficientnetb0",
        },
        "liveness_mobilenet": {
            "type": "liveness",
            "url": "https://tfhub.dev/google/tf2-preview/mobilenet_v2/classification/2",
            "input_shape": (224, 224, 3),
            "description": "MobileNetV2 for liveness detection",
            "source": "tensorflow_hub",
            "cache_key": "model:liveness:mobilenet",
        },
        "face_detection_ssd": {
            "type": "face_detection",
            "url": "https://tfhub.dev/tensorflow/ssd_mobilenet_v2/2",
            "input_shape": (320, 320, 3),
            "description": "SSD MobileNetV2 for face detection",
            "source": "tensorflow_hub",
            "cache_key": "model:face:detection",
        },
    }

    @classmethod
    def get_model_info(cls, model_name: str) -> Optional[Dict[str, Any]]:
        """Get model information"""
        return cls.MODELS.get(model_name)

    @classmethod
    def list_models(cls, model_type: str = None) -> Dict[str, Dict]:
        """List available models, optionally filtered by type"""
        if model_type:
            return {
                name: info
                for name, info in cls.MODELS.items()
                if info.get("type") == model_type
            }
        return cls.MODELS

    @classmethod
    def get_default_model(cls, model_type: str) -> str:
        """Get default model for a type"""
        defaults = {
            "deepfake": "deepfake_mobilenetv2",
            "liveness": "liveness_mobilenet",
            "face_detection": "face_detection_ssd",
        }
        return defaults.get(model_type)


class MLModelLoader:
    """Centralized ML model loading and caching"""

    def __init__(self, cache_models: bool = True):
        """
        Initialize model loader

        Args:
            cache_models: Whether to cache models in Redis
        """
        self.cache_models = cache_models
        self.redis_manager = get_redis_manager() if cache_models else None
        self.loaded_models = {}  # In-memory cache
        self.model_info = {}  # Cache metadata

    def load_model(self, model_name: str, force_reload: bool = False) -> Optional[Any]:
        """
        Load a model with caching

        Args:
            model_name: Model identifier
            force_reload: Force reload even if cached

        Returns:
            Loaded model or None if failed
        """
        # Check in-memory cache first
        if not force_reload and model_name in self.loaded_models:
            logger.info(f"Model {model_name} loaded from memory cache")
            return self.loaded_models[model_name]

        # Check Redis cache
        if (
            self.cache_models
            and not force_reload
            and self.redis_manager
            and self.redis_manager.is_connected()
        ):
            model = self._load_from_redis(model_name)
            if model is not None:
                self.loaded_models[model_name] = model
                logger.info(f"Model {model_name} loaded from Redis cache")
                return model

        # Load from source
        logger.info(f"Loading model {model_name} from source...")
        model = self._load_from_source(model_name)

        if model is not None:
            self.loaded_models[model_name] = model

            # Cache to Redis
            if (
                self.cache_models
                and self.redis_manager
                and self.redis_manager.is_connected()
            ):
                self._save_to_redis(model_name, model)

            logger.info(f"Model {model_name} loaded successfully and cached")
            return model

        logger.error(f"Failed to load model {model_name}")
        return None

    def _load_from_source(self, model_name: str) -> Optional[Any]:
        """Load model from original source"""
        try:
            model_info = ModelRegistry.get_model_info(model_name)
            if not model_info:
                logger.error(f"Unknown model: {model_name}")
                return None

            source = model_info.get("source")
            url = model_info.get("url")

            if source == "tensorflow_hub":
                logger.info(f"Loading from TensorFlow Hub: {url}")
                model = hub.load(url)
                self.model_info[model_name] = {
                    "loaded_at": datetime.utcnow().isoformat(),
                    "source": "tensorflow_hub",
                    "info": model_info,
                }
                return model

            elif source == "local":
                logger.info(f"Loading from local path: {url}")
                if os.path.exists(url):
                    model = keras.models.load_model(url)
                    self.model_info[model_name] = {
                        "loaded_at": datetime.utcnow().isoformat(),
                        "source": "local",
                        "info": model_info,
                    }
                    return model
                else:
                    logger.error(f"Local model not found: {url}")
                    return None

            else:
                logger.error(f"Unknown source: {source}")
                return None

        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            return None

    def _load_from_redis(self, model_name: str) -> Optional[Any]:
        """Load model from Redis cache"""
        try:
            if not self.redis_manager or not self.redis_manager.is_connected():
                return None

            model_info = ModelRegistry.get_model_info(model_name)
            if not model_info:
                return None

            cache_key = model_info.get("cache_key")
            cached_data = self.redis_manager.get_cache(cache_key)

            if cached_data:
                logger.info(f"Loading {model_name} from Redis cache")
                return pickle.loads(
                    cached_data.encode()
                    if isinstance(cached_data, str)
                    else cached_data
                )

            return None
        except Exception as e:
            logger.warning(f"Error loading from Redis: {e}")
            return None

    def _save_to_redis(self, model_name: str, model: Any) -> bool:
        """Save model to Redis cache"""
        try:
            if not self.redis_manager or not self.redis_manager.is_connected():
                return False

            model_info = ModelRegistry.get_model_info(model_name)
            if not model_info:
                return False

            cache_key = model_info.get("cache_key")
            # Note: TensorFlow Hub models and Keras models may not be fully pickle-able
            # We'll cache metadata instead for Hub models
            metadata = {
                "model_name": model_name,
                "cached_at": datetime.utcnow().isoformat(),
                "model_info": model_info,
            }

            self.redis_manager.set_cache(
                cache_key, metadata, expires_in_seconds=86400
            )  # 24 hour TTL
            logger.info(f"Model metadata for {model_name} cached in Redis")
            return True
        except Exception as e:
            logger.warning(f"Could not save model to Redis: {e}")
            return False

    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """Get information about a loaded model"""
        return self.model_info.get(model_name)

    def list_available_models(self, model_type: str = None) -> Dict[str, Dict]:
        """List available models"""
        return ModelRegistry.list_models(model_type)

    def clear_cache(self) -> bool:
        """Clear in-memory model cache"""
        try:
            self.loaded_models.clear()
            self.model_info.clear()
            logger.info("Model cache cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "loaded_models": list(self.loaded_models.keys()),
            "model_count": len(self.loaded_models),
            "cached_in_redis": self.cache_models,
            "redis_connected": (
                self.redis_manager.is_connected() if self.redis_manager else False
            ),
            "model_info": self.model_info,
        }


class InferencePreprocessor:
    """Preprocessing for model inference"""

    @staticmethod
    def preprocess_image(image, target_size: tuple = (224, 224)) -> Any:
        """
        Preprocess image for inference

        Args:
            image: Input image (numpy array)
            target_size: Target size (height, width)

        Returns:
            Preprocessed image
        """
        import cv2
        import numpy as np

        try:
            # Resize
            resized = cv2.resize(image, target_size)

            # Normalize to [0, 1]
            normalized = resized.astype("float32") / 255.0

            # Add batch dimension
            batched = np.expand_dims(normalized, axis=0)

            return batched
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return None

    @staticmethod
    def preprocess_frames(frames: list, target_size: tuple = (224, 224)) -> Any:
        """
        Preprocess multiple frames for inference

        Args:
            frames: List of frames
            target_size: Target size for each frame

        Returns:
            Batch of preprocessed frames
        """
        import numpy as np

        try:
            preprocessed = []
            for frame in frames:
                img = InferencePreprocessor.preprocess_image(frame, target_size)
                if img is not None:
                    preprocessed.append(img[0])  # Remove batch dim from each

            if preprocessed:
                return np.array(preprocessed)
            return None
        except Exception as e:
            logger.error(f"Error preprocessing frames: {e}")
            return None


# Singleton instance
_model_loader = None


def get_model_loader(cache_models: bool = True) -> MLModelLoader:
    """Get or create model loader singleton"""
    global _model_loader
    if _model_loader is None:
        _model_loader = MLModelLoader(cache_models=cache_models)
    return _model_loader


def list_available_models(model_type: str = None) -> Dict[str, Dict]:
    """List available models"""
    return ModelRegistry.list_models(model_type)


def get_default_model(model_type: str) -> str:
    """Get default model for type"""
    return ModelRegistry.get_default_model(model_type)
