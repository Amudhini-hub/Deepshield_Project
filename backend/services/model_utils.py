"""
Model Utilities for ML Model Management
Handles loading, initialization, and caching of ML models
"""

import logging
import os
from typing import Dict, Optional

from tensorflow import keras

logger = logging.getLogger(__name__)


class ModelManager:
    """Centralized ML model management"""

    _instances: Dict = {}

    @classmethod
    def get_deepfake_detector(cls, config: dict = None):
        """Get or create a DeepfakeDetector instance"""
        from deepfake_detection import DeepfakeDetector

        if "deepfake_detector" not in cls._instances:
            cls._instances["deepfake_detector"] = DeepfakeDetector(config)
        return cls._instances["deepfake_detector"]

    @classmethod
    def get_liveness_detector(cls, config: dict = None):
        """Get or create a LivenessDetector instance"""
        from liveness_detection import LivenessDetector

        if "liveness_detector" not in cls._instances:
            cls._instances["liveness_detector"] = LivenessDetector(config)
        return cls._instances["liveness_detector"]

    @classmethod
    def load_model(cls, model_path: str) -> Optional[keras.Model]:
        """Load a Keras model from file"""
        try:
            if os.path.exists(model_path):
                model = keras.models.load_model(model_path)
                logger.info(f"Model loaded successfully from {model_path}")
                return model
            else:
                logger.warning(f"Model file not found: {model_path}")
                return None
        except Exception as e:
            logger.error(f"Error loading model from {model_path}: {e}")
            return None

    @classmethod
    def save_model(cls, model: keras.Model, model_path: str) -> bool:
        """Save a Keras model to file"""
        try:
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            model.save(model_path)
            logger.info(f"Model saved successfully to {model_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving model to {model_path}: {e}")
            return False

    @classmethod
    def clear_cache(cls):
        """Clear all cached model instances"""
        cls._instances.clear()
        logger.info("Model cache cleared")


class ModelTrainer:
    """Utilities for training ML models"""

    @staticmethod
    def compile_deepfake_model(
        model: keras.Model, learning_rate: float = 0.001
    ) -> None:
        """Compile deepfake detection model"""
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
            loss="binary_crossentropy",
            metrics=["accuracy", keras.metrics.Precision(), keras.metrics.Recall()],
        )

    @staticmethod
    def compile_liveness_model(
        model: keras.Model, learning_rate: float = 0.001
    ) -> None:
        """Compile liveness detection model"""
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
            loss="categorical_crossentropy",
            metrics=["accuracy", keras.metrics.Precision(), keras.metrics.Recall()],
        )

    @staticmethod
    def create_training_callbacks(model_path: str) -> list:
        """Create callbacks for model training"""
        return [
            keras.callbacks.ModelCheckpoint(
                model_path, monitor="val_accuracy", save_best_only=True, verbose=1
            ),
            keras.callbacks.EarlyStopping(
                monitor="val_loss", patience=10, verbose=1, restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss", factor=0.5, patience=5, min_lr=1e-7, verbose=1
            ),
        ]


def initialize_models(config: dict = None) -> Dict:
    """Initialize all ML models"""
    logger.info("Initializing ML models...")

    try:
        deepfake_detector = ModelManager.get_deepfake_detector(config)
        liveness_detector = ModelManager.get_liveness_detector(config)

        logger.info("ML models initialized successfully")

        return {
            "deepfake_detector": deepfake_detector,
            "liveness_detector": liveness_detector,
        }
    except Exception as e:
        logger.error(f"Error initializing models: {e}")
        return {}


def get_model_info() -> Dict:
    """Get information about available models"""
    return {
        "deepfake_detection": {
            "models": ["MesoNet", "XceptionNet"],
            "ensemble": True,
            "fallback_methods": [
                "frequency_analysis",
                "compression_artifacts",
                "blend_detection",
                "face_consistency",
            ],
        },
        "liveness_detection": {
            "models": ["EfficientNetB3"],
            "ensemble": True,
            "detection_methods": [
                "neural_network",
                "blink_patterns",
                "micro_motions",
                "frequency_patterns",
                "RPPG",
            ],
        },
    }
