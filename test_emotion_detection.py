"""
Test script for emotion detection
"""
import sys
import os

# Add project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Testing Emotion Detection Setup")
print("=" * 60)

# Test 1: Check OpenCV
print("\n1. Testing OpenCV...")
try:
    import cv2
    print(f"   ✓ OpenCV installed (version: {cv2.__version__})")
except ImportError as e:
    print(f"   ✗ OpenCV not installed: {e}")
    print("   Run: pip install opencv-python")

# Test 2: Check Pillow
print("\n2. Testing Pillow...")
try:
    from PIL import Image
    print("   ✓ Pillow installed")
except ImportError as e:
    print(f"   ✗ Pillow not installed: {e}")
    print("   Run: pip install Pillow")

# Test 3: Check NumPy
print("\n3. Testing NumPy...")
try:
    import numpy as np
    print(f"   ✓ NumPy installed (version: {np.__version__})")
except ImportError as e:
    print(f"   ✗ NumPy not installed: {e}")

# Test 4: Check DeepFace
print("\n4. Testing DeepFace...")
try:
    from deepface import DeepFace
    print("   ✓ DeepFace installed")
    
    # Test if we can load the model
    print("\n5. Testing DeepFace model loading...")
    print("   This may take a moment (downloading models if needed)...")
    
    # Create a dummy image for testing
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    
    try:
        result = DeepFace.analyze(
            img_path=dummy_img,
            actions=['emotion'],
            enforce_detection=False,
            silent=True
        )
        print("   ✓ DeepFace model loaded successfully")
        print(f"   Sample result: {result}")
    except Exception as e:
        print(f"   ⚠ DeepFace model test failed: {e}")
        print("   This is normal on first run - models will download automatically")
        
except ImportError as e:
    print(f"   ✗ DeepFace not installed: {e}")
    print("   Run: pip install deepface")
except Exception as e:
    print(f"   ✗ DeepFace error: {e}")

# Test 5: Check emotion_detection module
print("\n6. Testing emotion_detection module...")
try:
    from ChatbotWebsite.chatbot.emotion_detection import detect_emotion, EMOTION_CONTEXT
    print("   ✓ emotion_detection module loaded")
    print(f"   Available emotions: {list(EMOTION_CONTEXT.keys())}")
except Exception as e:
    print(f"   ✗ emotion_detection module error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
print("\nIf all tests passed, emotion detection should work.")
print("If DeepFace model test failed, it will download on first use.")
