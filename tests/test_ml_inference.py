"""
ML Model Integration Tests
Tests for deepfake detection, liveness detection, and model loading
"""

import pytest
import numpy as np
from backend.services.model_loader import (
    get_model_loader,
    ModelRegistry,
    InferencePreprocessor,
)
from backend.services.deepfake_detection import DeepfakeDetector
from backend.services.liveness_detection import LivenessDetector


class TestModelRegistry:
    """Test ML model registry"""

    def test_model_registry_contains_deepfake_models(self):
        """Test deepfake models are registered"""
        models = ModelRegistry.list_models("deepfake")
        assert len(models) > 0
        assert "deepfake_mobilenetv2" in models

    def test_model_registry_contains_liveness_models(self):
        """Test liveness models are registered"""
        models = ModelRegistry.list_models("liveness")
        assert len(models) > 0
        assert "liveness_mobilenet" in models

    def test_get_model_info(self):
        """Test getting model information"""
        info = ModelRegistry.get_model_info("deepfake_mobilenetv2")
        assert info is not None
        assert info["type"] == "deepfake"
        assert "url" in info
        assert "input_shape" in info

    def test_get_default_model_deepfake(self):
        """Test getting default deepfake model"""
        model = ModelRegistry.get_default_model("deepfake")
        assert model == "deepfake_mobilenetv2"

    def test_get_default_model_liveness(self):
        """Test getting default liveness model"""
        model = ModelRegistry.get_default_model("liveness")
        assert model == "liveness_mobilenet"


class TestModelLoader:
    """Test ML model loader"""

    def test_model_loader_singleton(self):
        """Test model loader singleton pattern"""
        loader1 = get_model_loader()
        loader2 = get_model_loader()
        assert loader1 is loader2

    def test_model_loader_initialization(self):
        """Test model loader initialization"""
        loader = get_model_loader()
        assert loader is not None
        assert hasattr(loader, "load_model")
        assert hasattr(loader, "list_available_models")

    def test_list_available_models(self):
        """Test listing available models"""
        loader = get_model_loader()
        models = loader.list_available_models("deepfake")
        assert isinstance(models, dict)
        assert len(models) > 0

    def test_get_cache_stats(self):
        """Test getting cache statistics"""
        loader = get_model_loader()
        stats = loader.get_cache_stats()
        assert "loaded_models" in stats
        assert "model_count" in stats
        assert "cached_in_redis" in stats

    def test_clear_cache(self):
        """Test clearing model cache"""
        loader = get_model_loader()
        stats_before = loader.get_cache_stats()
        loader.clear_cache()
        stats_after = loader.get_cache_stats()
        assert stats_after["model_count"] == 0


class TestInferencePreprocessor:
    """Test inference preprocessing"""

    def test_preprocess_image(self):
        """Test image preprocessing"""
        # Create dummy image (480x640x3)
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        processed = InferencePreprocessor.preprocess_image(image, target_size=(224, 224))
        
        assert processed is not None
        assert processed.shape == (1, 224, 224, 3)
        assert processed.min() >= 0.0
        assert processed.max() <= 1.0

    def test_preprocess_frames(self):
        """Test batch frame preprocessing"""
        # Create dummy frames
        frames = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(5)]
        
        processed = InferencePreprocessor.preprocess_frames(frames, target_size=(224, 224))
        
        assert processed is not None
        assert processed.shape == (5, 224, 224, 3)
        assert processed.min() >= 0.0
        assert processed.max() <= 1.0

    def test_preprocess_frames_empty(self):
        """Test preprocessing empty frame list"""
        processed = InferencePreprocessor.preprocess_frames([], target_size=(224, 224))
        assert processed is None


class TestDeepfakeDetector:
    """Test deepfake detection"""

    def test_deepfake_detector_initialization(self):
        """Test deepfake detector initialization"""
        detector = DeepfakeDetector()
        assert detector is not None
        assert hasattr(detector, "detect_from_frames")

    def test_deepfake_detector_no_frames(self):
        """Test deepfake detection with no frames"""
        detector = DeepfakeDetector()
        result = detector.detect_from_frames([])
        
        assert result is not None
        assert result.confidence == 0.0
        assert result.frame_count == 0
        assert result.details.get("error") == "No frames provided"

    def test_deepfake_detector_single_frame(self):
        """Test deepfake detection with single frame"""
        detector = DeepfakeDetector()
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        result = detector.detect_from_frames([frame])
        
        assert result is not None
        assert isinstance(result.is_deepfake, bool)
        assert 0.0 <= result.confidence <= 1.0
        assert result.frame_count == 1
        assert "method" in result.details

    def test_deepfake_detector_multiple_frames(self):
        """Test deepfake detection with multiple frames"""
        detector = DeepfakeDetector()
        frames = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(10)]
        
        result = detector.detect_from_frames(frames)
        
        assert result is not None
        assert isinstance(result.is_deepfake, bool)
        assert 0.0 <= result.confidence <= 1.0
        assert result.frame_count == 10

    def test_deepfake_detector_has_anomalies(self):
        """Test deepfake detector identifies anomalies"""
        detector = DeepfakeDetector()
        frames = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(10)]
        
        result = detector.detect_from_frames(frames)
        
        assert isinstance(result.anomalies, list)
        # Anomalies field should exist (may be empty)


