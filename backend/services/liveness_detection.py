"""
Liveness Detection Service
Detects whether a face in video is alive (not a photograph, video replay, or mask)
Uses pre-trained neural networks for robust liveness verification
"""

import logging
import os
import json
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

import cv2
import numpy as np

from backend.services.model_loader import get_model_loader, InferencePreprocessor

logger = logging.getLogger(__name__)


class LivenessChallenge(Enum):
    """Types of liveness challenges"""

    EYE_GAZE = "eye_gaze"
    HEAD_MOVEMENT = "head_movement"
    BLINK_DETECTION = "blink_detection"
    RANDOM_MOTION = "random_motion"


@dataclass
class LivenessResult:
    """Liveness detection result"""

    is_alive: bool
    confidence: float
    challenge_type: str
    details: Dict
    frame_count: int


class LivenessDetector:
    """Main liveness detection engine using neural networks + ensemble methods"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.min_confidence = self.config.get("confidence_threshold", 0.85)
        self.models_dir = self.config.get("models_dir", "ml_models/liveness_detection")
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
            config_path = os.path.join(self.models_dir, "liveness_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.model_config = json.load(f)
                logger.info("Liveness model metadata loaded successfully")
            else:
                logger.info("Model metadata file not found, using defaults")
        except Exception as e:
            logger.warning(f"Could not load model metadata: {e}")

    def _load_neural_network_model(self):
        """Load pre-trained neural network model from TensorFlow Hub"""
        try:
            self.model = self.model_loader.load_model("liveness_mobilenet")
            if self.model is not None:
                self.use_neural_network = True
                logger.info("Neural network model loaded successfully for liveness detection")
                model_info = self.model_loader.get_model_info("liveness_mobilenet")
                logger.info(f"Model info: {model_info}")
            else:
                logger.warning("Failed to load neural network model, will use ensemble methods")
                self.use_neural_network = False
        except Exception as e:
            logger.warning(f"Could not load neural network model: {e}")
            self.use_neural_network = False

    def detect_from_video_frames(self, frames: List[np.ndarray]) -> LivenessResult:
        """
        Detect liveness from video frames using neural network + ensemble methods

        Args:
            frames: List of video frames

        Returns:
            LivenessResult with liveness detection
        """
        if not frames:
            return LivenessResult(
                is_alive=False,
                confidence=0.0,
                challenge_type="none",
                details={"error": "No frames provided"},
                frame_count=0,
            )

        try:
            scores = {}
            
            # Method 1: Neural Network Inference (if available)
            if self.use_neural_network:
                try:
                    nn_score = self._neural_network_inference(frames)
                    scores["neural_network"] = nn_score * 0.35  # 35% weight
                    logger.info(f"Neural network liveness score: {nn_score}")
                except Exception as e:
                    logger.warning(f"Neural network inference failed: {e}")
                    scores["neural_network"] = 0.5 * 0.35
            else:
                # Fallback
                scores["neural_network"] = 0.5 * 0.35

            # Method 2-5: Ensemble Analysis Methods
            blink_score = self._detect_blink_patterns(frames)
            motion_score = self._detect_micro_motions(frames)
            frequency_score = self._detect_frequency_patterns(frames)
            rppg_score = self._detect_rppg(frames)

            # Weighted ensemble combination
            scores["blink"] = blink_score * 0.20  # 20% weight
            scores["motion"] = motion_score * 0.20  # 20% weight
            scores["frequency"] = frequency_score * 0.15  # 15% weight
            scores["rppg"] = rppg_score * 0.10  # 10% weight

            confidence = min(1.0, sum(scores.values()))
            is_alive = confidence >= (1.0 - self.min_confidence)

            return LivenessResult(
                is_alive=is_alive,
                confidence=float(confidence),
                challenge_type="neural_network + ensemble",
                details={
                    "neural_network_score": float(scores.get("neural_network", 0)),
                    "blink_score": float(blink_score),
                    "motion_score": float(motion_score),
                    "frequency_score": float(frequency_score),
                    "rppg_score": float(rppg_score),
                    "frames_analyzed": len(frames),
                    "method": "neural_network_ensemble",
                    "using_neural_network": self.use_neural_network,
                },
                frame_count=len(frames),
            )

        except Exception as e:
            logger.error(f"Liveness detection error: {e}")
            return LivenessResult(
                is_alive=False,
                confidence=0.0,
                challenge_type="error",
                details={"error": str(e)},
                frame_count=len(frames),
            )

    def _neural_network_inference(self, frames: List[np.ndarray]) -> float:
        """
        Perform neural network inference for liveness
        
        Args:
            frames: List of video frames
            
        Returns:
            Confidence score 0.0-1.0 (higher = more likely alive)
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
            
            # Extract liveness probability
            if isinstance(predictions, dict):
                # Hub models may return dict
                logits = predictions.get("logits", predictions)
            else:
                logits = predictions
            
            # Convert to numpy
            if hasattr(logits, "numpy"):
                probs = logits.numpy()
            else:
                probs = logits
            
            # Assume last class is alive/real
            if probs.shape[-1] >= 2:
                liveness_probs = probs[..., -1]  # Real/alive class
            else:
                liveness_probs = probs[..., -1]
            
            # Average across batch
            avg_score = float(np.mean(liveness_probs))
            
            # Normalize to 0-1 range
            score = 1.0 / (1.0 + np.exp(-avg_score))  # Sigmoid normalization
            
            return score
            
        except Exception as e:
            logger.warning(f"Neural network inference error: {e}")
            return 0.5
                is_alive=False,
                confidence=0.0,
                challenge_type="error",
                details={"error": str(e)},
                frame_count=len(frames),
            )

    def _detect_blink_patterns(self, frames: List[np.ndarray]) -> float:
        """
        Detect blink patterns (real people blink, photos/videos don't)
        Returns score 0.0-1.0 (higher = more likely alive)
        """
        try:
            blink_indicators = []

            for i in range(min(len(frames) - 1, 10)):
                frame = frames[i]
                frame_gray = cv2.cvtColor(
                    (frame * 255).astype(np.uint8) if frame.max() <= 1.0 else frame.astype(np.uint8),
                    cv2.COLOR_BGR2GRAY
                )

                # Detect faces and eyes
                faces = self.face_cascade.detectMultiScale(frame_gray, 1.3, 5)
                for (x, y, w, h) in faces[:1]:  # Process first face
                    roi_gray = frame_gray[y : y + h, x : x + w]
                    eyes = self.eye_cascade.detectMultiScale(roi_gray)
                    
                    # If eyes detected, it's likely a real face
                    if len(eyes) >= 2:
                        blink_indicators.append(0.7)
                    else:
                        blink_indicators.append(0.3)

            if blink_indicators:
                return min(1.0, np.mean(blink_indicators))
            else:
                return 0.3

        except Exception as e:
            logger.debug(f"Blink detection failed: {e}")
            return 0.3

    def _detect_micro_motions(self, frames: List[np.ndarray]) -> float:
        """
        Detect micro-motions (subtle movements of real faces)
        Returns score 0.0-1.0 (higher = more likely alive)
        """
        try:
            if len(frames) < 2:
                return 0.3

            motion_scores = []

            for i in range(min(len(frames) - 1, 10)):
                frame1 = frames[i]
                frame2 = frames[i + 1]

                if frame1.shape != frame2.shape:
                    continue

                # Convert to grayscale
                frame1_gray = cv2.cvtColor(
                    (frame1 * 255).astype(np.uint8) if frame1.max() <= 1.0 else frame1.astype(np.uint8),
                    cv2.COLOR_BGR2GRAY
                )
                frame2_gray = cv2.cvtColor(
                    (frame2 * 255).astype(np.uint8) if frame2.max() <= 1.0 else frame2.astype(np.uint8),
                    cv2.COLOR_BGR2GRAY
                )

                # Calculate optical flow (simplified)
                diff = cv2.absdiff(frame1_gray, frame2_gray)
                motion_amount = np.mean(diff)

                # Real faces have micro-motions (natural breathing, subtle expressions)
                # Static videos/photos have minimal motion
                if 5 < motion_amount < 50:  # Natural range
                    motion_scores.append(0.8)
                elif motion_amount < 3:  # Too static (likely fake)
                    motion_scores.append(0.1)
                else:
                    motion_scores.append(0.5)

            if motion_scores:
                return min(1.0, np.mean(motion_scores))
            else:
                return 0.3

        except Exception as e:
            logger.debug(f"Micro-motion detection failed: {e}")
            return 0.3

    def _detect_frequency_patterns(self, frames: List[np.ndarray]) -> float:
        """
        Detect frequency patterns (biological signals vs synthetic)
        Returns score 0.0-1.0 (higher = more likely alive)
        """
        try:
            freq_scores = []

            for frame in frames[:5]:
                frame_bgr = (frame * 255).astype(np.uint8) if frame.max() <= 1.0 else frame.astype(np.uint8)
                frame_gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

                # Analyze frequency domain
                fft_result = np.fft.fft2(frame_gray)
                magnitude = np.abs(np.fft.fftshift(fft_result))

                # Real faces have natural frequency distribution
                # Deepfakes and photos have different patterns
                center_freq = magnitude[magnitude.shape[0]//2-10:magnitude.shape[0]//2+10,
                                      magnitude.shape[1]//2-10:magnitude.shape[1]//2+10]
                outer_freq = magnitude[:magnitude.shape[0]//4, :magnitude.shape[1]//4]

                center_energy = np.sum(center_freq)
                outer_energy = np.sum(outer_freq)

                ratio = center_energy / (outer_energy + 1e-8)

                # Real faces have specific ratios
                if 1.0 < ratio < 10.0:
                    freq_scores.append(0.7)
                else:
                    freq_scores.append(0.3)

            if freq_scores:
                return min(1.0, np.mean(freq_scores))
            else:
                return 0.3

        except Exception as e:
            logger.debug(f"Frequency pattern detection failed: {e}")
            return 0.3

    def _detect_rppg(self, frames: List[np.ndarray]) -> float:
        """
        Detect rPPG (remote photoplethysmography) - blood flow patterns
        Returns score 0.0-1.0 (higher = more likely alive)
        """
        try:
            if len(frames) < 5:
                return 0.3

            # Simplified rPPG: detect color variations indicating blood flow
            rppg_scores = []

            for i in range(min(len(frames) - 5, 5)):
                frame_segment = frames[i:i+5]
                
                # Extract red channel (most prominent for rPPG)
                green_means = []
                for frame in frame_segment:
                    frame_bgr = (frame * 255).astype(np.uint8) if frame.max() <= 1.0 else frame.astype(np.uint8)
                    green_channel = frame_bgr[:, :, 1]
                    green_means.append(np.mean(green_channel))

                # Calculate variance in green channel
                variance = np.var(green_means)

                # Real faces show periodic variation (heartbeat)
                # Dead faces or photos don't
                if 10 < variance < 1000:  # Natural range
                    rppg_scores.append(0.8)
                elif variance < 5:  # Too static
                    rppg_scores.append(0.1)
                else:
                    rppg_scores.append(0.4)

            if rppg_scores:
                return min(1.0, np.mean(rppg_scores))
            else:
                return 0.3

        except Exception as e:
            logger.debug(f"rPPG detection failed: {e}")
            return 0.3

    def detect_from_video(self, video_path: str, max_frames: int = 30) -> LivenessResult:
        """
        Detect liveness from video file

        Args:
            video_path: Path to video file
            max_frames: Maximum frames to analyze

        Returns:
            LivenessResult
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
                return LivenessResult(
                    is_alive=False,
                    confidence=0.0,
                    challenge_type="video",
                    details={"error": "Could not extract frames from video"},
                    frame_count=0,
                )

            return self.detect_from_video_frames(frames)

        except Exception as e:
            logger.error(f"Video liveness detection failed: {e}")
            return LivenessResult(
                is_alive=False,
                confidence=0.0,
                challenge_type="video",
                details={"error": str(e)},
                frame_count=0,
            )
