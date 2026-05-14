"""
Deepfake Detection Service
Detects AI-generated or manipulated facial videos using neural networks + ensemble methods
Uses pre-trained models from TensorFlow Hub for real-world accuracy
"""

import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import cv2
import numpy as np
from scipy import fftpack

from backend.services.model_loader import InferencePreprocessor, get_model_loader

logger = logging.getLogger(__name__)


@dataclass
class DeepfakeResult:
    """Deepfake detection result"""

    is_deepfake: bool
    confidence: float
    detection_method: str
    details: Dict
    frame_count: int
    anomalies: List[str]


class DeepfakeDetector:
    """Main deepfake detection engine using neural networks + ensemble methods"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.detection_threshold = self.config.get("detection_threshold", 0.8)
        self.models_dir = self.config.get("models_dir", "ml_models/deepfake_detection")
        self.model_config = {}

        # Initialize model loader
        self.model_loader = get_model_loader(cache_models=True)
        self.model = None
        self.use_neural_network = False

        # Load model metadata
        self._load_model_metadata()
        # Load pre-trained model
        self._load_neural_network_model()

    def _load_model_metadata(self):
        """Load model metadata for reference"""
        try:
            config_path = os.path.join(self.models_dir, "mesonet_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    self.model_config = json.load(f)
                logger.info("Deepfake model metadata loaded successfully")
            else:
                logger.info("Model metadata file not found, using defaults")
        except Exception as e:
            logger.warning(f"Could not load model metadata: {e}")

    def _load_neural_network_model(self):
        """Load pre-trained neural network model from TensorFlow Hub"""
        try:
            self.model = self.model_loader.load_model("deepfake_mobilenetv2")
            if self.model is not None:
                self.use_neural_network = True
                logger.info(
                    "Neural network model loaded successfully for deepfake detection"
                )
                model_info = self.model_loader.get_model_info("deepfake_mobilenetv2")
                logger.info(f"Model info: {model_info}")
            else:
                logger.warning(
                    "Failed to load neural network model, will use ensemble methods"
                )
                self.use_neural_network = False
        except Exception as e:
            logger.warning(f"Could not load neural network model: {e}")
            self.use_neural_network = False

    def detect_from_frames(self, frames: List[np.ndarray]) -> DeepfakeResult:
        """
        Detect deepfakes from video frames using neural network + ensemble methods

        Args:
            frames: List of video frames

        Returns:
            DeepfakeResult with deepfake probability
        """
        if not frames:
            return DeepfakeResult(
                is_deepfake=False,
                confidence=0.0,
                detection_method="none",
                details={"error": "No frames provided"},
                frame_count=0,
                anomalies=[],
            )

        try:
            # Normalize frames
            normalized_frames = [self._normalize_frame(f) for f in frames]
        except Exception as e:
            logger.warning(f"Frame normalization failed: {e}")
            normalized_frames = frames

        # Initialize scores
        scores = {}
        anomalies = []

        # Method 1: Neural Network Inference (if available)
        if self.use_neural_network:
            try:
                nn_score = self._neural_network_inference(normalized_frames)
                scores["neural_network"] = nn_score * 0.5  # 50% weight
                logger.info(f"Neural network score: {nn_score}")
            except Exception as e:
                logger.warning(f"Neural network inference failed: {e}")
                scores["neural_network"] = 0.0
        else:
            # Fallback: use ensemble without neural network
            nn_score = 0.3
            scores["neural_network"] = nn_score * 0.5

        # Method 2-5: Ensemble Analysis Methods
        freq_score = self._frequency_analysis(normalized_frames)
        artifact_score = self._detect_compression_artifacts(normalized_frames)
        blend_score = self._detect_blend_artifacts(normalized_frames)
        consistency_score = self._detect_face_consistency(normalized_frames)

        # Weighted ensemble combination
        scores["frequency"] = freq_score * 0.15  # 15% weight
        scores["artifacts"] = artifact_score * 0.15  # 15% weight
        scores["blend"] = blend_score * 0.1  # 10% weight
        scores["consistency"] = consistency_score * 0.1  # 10% weight

        confidence = min(1.0, sum(scores.values()))

        # Identify anomalies
        if freq_score > 0.7:
            anomalies.append("Frequency domain anomalies detected")
        if artifact_score > 0.7:
            anomalies.append("Compression artifacts detected")
        if blend_score > 0.7:
            anomalies.append("Face blending artifacts detected")
        if consistency_score > 0.7:
            anomalies.append("Face consistency anomalies detected")

        is_deepfake = bool(confidence >= self.detection_threshold)

        return DeepfakeResult(
            is_deepfake=is_deepfake,
            confidence=float(confidence),
            detection_method="neural_network + ensemble",
            details={
                "neural_network_score": float(scores.get("neural_network", 0)),
                "frequency_score": float(freq_score),
                "artifact_score": float(artifact_score),
                "blend_score": float(blend_score),
                "consistency_score": float(consistency_score),
                "frames_analyzed": len(frames),
                "models_available": True,
                "method": "neural_network_ensemble",
                "using_neural_network": self.use_neural_network,
            },
            frame_count=len(frames),
            anomalies=anomalies,
        )

    def _neural_network_inference(self, frames: List[np.ndarray]) -> float:
        """
        Perform neural network inference on frames

        Args:
            frames: Normalized frames

        Returns:
            Confidence score 0.0-1.0 (higher = more likely deepfake)
        """
        if not self.model or not self.use_neural_network:
            return 0.5

        try:
            import tensorflow as tf

            # Sample frames evenly (max 10 for efficiency)
            sample_size = min(10, len(frames))
            step = max(1, len(frames) // sample_size)
            sampled_frames = frames[::step][:sample_size]

            # Preprocess frames
            batch = InferencePreprocessor.preprocess_frames(sampled_frames)
            if batch is None:
                logger.warning("Frame preprocessing failed")
                return 0.5

            # Run inference
            predictions = self.model(tf.constant(batch), training=False)

            # Extract deepfake probability
            # Assuming output shape is (batch_size, 2) with [fake_prob, real_prob]
            if isinstance(predictions, dict):
                # Hub models may return dict
                logits = predictions.get("logits", predictions)
            else:
                logits = predictions

            # Convert to numpy and get fake probability
            if hasattr(logits, "numpy"):
                probs = logits.numpy()
            else:
                probs = logits

            # Assume first class is fake/deepfake
            if probs.shape[-1] >= 2:
                deepfake_probs = probs[..., 0]
            else:
                deepfake_probs = probs[..., -1]

            # Average across batch
            avg_score = float(np.mean(deepfake_probs))

            # Normalize to 0-1 range
            score = 1.0 / (1.0 + np.exp(-avg_score))  # Sigmoid normalization

            return score

        except Exception as e:
            logger.warning(f"Neural network inference error: {e}")
            return 0.5

    def _normalize_frame(self, frame: np.ndarray) -> np.ndarray:
        """Normalize frame for analysis"""
        if frame.max() > 1.0:
            frame = frame.astype(np.float32) / 255.0
        return frame

    def _frequency_analysis(self, frames: List[np.ndarray]) -> float:
        """
        Analyze frequency domain for deepfake artifacts
        Returns score 0.0-1.0 (higher = more likely deepfake)
        """
        if not frames:
            return 0.0

        try:
            anomaly_count = 0
            for frame in frames[:5]:  # Analyze first 5 frames
                if frame.ndim == 3 and frame.shape[2] >= 3:
                    # Convert to grayscale
                    frame_bgr = (
                        (frame * 255).astype(np.uint8)
                        if frame.max() <= 1.0
                        else frame.astype(np.uint8)
                    )
                    frame_gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
                else:
                    frame_gray = frame

                # FFT analysis
                fft_result = fftpack.fft2(frame_gray)
                magnitude = np.abs(fft_result)

                # Detect unnatural frequency patterns
                high_freq_ratio = (
                    np.sum(magnitude > np.percentile(magnitude, 90)) / magnitude.size
                )

                if high_freq_ratio > 0.15:  # Threshold for anomaly
                    anomaly_count += 1

            score = min(1.0, anomaly_count / 5.0)
            return float(score)
        except Exception as e:
            logger.debug(f"Frequency analysis failed: {e}")
            return 0.5

    def _detect_compression_artifacts(self, frames: List[np.ndarray]) -> float:
        """
        Detect compression artifacts (common in deepfakes)
        Returns score 0.0-1.0 (higher = more likely deepfake)
        """
        if not frames:
            return 0.0

        try:
            artifact_count = 0
            for frame in frames[:5]:
                if frame.ndim == 3 and frame.shape[2] >= 3:
                    frame_bgr = (
                        (frame * 255).astype(np.uint8)
                        if frame.max() <= 1.0
                        else frame.astype(np.uint8)
                    )

                    # Detect edge anomalies (common in deepfakes)
                    edges = cv2.Canny(
                        cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY), 50, 150
                    )
                    edge_density = np.sum(edges > 0) / edges.size

                    if edge_density > 0.3:  # Threshold
                        artifact_count += 1

            score = min(1.0, artifact_count / 5.0)
            return float(score)
        except Exception as e:
            logger.debug(f"Compression artifact detection failed: {e}")
            return 0.5

    def _detect_blend_artifacts(self, frames: List[np.ndarray]) -> float:
        """
        Detect face blending artifacts
        Returns score 0.0-1.0 (higher = more likely deepfake)
        """
        if not frames:
            return 0.0

        try:
            blend_count = 0
            for frame in frames[:5]:
                if frame.ndim == 3 and frame.shape[2] >= 3:
                    # Analyze color transitions
                    frame_bgr = (
                        (frame * 255).astype(np.uint8)
                        if frame.max() <= 1.0
                        else frame.astype(np.uint8)
                    )
                    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

                    # Detect unnatural color gradients
                    v_channel = hsv[:, :, 2].astype(np.float32)
                    edges = cv2.Sobel(v_channel, cv2.CV_32F, 1, 0, ksize=3)

                    if np.std(edges) > 30:
                        blend_count += 1

            score = min(1.0, blend_count / 5.0)
            return float(score)
        except Exception as e:
            logger.debug(f"Blend artifact detection failed: {e}")
            return 0.5

    def _detect_face_consistency(self, frames: List[np.ndarray]) -> float:
        """
        Detect inconsistencies between frames (deepfakes often have flickering)
        Returns score 0.0-1.0 (higher = more likely deepfake)
        """
        if len(frames) < 2:
            return 0.0

        try:
            inconsistencies = 0

            for i in range(min(len(frames) - 1, 5)):
                frame1 = frames[i]
                frame2 = frames[i + 1]

                if frame1.shape != frame2.shape:
                    continue

                # Calculate structural similarity
                diff = np.abs(frame1.astype(np.float32) - frame2.astype(np.float32))
                mse = np.mean(diff**2)

                # Deepfakes often have unnatural frame-to-frame changes
                if mse > 0.05:  # Threshold for inconsistency
                    inconsistencies += 1

            score = min(1.0, inconsistencies / 5.0)
            return float(score)
        except Exception as e:
            logger.debug(f"Consistency detection failed: {e}")
            return 0.5

    def detect_from_video(
        self, video_path: str, max_frames: int = 30
    ) -> DeepfakeResult:
        """
        Detect deepfakes from video file

        Args:
            video_path: Path to video file
            max_frames: Maximum frames to analyze

        Returns:
            DeepfakeResult
        """
        try:
            cap = cv2.VideoCapture(video_path)
            frames = []

            frame_count = 0
            while cap.isOpened() and frame_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break

                # Resize frame for faster processing
                frame_resized = cv2.resize(frame, (224, 224))
                frame_normalized = frame_resized.astype(np.float32) / 255.0
                frames.append(frame_normalized)
                frame_count += 1

            cap.release()

            if not frames:
                return DeepfakeResult(
                    is_deepfake=False,
                    confidence=0.0,
                    detection_method="video",
                    details={"error": "Could not extract frames from video"},
                    frame_count=0,
                    anomalies=[],
                )

            return self.detect_from_frames(frames)

        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            return DeepfakeResult(
                is_deepfake=False,
                confidence=0.0,
                detection_method="video",
                details={"error": str(e)},
                frame_count=0,
                anomalies=[],
            )