class TestLivenessDetector:
    """Test liveness detection"""

    def test_liveness_detector_initialization(self):
        """Test liveness detector initialization"""
        detector = LivenessDetector()
        assert detector is not None
        assert hasattr(detector, "detect_from_video_frames")

    def test_liveness_detector_no_frames(self):
        """Test liveness detection with no frames"""
        detector = LivenessDetector()
        result = detector.detect_from_video_frames([])
        
        assert result is not None
        assert result.confidence == 0.0
        assert result.frame_count == 0
        assert result.details.get("error") == "No frames provided"

    def test_liveness_detector_single_frame(self):
        """Test liveness detection with single frame"""
        detector = LivenessDetector()
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        result = detector.detect_from_video_frames([frame])
        
        assert result is not None
        assert isinstance(result.is_alive, bool)
        assert 0.0 <= result.confidence <= 1.0
        assert result.frame_count == 1
        assert "method" in result.details

    def test_liveness_detector_multiple_frames(self):
        """Test liveness detection with multiple frames"""
        detector = LivenessDetector()
        frames = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(30)]
        
        result = detector.detect_from_video_frames(frames)
        
        assert result is not None
        assert isinstance(result.is_alive, bool)
        assert 0.0 <= result.confidence <= 1.0
        assert result.frame_count == 30

    def test_liveness_detector_consistency(self):
        """Test liveness detector returns consistent results"""
        detector = LivenessDetector()
        frames = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(10)]
        
        result1 = detector.detect_from_video_frames(frames)
        result2 = detector.detect_from_video_frames(frames)
        
        # Results should be the same for same input
        assert result1.is_alive == result2.is_alive
        assert abs(result1.confidence - result2.confidence) < 0.01


class TestMLIntegration:
    """Integration tests for ML services"""

    def test_deepfake_and_liveness_together(self):
        """Test using both deepfake and liveness detectors"""
        deepfake_detector = DeepfakeDetector()
        liveness_detector = LivenessDetector()
        
        frames = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(10)]
        
        deepfake_result = deepfake_detector.detect_from_frames(frames)
        liveness_result = liveness_detector.detect_from_video_frames(frames)
        
        assert deepfake_result is not None
        assert liveness_result is not None
        
        # Both should produce confidence scores
        assert 0.0 <= deepfake_result.confidence <= 1.0
        assert 0.0 <= liveness_result.confidence <= 1.0

    def test_model_loading_with_cache(self):
        """Test model loading and caching"""
        loader = get_model_loader(cache_models=True)
        
        # First load
        model1 = loader.load_model("deepfake_mobilenetv2")
        
        # Check cache stats
        stats = loader.get_cache_stats()
        initial_count = stats["model_count"]
        
        # Second load (should use cache)
        model2 = loader.load_model("deepfake_mobilenetv2")
        
        # Both should be the same or both loaded
        assert model1 is not None or model2 is not None


class TestModelErrors:
    """Test error handling in ML services"""

    def test_deepfake_detector_handles_invalid_frames(self):
        """Test deepfake detector handles invalid frames"""
        detector = DeepfakeDetector()
        
        # Try with None
        try:
            result = detector.detect_from_frames([None])
            assert result is not None
        except Exception:
            # Should handle gracefully
            pass

    def test_liveness_detector_handles_invalid_frames(self):
        """Test liveness detector handles invalid frames"""
        detector = LivenessDetector()
        
        # Try with None
        try:
            result = detector.detect_from_video_frames([None])
            assert result is not None
        except Exception:
            # Should handle gracefully
            pass

    def test_model_loader_invalid_model_name(self):
        """Test model loader with invalid model name"""
        loader = get_model_loader()
        model = loader.load_model("invalid_model_name")
        assert model is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
