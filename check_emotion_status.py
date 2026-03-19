"""
Diagnostic script to check emotion detection status
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("Emotion Detection Diagnostic Tool")
print("=" * 70)

# Test 1: Basic imports
print("\n1. Testing basic imports...")
try:
    import cv2
    print(f"   ✓ OpenCV: {cv2.__version__}")
except Exception as e:
    print(f"   ✗ OpenCV error: {e}")

try:
    import numpy as np
    print(f"   ✓ NumPy: {np.__version__}")
except Exception as e:
    print(f"   ✗ NumPy error: {e}")

try:
    from PIL import Image
    print("   ✓ Pillow (PIL)")
except Exception as e:
    print(f"   ✗ Pillow error: {e}")

# Test 2: DeepFace import
print("\n2. Testing DeepFace import...")
try:
    from deepface import DeepFace
    print("   ✓ DeepFace imported successfully")
    
    # Test if we can access the analyze function
    if hasattr(DeepFace, 'analyze'):
        print("   ✓ DeepFace.analyze is available")
    else:
        print("   ✗ DeepFace.analyze not found")
        
except ImportError as e:
    print(f"   ✗ DeepFace import error: {e}")
    print("   → Run: pip install deepface")
except Exception as e:
    print(f"   ✗ DeepFace error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Emotion detection module
print("\n3. Testing emotion_detection module...")
try:
    from ChatbotWebsite.chatbot import emotion_detection
    print(f"   ✓ Module loaded")
    print(f"   → DEEPFACE_AVAILABLE: {emotion_detection.DEEPFACE_AVAILABLE}")
    if hasattr(emotion_detection, 'DEEPFACE_ERROR') and emotion_detection.DEEPFACE_ERROR:
        print(f"   → DEEPFACE_ERROR: {emotion_detection.DEEPFACE_ERROR}")
    print(f"   → Available emotions: {list(emotion_detection.EMOTION_CONTEXT.keys())}")
except Exception as e:
    print(f"   ✗ Module error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Flask route imports
print("\n4. Testing Flask route imports...")
try:
    from ChatbotWebsite import create_app
    app = create_app()
    with app.app_context():
        from ChatbotWebsite.chatbot.routes import EMOTION_DETECTION_AVAILABLE, detect_emotion
        print(f"   ✓ Routes loaded")
        print(f"   → EMOTION_DETECTION_AVAILABLE: {EMOTION_DETECTION_AVAILABLE}")
        print(f"   → detect_emotion function: {detect_emotion is not None}")
except Exception as e:
    print(f"   ✗ Routes error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Try a simple emotion detection (optional)
print("\n5. Testing emotion detection with dummy image...")
try:
    from ChatbotWebsite.chatbot.emotion_detection import detect_emotion
    import numpy as np
    
    # Create a dummy image
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    
    result = detect_emotion(dummy_img)
    print(f"   ✓ Detection completed")
    print(f"   → Success: {result.get('success')}")
    print(f"   → Emotion: {result.get('emotion')}")
    print(f"   → Face detected: {result.get('face_detected')}")
    if result.get('error'):
        print(f"   → Error: {result.get('error')}")
except Exception as e:
    print(f"   ✗ Detection error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Diagnostic Complete")
print("=" * 70)
print("\nIf any tests failed, fix the issues before using emotion detection.")
print("Most common fix: pip install opencv-python deepface")
