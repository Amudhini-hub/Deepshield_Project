"""
ML stack tests — PyTorch / timm pipeline.

Marks:
  (no mark)     — fast, no model weights needed (dataclass shapes, preprocessing API)
  @pytest.mark.slow — loads or runs actual PyTorch models (~100 MB download on first run)

Run all:  pytest tests/test_ml_inference.py -v
Skip slow: pytest tests/test_ml_inference.py -v -m "not slow"
"""

import os

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Optional dependency guard
# ---------------------------------------------------------------------------
try:
    import torch
    import torch.nn as nn

    from backend.ml.model_loader import ModelLoader
    from backend.ml.preprocessing import preprocess_batch
    from backend.services.deepfake_detection import DeepfakeDetector, DeepfakeResult
    from backend.services.liveness_detection import LivenessDetector, LivenessResult

    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not ML_AVAILABLE, reason="PyTorch / timm not installed"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def dummy_frames():
    """10 random BGR frames at 224×224 — no model loading needed."""
    return [np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8) for _ in range(10)]


@pytest.fixture(scope="module")
def synthetic_video(tmp_path_factory):
    """Write a 20-frame synthetic MP4 with OpenCV; yields the file path."""
    import cv2

    path = str(tmp_path_factory.mktemp("video") / "synth.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(path, fourcc, 10.0, (224, 224))
    for _ in range(20):
        frame = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        writer.write(frame)
    writer.release()
    return path


# ---------------------------------------------------------------------------
# ModelLoader — thread-safe singleton
# ---------------------------------------------------------------------------

class TestModelLoader:
    def test_get_device_returns_torch_device(self):
        assert isinstance(ModelLoader.get_device(), torch.device)

    def test_load_weights_missing_file_is_silent(self):
        """load_weights must not raise when the weights file does not exist."""
        ModelLoader.get_efficientnet_b0()  # ensure model is cached first
        ModelLoader.load_weights("efficientnet_b0", "/nonexistent/weights.pth")

    @pytest.mark.slow
    def test_get_xception_singleton(self):
        assert ModelLoader.get_xception() is ModelLoader.get_xception()

    @pytest.mark.slow
    def test_get_efficientnet_singleton(self):
        assert ModelLoader.get_efficientnet() is ModelLoader.get_efficientnet()

    @pytest.mark.slow
    def test_get_efficientnet_b0_singleton(self):
        assert ModelLoader.get_efficientnet_b0() is ModelLoader.get_efficientnet_b0()

    @pytest.mark.slow
    def test_all_models_in_eval_mode(self):
        for getter in (
            ModelLoader.get_xception,
            ModelLoader.get_efficientnet,
            ModelLoader.get_efficientnet_b0,
        ):
            model = getter()
            assert not model.training, f"{model.__class__.__name__} must be in eval mode"

    @pytest.mark.slow
    def test_models_are_nn_modules(self):
        for getter in (
            ModelLoader.get_xception,
            ModelLoader.get_efficientnet,
            ModelLoader.get_efficientnet_b0,
        ):
            assert isinstance(getter(), nn.Module)


# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------

class TestPreprocessing:
    def test_batch_shape(self, dummy_frames):
        device = torch.device("cpu")
        batch = preprocess_batch(dummy_frames, (224, 224), device)
        assert batch.shape == (len(dummy_frames), 3, 224, 224)

    def test_batch_on_cpu(self, dummy_frames):
        device = torch.device("cpu")
        batch = preprocess_batch(dummy_frames, (224, 224), device)
        assert batch.device.type == "cpu"

    def test_batch_value_range(self, dummy_frames):
        device = torch.device("cpu")
        batch = preprocess_batch(dummy_frames, (224, 224), device)
        # Normalized with mean/std 0.5 → values in roughly [-2, 2]
        assert float(batch.min()) >= -3.0
        assert float(batch.max()) <= 3.0

    def test_batch_different_target_sizes(self, dummy_frames):
        device = torch.device("cpu")
        for h, w in ((224, 224), (299, 299), (380, 380)):
            batch = preprocess_batch(dummy_frames, (h, w), device)
            assert batch.shape == (len(dummy_frames), 3, h, w)

    def test_single_frame_batch(self):
        device = torch.device("cpu")
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        batch = preprocess_batch([frame], (224, 224), device)
        assert batch.shape == (1, 3, 224, 224)


# ---------------------------------------------------------------------------
# LivenessResult dataclass + backward-compat aliases
# ---------------------------------------------------------------------------

class TestLivenessResult:
    def _make(self, is_live=True):
        return LivenessResult(
            is_live=is_live,
            confidence=0.9 if is_live else 0.2,
            detection_method="efficientnet_b0",
            frame_count=5,
            details={"live_score": 0.9, "threshold": 0.5, "frames_analysed": 5},
            anomalies=[],
        )

    def test_is_alive_alias_true(self):
        assert self._make(True).is_alive is True

    def test_is_alive_alias_false(self):
        assert self._make(False).is_alive is False

    def test_challenge_type_alias(self):
        assert self._make().challenge_type == "efficientnet_b0"

    def test_all_tasks_py_attributes_present(self):
        r = self._make()
        for attr in ("is_alive", "confidence", "challenge_type", "frame_count", "details"):
            assert hasattr(r, attr), f"LivenessResult missing attribute: {attr}"

    def test_anomalies_field(self):
        r = self._make()
        assert isinstance(r.anomalies, list)

    def test_processing_time_defaults_to_zero(self):
        r = self._make()
        assert r.processing_time_ms == 0.0


# ---------------------------------------------------------------------------
# DeepfakeResult dataclass
# ---------------------------------------------------------------------------

class TestDeepfakeResult:
    def _make(self):
        return DeepfakeResult(
            is_deepfake=False,
            confidence=0.3,
            detection_method="xception_efficientnet_ensemble",
            frame_count=10,
            details={"xception_score": 0.3, "efficientnet_score": 0.3},
            anomalies=[],
        )

    def test_fields_present(self):
        r = self._make()
        assert r.is_deepfake is False
        assert r.frame_count == 10
        assert isinstance(r.anomalies, list)

    def test_processing_time_defaults_to_zero(self):
        assert self._make().processing_time_ms == 0.0


# ---------------------------------------------------------------------------
# LivenessDetector
# ---------------------------------------------------------------------------

class TestLivenessDetector:
    @pytest.mark.slow
    def test_detect_from_frame_returns_liveness_result(self):
        detector = LivenessDetector()
        frame = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        result = detector.detect_from_frame(frame)
        assert isinstance(result, LivenessResult)

    @pytest.mark.slow
    def test_detect_from_frame_confidence_in_range(self):
        detector = LivenessDetector()
        frame = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        result = detector.detect_from_frame(frame)
        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.slow
    def test_detect_from_frame_single_frame_count(self):
        detector = LivenessDetector()
        frame = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        result = detector.detect_from_frame(frame)
        assert result.frame_count == 1

    @pytest.mark.slow
    def test_detect_from_frame_details_keys(self):
        detector = LivenessDetector()
        frame = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        result = detector.detect_from_frame(frame)
        for key in ("live_score", "threshold", "frames_analysed"):
            assert key in result.details, f"Missing detail key: {key}"

    @pytest.mark.slow
    def test_detect_from_video_with_synthetic_file(self, synthetic_video):
        detector = LivenessDetector()
        result = detector.detect_from_video(synthetic_video, max_frames=10)
        assert isinstance(result, LivenessResult)
        assert result.frame_count > 0
        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.slow
    def test_detect_from_video_missing_file_raises(self):
        detector = LivenessDetector()
        with pytest.raises((ValueError, Exception)):
            detector.detect_from_video("/nonexistent/video.mp4")

    @pytest.mark.slow
    def test_tasks_py_attribute_access(self, synthetic_video):
        """Reproduce exactly what tasks.py does after calling detect_from_video."""
        detector = LivenessDetector()
        result = detector.detect_from_video(synthetic_video, max_frames=5)
        # tasks.py reads these attribute names directly
        _ = result.is_alive
        _ = result.confidence
        _ = result.challenge_type
        _ = result.frame_count
        _ = result.details


# ---------------------------------------------------------------------------
# DeepfakeDetector
# ---------------------------------------------------------------------------

class TestDeepfakeDetector:
    @pytest.mark.slow
    def test_detect_from_frames_raises_not_implemented(self):
        detector = DeepfakeDetector()
        with pytest.raises(NotImplementedError):
            detector.detect_from_frames([])

    @pytest.mark.slow
    def test_detect_from_video_with_synthetic_file(self, synthetic_video):
        detector = DeepfakeDetector()
        result = detector.detect_from_video(synthetic_video, max_frames=10)
        assert isinstance(result.is_deepfake, bool)
        assert 0.0 <= result.confidence <= 1.0
        assert result.frame_count > 0

    @pytest.mark.slow
    def test_detect_from_video_details_keys(self, synthetic_video):
        detector = DeepfakeDetector()
        result = detector.detect_from_video(synthetic_video, max_frames=10)
        for key in ("xception_score", "efficientnet_score", "ensemble_method", "frames_analysed"):
            assert key in result.details, f"Missing detail key: {key}"

    @pytest.mark.slow
    def test_detect_from_video_anomalies_is_list(self, synthetic_video):
        detector = DeepfakeDetector()
        result = detector.detect_from_video(synthetic_video, max_frames=5)
        assert isinstance(result.anomalies, list)

    @pytest.mark.slow
    def test_detect_from_video_missing_file_raises(self):
        detector = DeepfakeDetector()
        with pytest.raises((ValueError, Exception)):
            detector.detect_from_video("/nonexistent/video.mp4")

    @pytest.mark.slow
    def test_detection_method_label(self, synthetic_video):
        detector = DeepfakeDetector()
        result = detector.detect_from_video(synthetic_video, max_frames=5)
        assert result.detection_method == "xception_efficientnet_ensemble"
