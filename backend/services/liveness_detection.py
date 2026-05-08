"""
Liveness Detection Service
Detects whether a face in video is alive (not a photograph, video replay, or mask)
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

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


class EfficientNetLiveness(keras.Model):
    """EfficientNet-based model for liveness detection"""

    def __init__(self, num_classes=2):
        super(EfficientNetLiveness, self).__init__()
        self.base_model = keras.applications.EfficientNetB3(
            weights="imagenet", include_top=False, input_shape=(224, 224, 3)
        )
        self.base_model.trainable = False

        self.global_avg = layers.GlobalAveragePooling2D()
        self.dropout1 = layers.Dropout(0.4)
        self.dense1 = layers.Dense(256, activation="relu")
        self.batch_norm = layers.BatchNormalization()
        self.dropout2 = layers.Dropout(0.3)
        self.dense2 = layers.Dense(128, activation="relu")
        self.output_layer = layers.Dense(num_classes, activation="softmax")

    def call(self, x, training=False):
        x = keras.applications.efficientnet.preprocess_input(x)
        x = self.base_model(x, training=False)
        x = self.global_avg(x)
        x = self.dropout1(x, training=training)
        x = self.dense1(x)
        x = self.batch_norm(x, training=training)
        x = self.dropout2(x, training=training)
        x = self.dense2(x)
        x = self.output_layer(x)
        return x


class LivenessDetector:
    """Main liveness detection engine"""

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
        self.liveness_model = None
        self._load_models()

    def _load_models(self):
        """Load or initialize pre-trained models"""
        try:
            liveness_path = os.path.join(self.models_dir, "liveness_model.h5")

            if os.path.exists(liveness_path):
                self.liveness_model = keras.models.load_model(liveness_path)
                logger.info("Liveness model loaded successfully")
            else:
                self.liveness_model = EfficientNetLiveness()
                logger.info("Liveness model initialized (untrained)")

        except Exception as e:
            logger.warning(
                f"Could not load liveness model: {e}. Using fallback detection."
            )
            self.liveness_model = None

    def detect_from_video_frames(self, frames: List[np.ndarray]) -> LivenessResult:
        """
        Detect liveness from video frames

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
            # Use neural network if available
            if self.liveness_model is not None:
                nn_score = self._neural_network_liveness(frames)
            else:
                nn_score = 0.5
        except Exception as e:
            logger.warning(f"Neural network liveness detection failed: {e}")
            nn_score = 0.5

        # Use multiple detection methods for robustness
        blink_score = self._detect_blink_patterns(frames)
        motion_score = self._detect_micro_motions(frames)
        frequency_score = self._detect_frequency_patterns(frames)
        rppg_score = self._detect_rppg(frames)

        # Weighted ensemble combination
        scores = {
            "neural_network": nn_score * 0.35,  # 35% weight
            "blink": blink_score * 0.20,  # 20% weight
            "motion": motion_score * 0.20,  # 20% weight
            "frequency": frequency_score * 0.15,  # 15% weight
            "rppg": rppg_score * 0.10,  # 10% weight
        }

        confidence = sum(scores.values())
        is_alive = confidence >= self.min_confidence

        return LivenessResult(
            is_alive=is_alive,
            confidence=float(confidence),
            challenge_type=LivenessChallenge.RANDOM_MOTION.value,
            details={
                "neural_network_score": float(scores["neural_network"]),
                "blink_score": float(blink_score),
                "motion_score": float(motion_score),
                "frequency_score": float(frequency_score),
                "rppg_score": float(rppg_score),
                "face_detected": self._has_face(frames[0]),
                "frame_variation": self._calculate_frame_variation(frames),
                "model_available": self.liveness_model is not None,
            },
            frame_count=len(frames),
        )

    def _neural_network_liveness(self, frames: List[np.ndarray]) -> float:
        """
        Use neural network for liveness detection

        Args:
            frames: List of video frames

        Returns:
            Liveness probability (0.0 - 1.0)
        """
        try:
            # Sample frames to reduce computation
            sample_indices = np.linspace(
                0, len(frames) - 1, min(8, len(frames)), dtype=int
            )
            sample_frames = [frames[i] for i in sample_indices]

            scores = []

            for frame in sample_frames:
                processed = self._preprocess_frame_liveness(frame)
                if processed is not None:
                    prediction = self.liveness_model(processed, training=False)
                    liveness_prob = float(
                        prediction[0][1]
                    )  # probability of being alive
                    scores.append(liveness_prob)

            if scores:
                return np.mean(scores)
            else:
                return 0.5

        except Exception as e:
            logger.warning(f"Neural network liveness detection error: {e}")
            return 0.5

    def _preprocess_frame_liveness(self, frame: np.ndarray) -> Optional[tf.Tensor]:
        """Preprocess frame for liveness model (224x224)"""
        try:
            # Convert BGR to RGB
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Resize to 224x224
            frame = cv2.resize(frame, (224, 224))
            # Add batch dimension
            frame = np.expand_dims(frame, 0)
            return tf.convert_to_tensor(frame.astype(np.float32))
        except Exception as e:
            logger.warning(f"Frame preprocessing error: {e}")
            return None

    def _detect_blink_patterns(self, frames: List[np.ndarray]) -> float:
        """Detect eye blinking patterns"""
        try:
            blink_count = 0
            eye_closure_frames = 0

            for frame in frames:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

                if len(faces) > 0:
                    x, y, w, h = faces[0]
                    roi = gray[y : y + h, x : x + w]
                    eyes = self.eye_cascade.detectMultiScale(roi)

                    if len(eyes) < 2:
                        eye_closure_frames += 1
                    else:
                        if eye_closure_frames > 2:
                            blink_count += 1
                        eye_closure_frames = 0

            # Score based on blink count (typically 1-3 blinks in video)
            normalized_blinks = min(blink_count, 3) / 3.0
            return min(0.95, normalized_blinks + 0.3)

        except Exception as e:
            logger.error(f"Error in blink detection: {e}")
            return 0.3

    def _detect_micro_motions(self, frames: List[np.ndarray]) -> float:
        """Detect natural micro-motions"""
        try:
            if len(frames) < 2:
                return 0.0

            motion_frames = 0

            for i in range(1, min(len(frames), 20)):  # Sample up to 20 frames
                prev_gray = cv2.cvtColor(frames[i - 1], cv2.COLOR_BGR2GRAY)
                curr_gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)

                # Calculate optical flow
                try:
                    flow = cv2.calcOpticalFlowFarneback(
                        prev_gray, curr_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
                    )

                    # Magnitude and angle
                    magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])

                    # Motion score
                    motion_avg = np.mean(magnitude)
                    if 0.1 < motion_avg < 5.0:  # Natural motion range
                        motion_frames += 1
                except:
                    pass

            return min(motion_frames / min(len(frames), 20), 0.95)

        except Exception as e:
            logger.error(f"Error in motion detection: {e}")
            return 0.3

    def _detect_frequency_patterns(self, frames: List[np.ndarray]) -> float:
        """Detect frequency patterns to identify replay/print attacks"""
        try:
            if len(frames) < 2:
                return 0.5

            # Analyze color channel variation
            variation_scores = []

            for frame in frames:
                # Convert to LAB color space
                lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

                # Calculate channel entropy
                for channel in cv2.split(lab):
                    entropy = self._calculate_entropy(channel)
                    variation_scores.append(entropy)

            if not variation_scores:
                return 0.3

            avg_variation = np.mean(variation_scores)
            # Live faces typically have entropy between 4.5-7.5
            if 4.5 <= avg_variation <= 7.5:
                return 0.9
            elif 3.0 <= avg_variation <= 8.0:
                return 0.6
            else:
                return 0.2

        except Exception as e:
            logger.error(f"Error in frequency pattern detection: {e}")
            return 0.3

    def _detect_rppg(self, frames: List[np.ndarray]) -> float:
        """Detect Remote Photoplethysmography (heart rate) signal"""
        try:
            if len(frames) < 10:
                return 0.5

            # Extract ROI from face area
            gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) == 0:
                return 0.2

            x, y, w, h = faces[0]
            roi_x, roi_y = int(x + w * 0.2), int(y + h * 0.3)
            roi_w, roi_h = int(w * 0.6), int(h * 0.4)

            # Extract color signals from ROI
            r_channel = []
            g_channel = []
            b_channel = []

            for frame in frames:
                roi = frame[roi_y : roi_y + roi_h, roi_x : roi_x + roi_w]
                b, g, r = cv2.split(roi)
                r_channel.append(np.mean(r))
                g_channel.append(np.mean(g))
                b_channel.append(np.mean(b))

            # Compute normalized signals
            r_norm = (np.array(r_channel) - np.mean(r_channel)) / (
                np.std(r_channel) + 1e-8
            )
            g_norm = (np.array(g_channel) - np.mean(g_channel)) / (
                np.std(g_channel) + 1e-8
            )
            b_norm = (np.array(b_channel) - np.mean(b_channel)) / (
                np.std(b_channel) + 1e-8
            )

            # Weighted combination (Green dominates for RPPG)
            rppg_signal = 3 * g_norm - 2 * r_norm

            # Compute FFT to detect periodic signals
            fft = np.abs(np.fft.fft(rppg_signal))

            # Check for periodicity in heart rate range (40-200 BPM)
            # At 30 fps: 0.67-3.33 Hz
            heart_rate_band = fft[2:10]  # Approximate frequency range

            if np.max(heart_rate_band) > np.mean(fft) * 2:
                return 0.85  # Strong RPPG signal
            elif np.max(heart_rate_band) > np.mean(fft) * 1.5:
                return 0.6  # Moderate RPPG signal
            else:
                return 0.3  # Weak or no RPPG signal

        except Exception as e:
            logger.error(f"Error in RPPG detection: {e}")
            return 0.5

    def _has_face(self, frame: np.ndarray) -> bool:
        """Check if frame contains a face"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            return len(faces) > 0
        except:
            return False

    def _calculate_frame_variation(self, frames: List[np.ndarray]) -> float:
        """Calculate variation between frames"""
        try:
            if len(frames) < 2:
                return 0.0

            variations = []
            for i in range(1, len(frames)):
                diff = cv2.absdiff(frames[i - 1], frames[i])
                mean_diff = np.mean(diff)
                variations.append(mean_diff)

            return float(np.mean(variations)) if variations else 0.0

        except Exception as e:
            logger.error(f"Error calculating frame variation: {e}")
            return 0.0

    @staticmethod
    def _calculate_entropy(channel: np.ndarray) -> float:
        """Calculate entropy of a channel"""
        hist = cv2.calcHist([channel], [0], None, [256], [0, 256])
        hist = hist.flatten() / hist.sum()
        entropy = -np.sum(hist * np.log2(hist + 1e-10))
        return entropy


class ChallengeGenerator:
    """Generates random liveness challenges"""

    @staticmethod
    def generate_challenge() -> Dict:
        """Generate a random liveness challenge"""
        import random

        challenge_type = random.choice(list(LivenessChallenge))

        challenges = {
            LivenessChallenge.EYE_GAZE: {
                "type": "eye_gaze",
                "instruction": "Look at the dot and move your eyes to follow it",
                "duration": 5,
            },
            LivenessChallenge.HEAD_MOVEMENT: {
                "type": "head_movement",
                "instruction": "Slowly turn your head left, then right",
                "duration": 6,
            },
            LivenessChallenge.BLINK_DETECTION: {
                "type": "blink_detection",
                "instruction": "Blink 3 times naturally",
                "duration": 4,
            },
            LivenessChallenge.RANDOM_MOTION: {
                "type": "random_motion",
                "instruction": "Keep your face in frame and maintain natural expressions",
                "duration": 5,
            },
        }

        return challenges[challenge_type]
