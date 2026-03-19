"""
Facial Emotion Detection Module for SoulMate Chatbot
Uses DeepFace and OpenCV to detect emotions from webcam images
"""

import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image
import logging
import os

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
logging.getLogger('tensorflow').setLevel(logging.ERROR)

# Import DeepFace with error handling
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
    DEEPFACE_ERROR = None
except ImportError as e:
    print(f"Warning: DeepFace not available. Emotion detection disabled. Error: {e}")
    DEEPFACE_AVAILABLE = False
    DEEPFACE_ERROR = str(e)
except Exception as e:
    print(f"Warning: DeepFace import failed. Error: {e}")
    DEEPFACE_AVAILABLE = False
    DEEPFACE_ERROR = str(e)

# Emotion mapping for mental health context
EMOTION_CONTEXT = {
    "angry": {
        "mood": "angry",
        "response_style": "calming",
        "message": "I notice you might be feeling frustrated or upset. Would you like to talk about what's bothering you?",
        "color": "#ef4444",
        "icon": "😠"
    },
    "disgust": {
        "mood": "uncomfortable",
        "response_style": "gentle",
        "message": "I sense some discomfort. I'm here to listen if you want to share what's on your mind.",
        "color": "#84cc16",
        "icon": "🤢"
    },
    "fear": {
        "mood": "anxious",
        "response_style": "reassuring",
        "message": "You seem worried or anxious. Take a deep breath - I'm here to support you.",
        "color": "#a855f7",
        "icon": "😨"
    },
    "happy": {
        "mood": "happy",
        "response_style": "celebratory",
        "message": "You look happy! That's wonderful to see. What's bringing you joy today?",
        "color": "#22c55e",
        "icon": "😊"
    },
    "sad": {
        "mood": "sad",
        "response_style": "empathetic",
        "message": "I can see you might be feeling down. I'm here for you - would you like to talk about it?",
        "color": "#3b82f6",
        "icon": "😢"
    },
    "surprise": {
        "mood": "surprised",
        "response_style": "gentle",
        "message": "You seem surprised! Is everything okay?",
        "color": "#f59e0b",
        "icon": "😲"
    },
    "neutral": {
        "mood": "neutral",
        "response_style": "gentle",
        "message": "How are you feeling today? I'm here to chat whenever you're ready.",
        "color": "#6b7280",
        "icon": "😐"
    }
}


def decode_base64_image(base64_string):
    """
    Decode base64 image string to numpy array
    
    Args:
        base64_string: Base64 encoded image string
        
    Returns:
        numpy array: Decoded image
    """
    try:
        # Check if input is valid
        if not base64_string or not isinstance(base64_string, str):
            print("Error: Invalid base64 string")
            return None
        
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Clean up the string - remove any whitespace or newlines
        base64_string = base64_string.strip()
        
        # Add padding if needed
        padding = 4 - len(base64_string) % 4
        if padding != 4:
            base64_string += '=' * padding
        
        # Decode base64
        try:
            img_data = base64.b64decode(base64_string)
        except Exception as decode_err:
            print(f"Error decoding base64: {decode_err}")
            return None
        
        # Convert to PIL Image
        try:
            img = Image.open(BytesIO(img_data))
        except Exception as img_err:
            print(f"Error opening image: {img_err}")
            return None
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Convert to numpy array
        img_array = np.array(img)
        
        # Validate array
        if img_array is None or img_array.size == 0:
            print("Error: Decoded image is empty")
            return None
            
        return img_array
    except Exception as e:
        print(f"Error decoding image: {e}")
        import traceback
        traceback.print_exc()
        return None


