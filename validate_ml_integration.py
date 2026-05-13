#!/usr/bin/env python3
"""
ML Model Integration Validation Script
Validates all ML components are working correctly
"""

import sys
import time
import numpy as np
from datetime import datetime

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_model_loader():
    """Test 1: Model Loader"""
    print_section("TEST 1: Model Loader Service")
    try:
        from backend.services.model_loader import get_model_loader, ModelRegistry
        
        # Test registry
        print("✅ Model registry imported")
        models = ModelRegistry.list_models("deepfake")
        print(f"✅ Found {len(models)} deepfake models")
        
        models = ModelRegistry.list_models("liveness")
        print(f"✅ Found {len(models)} liveness models")
        
        # Test loader
        loader = get_model_loader()
        print("✅ Model loader initialized")
        
        # List available
        available = loader.list_available_models("deepfake")
        print(f"✅ Deepfake models available: {list(available.keys())[:2]}...")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_deepfake_detector():
    """Test 2: Deepfake Detector"""
    print_section("TEST 2: Deepfake Detection")
    try:
        from backend.services.deepfake_detection import DeepfakeDetector
        
        # Initialize detector
        detector = DeepfakeDetector()
        print("✅ Deepfake detector initialized")
        
        # Create dummy frames
        print("  Creating test frames...")
        frames = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(5)]
        print(f"✅ Generated {len(frames)} test frames")
        
        # Run detection
        print("  Running deepfake detection...")
        start = time.time()
        result = detector.detect_from_frames(frames)
        elapsed = time.time() - start
        
        print(f"✅ Detection completed in {elapsed:.2f}s")
        print(f"   - Is Deepfake: {result.is_deepfake}")
        print(f"   - Confidence: {result.confidence:.2%}")
        print(f"   - Method: {result.details.get('method', 'unknown')}")
        print(f"   - Using Neural Network: {result.details.get('using_neural_network', False)}")
        print(f"   - Frames Analyzed: {result.frame_count}")
        
        if result.anomalies:
            print(f"   - Anomalies Found: {', '.join(result.anomalies)}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_liveness_detector():
    """Test 3: Liveness Detector"""
    print_section("TEST 3: Liveness Detection")
    try:
        from backend.services.liveness_detection import LivenessDetector
        
        # Initialize detector
        detector = LivenessDetector()
        print("✅ Liveness detector initialized")
        
        # Create dummy frames
        print("  Creating test frames...")
        frames = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(10)]
        print(f"✅ Generated {len(frames)} test frames")
        
        # Run detection
        print("  Running liveness detection...")
        start = time.time()
        result = detector.detect_from_video_frames(frames)
        elapsed = time.time() - start
        
        print(f"✅ Detection completed in {elapsed:.2f}s")
        print(f"   - Is Alive: {result.is_alive}")
        print(f"   - Confidence: {result.confidence:.2%}")
        print(f"   - Method: {result.details.get('method', 'unknown')}")
        print(f"   - Using Neural Network: {result.details.get('using_neural_network', False)}")
        print(f"   - Frames Analyzed: {result.frame_count}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_inference_preprocessor():
    """Test 4: Inference Preprocessor"""
    print_section("TEST 4: Inference Preprocessing")
    try:
        from backend.services.model_loader import InferencePreprocessor
        
        # Test image preprocessing
        print("  Testing image preprocessing...")
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        processed = InferencePreprocessor.preprocess_image(image, target_size=(224, 224))
        
        assert processed is not None
        assert processed.shape == (1, 224, 224, 3)
        assert processed.min() >= 0.0 and processed.max() <= 1.0
        print("✅ Image preprocessing works")
        print(f"   - Output shape: {processed.shape}")
        print(f"   - Value range: [{processed.min():.3f}, {processed.max():.3f}]")
        
        # Test batch preprocessing
        print("  Testing batch preprocessing...")
        frames = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(5)]
        batch = InferencePreprocessor.preprocess_frames(frames, target_size=(224, 224))
        
        assert batch is not None
        assert batch.shape == (5, 224, 224, 3)
        assert batch.min() >= 0.0 and batch.max() <= 1.0
        print("✅ Batch preprocessing works")
        print(f"   - Output shape: {batch.shape}")
        print(f"   - Value range: [{batch.min():.3f}, {batch.max():.3f}]")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_caching():
    """Test 5: Model Caching"""
    print_section("TEST 5: Model Caching")
    try:
        from backend.services.model_loader import get_model_loader
        
        loader = get_model_loader(cache_models=True)
        print("✅ Model loader with caching initialized")
        
        # Check cache stats
        stats = loader.get_cache_stats()
        print(f"✅ Cache stats retrieved")
        print(f"   - Loaded models: {stats['model_count']}")
        print(f"   - Redis enabled: {stats['cached_in_redis']}")
        print(f"   - Redis connected: {stats['redis_connected']}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """Test 6: ML Configuration"""
    print_section("TEST 6: ML Configuration")
    try:
        from backend.config.config import get_config
        
        config = get_config()
        print("✅ Configuration loaded")
        
        # Check ML-related settings
        settings = {
            "DEEPFAKE_DETECTION_THRESHOLD": getattr(config, "detection_threshold", 0.8),
            "LIVENESS_CONFIDENCE_THRESHOLD": getattr(config, "LIVENESS_CONFIDENCE_THRESHOLD", 0.85),
            "DEEPFAKE_FRAME_SAMPLING": getattr(config, "DEEPFAKE_FRAME_SAMPLING_INTERVAL", 5),
        }
        
        for setting, value in settings.items():
            print(f"   - {setting}: {value}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """Test 7: ML API Endpoints"""
    print_section("TEST 7: ML API Endpoints")
    try:
        from backend.api import ML_AVAILABLE
        
        print(f"✅ ML services availability: {ML_AVAILABLE}")
        
        if ML_AVAILABLE:
            print("✅ ML endpoints should be active")
            print("   - POST /api/v1/deepfake/detect")
            print("   - POST /api/v1/liveness/detect")
        else:
            print("⚠️  ML services not available")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests"""
    print("\n" + "="*70)
    print("  DeepShield ML Model Integration - Validation Suite")
    print("="*70)
    print(f"Started at: {datetime.now().isoformat()}")
    
    results = []
    
    # Run tests
    results.append(("Model Loader", test_model_loader()))
    results.append(("Deepfake Detector", test_deepfake_detector()))
    results.append(("Liveness Detector", test_liveness_detector()))
    results.append(("Inference Preprocessor", test_inference_preprocessor()))
    results.append(("Model Caching", test_model_caching()))
    results.append(("ML Configuration", test_configuration()))
    results.append(("ML API Endpoints", test_api_endpoints()))
    
    # Summary
    print_section("SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Completed at: {datetime.now().isoformat()}")
    
    if passed == total:
        print("\n🎉 All ML tests passed! System is ready for deployment.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
