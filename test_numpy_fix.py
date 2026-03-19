"""Test that numpy float32 serialization is fixed"""
import json
import numpy as np

# Simulate what DeepFace returns
test_result = {
    'dominant_emotion': 'happy',
    'emotion': {
        'happy': np.float32(85.5),
        'sad': np.float32(5.2),
        'neutral': np.float32(9.3)
    }
}

# Old way (would fail)
print("Testing OLD way (should fail):")
try:
    old_response = {
        "emotion": test_result['dominant_emotion'],
        "confidence": round(test_result['emotion'].get('happy', 0), 2),
        "all_emotions": {k: round(v, 2) for k, v in test_result['emotion'].items()}
    }
    json.dumps(old_response)
    print("  OLD way: PASSED (unexpected)")
except TypeError as e:
    print(f"  OLD way: FAILED as expected - {e}")

# New way (should work)
print("\nTesting NEW way (should work):")
try:
    dominant_emotion = str(test_result['dominant_emotion'])
    emotion_scores = test_result.get('emotion', {})
    confidence = float(emotion_scores.get('happy', 0))
    all_emotions = {str(k): float(v) for k, v in emotion_scores.items()}
    
    new_response = {
        "emotion": dominant_emotion,
        "confidence": round(confidence, 2),
        "all_emotions": all_emotions
    }
    json_str = json.dumps(new_response)
    print(f"  NEW way: PASSED")
    print(f"  Response: {json_str}")
except TypeError as e:
    print(f"  NEW way: FAILED - {e}")

print("\n" + "="*50)
print("Fix verification complete!")