def detect_emotion(image_data):
    """
    Detect emotion from image using DeepFace
    
    Args:
        image_data: Either base64 string or numpy array
        
    Returns:
        dict: Emotion detection results
    """
    try:
        # Decode image if base64 string
        if isinstance(image_data, str):
            img = decode_base64_image(image_data)
            if img is None:
                return {
                    "success": True,  # Return success with fallback
                    "emotion": "neutral",
                    "confidence": 100,
                    "face_detected": False,
                    "context": EMOTION_CONTEXT['neutral'],
                    "note": "Could not decode image. Using neutral response."
                }
        else:
            img = image_data
        
        # Check if DeepFace is available
        if not DEEPFACE_AVAILABLE:
            print("DeepFace not available, returning neutral fallback")
            return {
                "success": True,  # Return success with fallback
                "emotion": "neutral",
                "confidence": 100,
                "all_emotions": {"neutral": 100},
                "context": EMOTION_CONTEXT['neutral'],
                "face_detected": False,
                "note": "Emotion detection not available. Using neutral response."
            }
        
        # Analyze emotion using DeepFace
        try:
            result = DeepFace.analyze(
                img_path=img,
                actions=['emotion'],
                enforce_detection=False,
                silent=True
            )
        except Exception as deepface_error:
            print(f"DeepFace analysis error: {deepface_error}")
            # Return neutral if face detection fails
            return {
                "success": True,
                "emotion": "neutral",
                "confidence": 100,
                "all_emotions": {"neutral": 100},
                "context": EMOTION_CONTEXT['neutral'],
                "face_detected": False,
                "note": "Could not detect face clearly. Using neutral response."
            }
        
        # Handle list result (multiple faces)
        if isinstance(result, list):
            if len(result) == 0:
                return {
                    "success": True,
                    "emotion": "neutral",
                    "confidence": 100,
                    "all_emotions": {"neutral": 100},
                    "context": EMOTION_CONTEXT['neutral'],
                    "face_detected": False,
                    "note": "No face detected. Using neutral response."
                }
            result = result[0]
        
        # Check if result has required keys
        if not result or 'dominant_emotion' not in result:
            return {
                "success": True,
                "emotion": "neutral",
                "confidence": 100,
                "all_emotions": {"neutral": 100},
                "context": EMOTION_CONTEXT['neutral'],
                "face_detected": False,
                "note": "Could not analyze emotion. Using neutral response."
            }
        
        # Extract dominant emotion
        dominant_emotion = str(result['dominant_emotion'])
        emotion_scores = result.get('emotion', {})
        
        # Get confidence for dominant emotion and convert to Python float
        confidence = float(emotion_scores.get(dominant_emotion, 0))
        
        # Convert all emotion scores to Python floats
        all_emotions = {str(k): float(v) for k, v in emotion_scores.items()}
        
        # Get context for the emotion
        context = EMOTION_CONTEXT.get(dominant_emotion.lower(), EMOTION_CONTEXT['neutral'])
        
        return {
            "success": True,
            "emotion": dominant_emotion,
            "confidence": round(confidence, 2),
            "all_emotions": all_emotions,
            "context": context,
            "face_detected": True
        }
        
    except Exception as e:
        print(f"Error detecting emotion: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "emotion": "neutral",
            "confidence": 0,
            "context": EMOTION_CONTEXT['neutral'],
            "face_detected": False
        }


def get_emotion_suggestion(emotion):
    """
    Get suggestion based on detected emotion
    
    Args:
        emotion: Detected emotion string
        
    Returns:
        dict: Suggestion with message and styling
    """
    emotion_lower = emotion.lower() if emotion else 'neutral'
    return EMOTION_CONTEXT.get(emotion_lower, EMOTION_CONTEXT['neutral'])


def analyze_emotion_trend(emotion_history):
    """
    Analyze emotion trend from history
    
    Args:
        emotion_history: List of emotion detection results
        
    Returns:
        dict: Trend analysis
    """
    if not emotion_history:
        return {
            "trend": "neutral",
            "stability": "stable",
            "suggestion": "Start tracking your emotions to see patterns."
        }
    
    # Count emotions
    emotion_counts = {}
    for entry in emotion_history:
        emotion = entry.get('emotion', 'neutral')
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    
    # Find dominant emotion
    dominant = max(emotion_counts, key=emotion_counts.get)
    
    # Calculate stability
    total = len(emotion_history)
    dominant_count = emotion_counts[dominant]
    stability_score = dominant_count / total
    
    if stability_score > 0.7:
        stability = "stable"
    elif stability_score > 0.4:
        stability = "moderate"
    else:
        stability = "fluctuating"
    
    # Generate suggestion
    if dominant in ['sad', 'fear', 'angry']:
        suggestion = f"You've been feeling {dominant} frequently. Consider talking to someone or trying mindfulness exercises."
    elif dominant == 'happy':
        suggestion = "Great to see you've been happy! Keep doing what works for you."
    else:
        suggestion = "Your emotions have been balanced. Keep checking in with yourself."
    
    return {
        "trend": dominant,
        "stability": stability,
        "emotion_distribution": emotion_counts,
        "suggestion": suggestion
    }


# Test function
if __name__ == "__main__":
    print("Emotion Detection Module Test")
    print("=" * 50)
    
    # Test with a sample image path (if provided)
    import sys
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
        print(f"Testing with image: {test_image}")
        result = detect_emotion(test_image)
        print(f"Result: {result}")
    else:
        print("Module loaded successfully!")
        print("Available emotions:", list(EMOTION_CONTEXT.keys()))
