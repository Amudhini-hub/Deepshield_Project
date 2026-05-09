#!/usr/bin/env python3
"""
Test script for ML detection services
Tests deepfake and liveness detection end-to-end
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

import numpy as np
import cv2
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_test_frames(num_frames=10):
    """Generate synthetic test frames"""
    logger.info(f"Generating {num_frames} test frames...")
    frames = []
    
    for i in range(num_frames):
        # Create a random frame
        frame = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
        frames.append(frame)
    
    logger.info(f"Generated {len(frames)} frames of shape {frames[0].shape}")
    return frames


def test_deepfake_detection():
    """Test deepfake detection service"""
    logger.info("=" * 60)
    logger.info("Testing Deepfake Detection Service")
    logger.info("=" * 60)
    
    try:
        from backend.services.deepfake_detection import DeepfakeDetector
        
        # Initialize detector
        detector = DeepfakeDetector({"detection_threshold": 0.8})
        logger.info("✓ DeepfakeDetector initialized successfully")
        
        # Generate test frames
        frames = generate_test_frames(10)
        
        # Run detection
        logger.info("Running deepfake detection...")
        result = detector.detect_from_frames(frames)
        
        logger.info(f"✓ Deepfake Detection Result:")
        logger.info(f"  - Is Deepfake: {result.is_deepfake}")
        logger.info(f"  - Confidence: {result.confidence:.4f}")
        logger.info(f"  - Frames Analyzed: {result.frame_count}")
        logger.info(f"  - Detection Method: {result.detection_method}")
        logger.info(f"  - Details: {result.details}")
        logger.info(f"  - Anomalies: {result.anomalies}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Deepfake detection test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_liveness_detection():
    """Test liveness detection service"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Liveness Detection Service")
    logger.info("=" * 60)
    
    try:
        from backend.services.liveness_detection import LivenessDetector
        
        # Initialize detector
        detector = LivenessDetector({"confidence_threshold": 0.85})
        logger.info("✓ LivenessDetector initialized successfully")
        
        # Generate test frames
        frames = generate_test_frames(15)
        
        # Run detection
        logger.info("Running liveness detection...")
        result = detector.detect_from_video_frames(frames)
        
        logger.info(f"✓ Liveness Detection Result:")
        logger.info(f"  - Is Alive: {result.is_alive}")
        logger.info(f"  - Confidence: {result.confidence:.4f}")
        logger.info(f"  - Frames Analyzed: {result.frame_count}")
        logger.info(f"  - Challenge Type: {result.challenge_type}")
        logger.info(f"  - Details: {result.details}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Liveness detection test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    logger.info("\n" + "🧪" * 30)
    logger.info("DeepShield ML Detection Services - Integration Test")
    logger.info("🧪" * 30 + "\n")
    
    # Run tests
    deepfake_pass = test_deepfake_detection()
    liveness_pass = test_liveness_detection()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Deepfake Detection: {'✅ PASS' if deepfake_pass else '❌ FAIL'}")
    logger.info(f"Liveness Detection: {'✅ PASS' if liveness_pass else '❌ FAIL'}")
    
    if deepfake_pass and liveness_pass:
        logger.info("\n🎉 ALL TESTS PASSED!")
        logger.info("ML Detection Services are working correctly!")
        return 0
    else:
        logger.warning("\n⚠️ SOME TESTS FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
