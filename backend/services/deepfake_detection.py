"""
Deepfake Detection Service
Detects AI-generated or manipulated facial videos using ensemble of CNN models
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import os

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


class MesoNet(keras.Model):
    """MesoNet for Deepfake Detection - Lightweight CNN"""
    
    def __init__(self, num_classes=2):
        super(MesoNet, self).__init__()
        
        self.conv1 = layers.Conv2D(8, (3, 3), padding='same', activation='relu')
        self.batch1 = layers.BatchNormalization()
        self.pool1 = layers.MaxPooling2D((4, 4))
        
        self.conv2 = layers.Conv2D(8, (5, 5), padding='same', activation='relu')
        self.batch2 = layers.BatchNormalization()
        self.pool2 = layers.MaxPooling2D((4, 4))
        
        self.conv3 = layers.Conv2D(16, (5, 5), padding='same', activation='relu')
        self.batch3 = layers.BatchNormalization()
        self.pool3 = layers.MaxPooling2D((4, 4))
        
        self.conv4 = layers.Conv2D(16, (5, 5), padding='same', activation='relu')
        self.batch4 = layers.BatchNormalization()
        self.pool4 = layers.MaxPooling2D((4, 4))
        
        self.flatten = layers.Flatten()
        self.dropout = layers.Dropout(0.5)
        self.dense1 = layers.Dense(16, activation='relu')
        self.dense2 = layers.Dense(num_classes, activation='softmax')
    
    def call(self, x, training=False):
        x = self.conv1(x)
        x = self.batch1(x, training=training)
        x = self.pool1(x)
        
        x = self.conv2(x)
        x = self.batch2(x, training=training)
        x = self.pool2(x)
        
        x = self.conv3(x)
        x = self.batch3(x, training=training)
        x = self.pool3(x)
        
        x = self.conv4(x)
        x = self.batch4(x, training=training)
        x = self.pool4(x)
        
        x = self.flatten(x)
        x = self.dropout(x, training=training)
        x = self.dense1(x)
        x = self.dense2(x)
        return x


class XceptionNetLite(keras.Model):
    """XceptionNet-based architecture for deepfake detection"""
    
    def __init__(self, num_classes=2):
        super(XceptionNetLite, self).__init__()
        self.base_model = keras.applications.Xception(
            weights='imagenet',
            include_top=False,
            input_shape=(299, 299, 3)
        )
        self.base_model.trainable = False
        
        self.global_avg = layers.GlobalAveragePooling2D()
        self.dropout1 = layers.Dropout(0.5)
        self.dense1 = layers.Dense(512, activation='relu')
        self.batch_norm = layers.BatchNormalization()
        self.dropout2 = layers.Dropout(0.5)
        self.output_layer = layers.Dense(num_classes, activation='softmax')
    
    def call(self, x, training=False):
        x = keras.applications.xception.preprocess_input(x)
        x = self.base_model(x, training=False)
        x = self.global_avg(x)
        x = self.dropout1(x, training=training)
        x = self.dense1(x)
        x = self.batch_norm(x, training=training)
        x = self.dropout2(x, training=training)
        x = self.output_layer(x)
        return x


class DeepfakeDetector:
    """Main deepfake detection engine using ensemble methods"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.detection_threshold = self.config.get('detection_threshold', 0.8)
        self.models_dir = self.config.get('models_dir', 'ml_models/deepfake_detection')
        self.mesonet_model = None
        self.xception_model = None
        self._load_models()
        
    def _load_models(self):
        """Load or initialize pre-trained models"""
        try:
            # Try to load pre-trained models if they exist
            mesonet_path = os.path.join(self.models_dir, 'mesonet_model.h5')
            xception_path = os.path.join(self.models_dir, 'xception_model.h5')
            
            if os.path.exists(mesonet_path):
                self.mesonet_model = keras.models.load_model(mesonet_path)
                logger.info("MesoNet model loaded successfully")
            else:
                self.mesonet_model = MesoNet()
                logger.info("MesoNet model initialized (untrained)")
            
            if os.path.exists(xception_path):
                self.xception_model = keras.models.load_model(xception_path)
                logger.info("XceptionNet model loaded successfully")
            else:
                self.xception_model = XceptionNetLite()
                logger.info("XceptionNet model initialized (untrained)")
                
        except Exception as e:
            logger.warning(f"Could not load models: {e}. Using fallback detection.")
            self.mesonet_model = None
            self.xception_model = None
        
    def detect_from_frames(self, frames: List[np.ndarray]) -> DeepfakeResult:
        """
        Detect deepfakes from video frames using ensemble methods
        
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
                anomalies=[]
            )
        
        try:
            # Use neural network ensemble if models are available
            if self.mesonet_model is not None or self.xception_model is not None:
                nn_score = self._neural_network_detection(frames)
            else:
                nn_score = 0.5
        except Exception as e:
            logger.warning(f"Neural network detection failed: {e}")
            nn_score = 0.5
        
        # Use multiple detection methods for robustness
        freq_score = self._frequency_analysis(frames)
        artifact_score = self._detect_compression_artifacts(frames)
        blend_score = self._detect_blend_artifacts(frames)
        consistency_score = self._detect_face_consistency(frames)
        
        # Weighted ensemble combination
        scores = {
            'neural_network': nn_score * 0.4,      # 40% weight
            'frequency': freq_score * 0.2,          # 20% weight
            'artifacts': artifact_score * 0.2,      # 20% weight
            'blend': blend_score * 0.1,             # 10% weight
            'consistency': consistency_score * 0.1  # 10% weight
        }
        
        confidence = sum(scores.values())
        
        # Identify anomalies
        anomalies = []
        if scores['neural_network'] > 0.3:
            anomalies.append("Neural network detected suspicious patterns")
        if freq_score > 0.7:
            anomalies.append("Frequency domain anomalies detected")
        if artifact_score > 0.7:
            anomalies.append("Compression artifacts detected")
        if blend_score > 0.7:
            anomalies.append("Face blending artifacts detected")
        if consistency_score > 0.7:
            anomalies.append("Face consistency anomalies detected")
        
        is_deepfake = confidence >= self.detection_threshold
        
        return DeepfakeResult(
            is_deepfake=is_deepfake,
            confidence=float(confidence),
            detection_method="ensemble",
            details={
                "neural_network_score": float(scores['neural_network']),
                "frequency_score": float(freq_score),
                "artifact_score": float(artifact_score),
                "blend_score": float(blend_score),
                "consistency_score": float(consistency_score),
                "frames_analyzed": len(frames),
                "models_available": self.mesonet_model is not None or self.xception_model is not None
            },
            frame_count=len(frames),
            anomalies=anomalies
        )
    
    def _neural_network_detection(self, frames: List[np.ndarray]) -> float:
        """
        Use trained neural networks for deepfake detection
        
        Args:
            frames: List of video frames
            
        Returns:
            Deepfake probability (0.0 - 1.0)
        """
        try:
            # Sample frames to reduce computation
            sample_indices = np.linspace(0, len(frames) - 1, min(10, len(frames)), dtype=int)
            sample_frames = [frames[i] for i in sample_indices]
            
            scores = []
            
            # Use MesoNet if available
            if self.mesonet_model is not None:
                for frame in sample_frames:
                    processed = self._preprocess_frame_mesonet(frame)
                    prediction = self.mesonet_model(processed, training=False)
                    deepfake_prob = float(prediction[0][1])
                    scores.append(deepfake_prob)
            
            # Use XceptionNet if available
            if self.xception_model is not None:
                for frame in sample_frames:
                    processed = self._preprocess_frame_xception(frame)
                    prediction = self.xception_model(processed, training=False)
                    deepfake_prob = float(prediction[0][1])
                    scores.append(deepfake_prob)
            
            if scores:
                return np.mean(scores)
            else:
                return 0.5  # Neutral if no models available
                
        except Exception as e:
            logger.warning(f"Neural network detection error: {e}")
            return 0.5
    
    def _preprocess_frame_mesonet(self, frame: np.ndarray) -> Optional[tf.Tensor]:
        """Preprocess frame for MesoNet (256x256)"""
        try:
            # Convert BGR to RGB
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Resize to 256x256
            frame = cv2.resize(frame, (256, 256))
            # Normalize to [0, 1]
            frame = frame.astype(np.float32) / 255.0
            # Add batch dimension
            frame = np.expand_dims(frame, 0)
            return tf.convert_to_tensor(frame)
        except Exception as e:
            logger.warning(f"Frame preprocessing error: {e}")
            return None
    
    def _preprocess_frame_xception(self, frame: np.ndarray) -> Optional[tf.Tensor]:
        """Preprocess frame for XceptionNet (299x299)"""
        try:
            # Convert BGR to RGB
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Resize to 299x299
            frame = cv2.resize(frame, (299, 299))
            # Add batch dimension
            frame = np.expand_dims(frame, 0)
            return tf.convert_to_tensor(frame.astype(np.float32))
        except Exception as e:
            logger.warning(f"Frame preprocessing error: {e}")
            return None
    
    def _frequency_analysis(self, frames: List[np.ndarray]) -> float:
        """
        Analyze frequency domain for deepfake indicators
        Real faces have natural frequency patterns
        """
        try:
            anomaly_scores = []
            
            for frame in frames:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Apply FFT
                f_transform = np.fft.fft2(gray)
                f_shift = np.fft.fftshift(f_transform)
                magnitude_spectrum = np.abs(f_shift)
                
                # Analyze magnitude distribution
                log_magnitude = np.log1p(magnitude_spectrum)
                
                # Real faces have specific frequency patterns
                # Deepfakes show unnatural frequency distribution
                h, w = log_magnitude.shape
                high_freq_region = log_magnitude[h//3:h//2, w//3:w//2]
                low_freq_region = log_magnitude[h//10:h//5, w//10:w//5]
                
                high_freq_ratio = np.sum(high_freq_region) / (np.sum(log_magnitude) + 1e-8)
                low_freq_ratio = np.sum(low_freq_region) / (np.sum(log_magnitude) + 1e-8)
                
                # Anomaly if ratio is unnatural
                if high_freq_ratio > 0.6 or low_freq_ratio < 0.05:
                    anomaly_scores.append(0.8)
                else:
                    anomaly_scores.append(0.2)
            
            return np.mean(anomaly_scores) if anomaly_scores else 0.3
            
        except Exception as e:
            logger.error(f"Error in frequency analysis: {e}")
            return 0.3
    
    def _detect_compression_artifacts(self, frames: List[np.ndarray]) -> float:
        """Detect compression artifacts typical of deepfakes"""
        try:
            artifact_scores = []
            
            for frame in frames:
                # Convert to LAB color space for better artifact detection
                lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                
                # Calculate gradient magnitude
                gradient_x = cv2.Sobel(lab, cv2.CV_32F, 1, 0, ksize=3)
                gradient_y = cv2.Sobel(lab, cv2.CV_32F, 0, 1, ksize=3)
                gradient_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)
                
                # Deepfakes often have artifacts in boundaries
                high_gradient_pixels = np.sum(gradient_magnitude > 50)
                total_pixels = gradient_magnitude.size
                ratio = high_gradient_pixels / total_pixels
                
                if ratio > 0.05:
                    artifact_scores.append(0.7)
                elif ratio > 0.02:
                    artifact_scores.append(0.4)
                else:
                    artifact_scores.append(0.1)
            
            return np.mean(artifact_scores) if artifact_scores else 0.3
            
        except Exception as e:
            logger.error(f"Error detecting compression artifacts: {e}")
            return 0.3
    
    def _detect_blend_artifacts(self, frames: List[np.ndarray]) -> float:
        """Detect face blending artifacts at boundaries"""
        try:
            blend_scores = []
            
            for frame in frames:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Apply edge detection
                edges = cv2.Canny(gray, 50, 150)
                
                # Analyze edge distribution
                edge_density = np.sum(edges > 0) / edges.size
                
                # Real faces have natural edge distribution
                # Deepfakes often have artificial edges at face boundaries
                if edge_density > 0.3:
                    blend_scores.append(0.7)
                elif edge_density > 0.15:
                    blend_scores.append(0.4)
                else:
                    blend_scores.append(0.2)
            
            return np.mean(blend_scores) if blend_scores else 0.3
            
        except Exception as e:
            logger.error(f"Error detecting blend artifacts: {e}")
            return 0.3
    
    def _detect_face_consistency(self, frames: List[np.ndarray]) -> float:
        """Detect inconsistencies in facial features across frames"""
        try:
            if len(frames) < 2:
                return 0.2
            
            consistency_scores = []
            
            # Compare consecutive frames
            for i in range(1, min(len(frames), 10)):  # Sample up to 10 frames
                prev_frame = frames[i-1]
                curr_frame = frames[i]
                
                # Convert to LAB for better color consistency detection
                prev_lab = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2LAB)
                curr_lab = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2LAB)
                
                # Calculate difference
                diff = cv2.absdiff(prev_lab, curr_lab)
                mean_diff = np.mean(diff)
                
                # Real videos have smooth transitions
                # Deepfakes often have jittery or unnatural transitions
                if mean_diff > 50:
                    consistency_scores.append(0.8)
                elif mean_diff > 20:
                    consistency_scores.append(0.4)
                else:
                    consistency_scores.append(0.2)
            
            return np.mean(consistency_scores) if consistency_scores else 0.3
            
        except Exception as e:
            logger.error(f"Error detecting face consistency: {e}")
            return 0.3


class SpoofDetector:
    """Detects print and replay attacks"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
    def detect_print_attack(self, frames: List[np.ndarray]) -> float:
        """Detect if attack uses printed photos"""
        try:
            print_scores = []
            
            for frame in frames:
                # Print photos have flat appearance
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Calculate Laplacian variance (focus measure)
                laplacian = cv2.Laplacian(gray, cv2.CV_64F)
                variance = laplacian.var()
                
                # Print photos have lower variance
                if variance < 100:
                    print_scores.append(0.8)
                elif variance < 500:
                    print_scores.append(0.5)
                else:
                    print_scores.append(0.1)
            
            return np.mean(print_scores) if print_scores else 0.3
            
        except Exception as e:
            logger.error(f"Error detecting print attack: {e}")
            return 0.3
    
    def detect_replay_attack(self, frames: List[np.ndarray]) -> float:
        """Detect if attack uses video replay"""
        try:
            if len(frames) < 2:
                return 0.2
            
            replay_scores = []
            
            for i in range(1, len(frames)):
                prev_gray = cv2.cvtColor(frames[i-1], cv2.COLOR_BGR2GRAY)
                curr_gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
                
                # Calculate difference
                diff = cv2.absdiff(prev_gray, curr_gray)
                
                # Replay attacks show minimal variation
                mean_diff = np.mean(diff)
                
                if mean_diff < 5:
                    replay_scores.append(0.9)
                elif mean_diff < 10:
                    replay_scores.append(0.6)
                else:
                    replay_scores.append(0.2)
            
            return np.mean(replay_scores) if replay_scores else 0.3
            
        except Exception as e:
            logger.error(f"Error detecting replay attack: {e}")
            return 0.3
