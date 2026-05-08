"""
ML Models Usage Examples
Demonstrates how to use the deepfake and liveness detection models
"""

from typing import List

import cv2
import numpy as np


# Example 1: Using DeepfakeDetector directly
def example_deepfake_detection():
    """Example: Detect deepfakes in video frames"""
    from backend.services.deepfake_detection import DeepfakeDetector

    # Initialize detector
    detector = DeepfakeDetector(
        config={
            "detection_threshold": 0.8,
            "models_dir": "ml_models/deepfake_detection",
        }
    )

    # Load video frames (simulated)
    frames = load_video_frames("path/to/video.mp4", max_frames=30)

    # Detect deepfakes
    result = detector.detect_from_frames(frames)

    # Output
    print(f"Is Deepfake: {result.is_deepfake}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Anomalies: {result.anomalies}")
    print(f"Details: {result.details}")


# Example 2: Using LivenessDetector directly
def example_liveness_detection():
    """Example: Detect liveness in video frames"""
    from backend.services.liveness_detection import LivenessDetector

    # Initialize detector
    detector = LivenessDetector(
        config={
            "confidence_threshold": 0.85,
            "models_dir": "ml_models/liveness_detection",
        }
    )

    # Load video frames (simulated)
    frames = load_video_frames("path/to/video.mp4", max_frames=60)

    # Detect liveness
    result = detector.detect_from_video_frames(frames)

    # Output
    print(f"Is Alive: {result.is_alive}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Challenge Type: {result.challenge_type}")
    print(f"Details: {result.details}")


# Example 3: Using API endpoints with requests
def example_api_usage():
    """Example: Using the API endpoints"""
    import requests

    # Get JWT token
    login_response = requests.post(
        "http://localhost:5000/api/v1/users/login",
        data={"username": "user@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # Test deepfake detection
    with open("video.mp4", "rb") as f:
        files = {"file": f}
        deepfake_response = requests.post(
            "http://localhost:5000/api/v1/deepfake/detect", files=files, headers=headers
        )

    deepfake_result = deepfake_response.json()
    print("Deepfake Detection Result:")
    print(f"  Is Deepfake: {deepfake_result['is_deepfake']}")
    print(f"  Confidence: {deepfake_result['confidence']}")

    # Test liveness detection
    with open("video.mp4", "rb") as f:
        files = {"file": f}
        liveness_response = requests.post(
            "http://localhost:5000/api/v1/liveness/detect", files=files, headers=headers
        )

    liveness_result = liveness_response.json()
    print("\nLiveness Detection Result:")
    print(f"  Is Alive: {liveness_result['is_alive']}")
    print(f"  Confidence: {liveness_result['confidence']}")


# Example 4: Training a new model
def example_model_training():
    """Example: Training a deepfake detection model"""
    import numpy as np

    from backend.services.deepfake_detection import MesoNet
    from backend.services.model_utils import ModelManager, ModelTrainer

    # Initialize model
    model = MesoNet(num_classes=2)

    # Compile
    ModelTrainer.compile_deepfake_model(model, learning_rate=0.001)

    # Generate dummy training data (replace with real data)
    x_train = np.random.rand(100, 256, 256, 3).astype(np.float32)
    y_train = np.random.randint(0, 2, 100)
    x_val = np.random.rand(20, 256, 256, 3).astype(np.float32)
    y_val = np.random.randint(0, 2, 20)

    # Get training callbacks
    callbacks = ModelTrainer.create_training_callbacks(
        "ml_models/deepfake_detection/mesonet_model.h5"
    )

    # Train
    history = model.fit(
        x_train,
        y_train,
        validation_data=(x_val, y_val),
        epochs=50,
        batch_size=16,
        callbacks=callbacks,
        verbose=1,
    )

    return model, history


# Example 5: Model management
def example_model_management():
    """Example: Managing models"""
    from backend.services.model_utils import ModelManager, get_model_info

    # Get or create detectors (lazy loaded)
    deepfake_detector = ModelManager.get_deepfake_detector()
    liveness_detector = ModelManager.get_liveness_detector()

    # Get model info
    info = get_model_info()
    print("Model Information:")
    print(f"  Deepfake Models: {info['deepfake_detection']['models']}")
    print(f"  Liveness Models: {info['liveness_detection']['models']}")

    # Clear cache (useful when switching models)
    ModelManager.clear_cache()


# Utility function
def load_video_frames(video_path: str, max_frames: int = 30) -> List[np.ndarray]:
    """Load frames from video file"""
    frames = []
    cap = cv2.VideoCapture(video_path)

    frame_count = 0
    while frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        # Resize for faster processing
        frame = cv2.resize(frame, (640, 480))
        frames.append(frame)
        frame_count += 1

    cap.release()
    return frames


if __name__ == "__main__":
    print("ML Models Usage Examples")
    print("=" * 50)
    print("\nNote: These are example functions. Uncomment to run.")
    print("\nAvailable examples:")
    print("1. example_deepfake_detection() - Detect deepfakes")
    print("2. example_liveness_detection() - Detect liveness")
    print("3. example_api_usage() - Use API endpoints")
    print("4. example_model_training() - Train a model")
    print("5. example_model_management() - Manage models")
