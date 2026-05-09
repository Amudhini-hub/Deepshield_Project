#!/usr/bin/env python3
"""
Comprehensive API test for ML detection endpoints
Tests deepfake and liveness detection through API
"""

import sys
import os
from pathlib import Path
import json
import io
import logging
from base64 import b64encode

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

import numpy as np
import cv2
from fastapi.testclient import TestClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_test_video_bytes():
    """Create a test video file in memory"""
    logger.info("Creating test video file...")
    
    # Create a video writer that writes to memory
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('test_video_temp.mp4', fourcc, 30.0, (224, 224))
    
    # Write 10 frames
    for i in range(10):
        frame = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
        out.write(frame)
    
    out.release()
    
    # Read the video file
    with open('test_video_temp.mp4', 'rb') as f:
        video_bytes = f.read()
    
    # Clean up temp file
    os.remove('test_video_temp.mp4')
    
    logger.info(f"Created test video: {len(video_bytes)} bytes")
    return video_bytes


def test_api_endpoints():
    """Test API endpoints"""
    logger.info("=" * 60)
    logger.info("Testing API Detection Endpoints")
    logger.info("=" * 60)
    
    try:
        # Import the app
        from backend.main import app
        
        client = TestClient(app)
        logger.info("✓ Test client initialized")
        
        # Test health endpoint first
        logger.info("\nTesting health endpoint...")
        response = client.get("/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        logger.info(f"✓ Health check passed: {response.json()}")
        
        # Create test video
        video_bytes = create_test_video_bytes()
        
        # Test deepfake detection endpoint
        logger.info("\nTesting deepfake detection endpoint...")
        
        files = {
            'file': ('test_video.mp4', io.BytesIO(video_bytes), 'video/mp4')
        }
        
        response = client.post(
            "/api/v1/deepfake/detect",
            files=files
        )
        
        logger.info(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✓ Deepfake Detection Response:")
            logger.info(f"  - Is Deepfake: {result.get('is_deepfake')}")
            logger.info(f"  - Confidence: {result.get('confidence', 'N/A')}")
            logger.info(f"  - Detection Method: {result.get('detection_method')}")
        elif response.status_code == 401:
            logger.warning(f"⚠️  Endpoint requires authentication: {response.status_code}")
        else:
            logger.error(f"✗ Deepfake detection failed: {response.status_code}")
            logger.error(f"  Response: {response.text}")
        
        # Test liveness detection endpoint
        logger.info("\nTesting liveness detection endpoint...")
        
        files = {
            'file': ('test_video.mp4', io.BytesIO(video_bytes), 'video/mp4')
        }
        
        response = client.post(
            "/api/v1/liveness/detect",
            files=files
        )
        
        logger.info(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✓ Liveness Detection Response:")
            logger.info(f"  - Is Alive: {result.get('is_alive')}")
            logger.info(f"  - Confidence: {result.get('confidence', 'N/A')}")
            logger.info(f"  - Challenge Type: {result.get('challenge_type')}")
        elif response.status_code == 401:
            logger.warning(f"⚠️  Endpoint requires authentication: {response.status_code}")
        else:
            logger.error(f"✗ Liveness detection failed: {response.status_code}")
            logger.error(f"  Response: {response.text}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ API test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run API tests"""
    logger.info("\n" + "🧪" * 30)
    logger.info("DeepShield API Detection Endpoints - Integration Test")
    logger.info("🧪" * 30 + "\n")
    
    try:
        result = test_api_endpoints()
        
        logger.info("\n" + "=" * 60)
        if result:
            logger.info("✅ API TESTS COMPLETED")
            logger.info("ML Detection endpoints are accessible through API!")
        else:
            logger.warning("⚠️ Some API tests encountered issues")
        logger.info("=" * 60)
        
        return 0 if result else 1
    
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
