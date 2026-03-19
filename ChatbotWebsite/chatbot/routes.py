from flask import Blueprint, render_template, request, jsonify, url_for, flash, redirect, session
from flask_login import current_user
from ChatbotWebsite import db
from ChatbotWebsite.chatbot.topic import *
from ChatbotWebsite.chatbot.chatbot import *
from ChatbotWebsite.chatbot.test import *
from ChatbotWebsite.chatbot.mindfulness import *
from ChatbotWebsite.chatbot.translator import (
    process_multilingual_chat, 
    translate_response, 
    get_language_name,
    translation_pipeline
)
from ChatbotWebsite.chatbot.self_learning import learning_engine
from ChatbotWebsite.models import ChatMessage
from datetime import datetime
chatbot = Blueprint("chatbot", __name__)

# Import emotion detection with error handling
try:
    from ChatbotWebsite.chatbot.emotion_detection import detect_emotion, get_emotion_suggestion
    EMOTION_DETECTION_AVAILABLE = True
except Exception as e:
    print(f"Warning: Emotion detection not available: {e}")
    EMOTION_DETECTION_AVAILABLE = False
    detect_emotion = None
    get_emotion_suggestion = None


# Chat Page (Main Page)
@chatbot.route("/chat")
def chat():
    try:
        messages = None
        if current_user.is_authenticated:
            today_start = datetime.combine(datetime.now().date(), datetime.min.time())
            messages = ChatMessage.query.filter(
                ChatMessage.user_id == current_user.id,
                ChatMessage.timestamp >= today_start
            ).order_by(ChatMessage.timestamp.asc()).all()
        return render_template(
            "chat/chat.html",
            title="Chat",
            topics=topics,
            messages=messages,
            tests=tests,
            mindfulness_exercises=mindfulness_exercises,
        )
    except Exception as e:
        print(f"Error in chat route: {e}")
        return render_template(
            "chat/chat.html",
            title="Chat",
            topics=topics,
            messages=[],
            tests=tests,
            mindfulness_exercises=mindfulness_exercises,
        )


# Chat Messages, Post reqeust, get response from chatbot and add both messages to database
@chatbot.route("/chat_messages", methods=["POST"])
def chatting():
    try:
        # Get user message
        original_message = request.form["msg"]
        
        # Get detected emotion from facial analysis if available
        detected_emotion = request.form.get("detected_emotion", None)
        emotion_data_str = request.form.get("emotion_data", None)
        
        # Parse emotion data if provided
        emotion_context = None
        if emotion_data_str:
            try:
                import json
                emotion_data = json.loads(emotion_data_str)
                emotion_context = emotion_data.get("context", {})
            except:
                pass
        
        # Generate session ID for translation context
        session_id = str(current_user.id) if current_user.is_authenticated else session.get('_id', 'anonymous')
        
        # Step 1: Process multilingual input (detect language and translate to English)
        translation_data = process_multilingual_chat(original_message, session_id)
        english_message = translation_data['processed_text']
        detected_lang = translation_data['detected_language']
        is_translated = translation_data['is_translated']
        
        # Step 2: Process with NLP model (using English text)
        response_data = get_response(english_message)
        
        # Extract response text and handle safety/medical flags
        english_response = response_data["response"]
        
        # Enhance response based on detected facial emotion
        if detected_emotion and emotion_context:
            # Add emotion-aware opening if the response doesn't already address emotions
            emotion_mood = emotion_context.get("mood", "")
            emotion_message = emotion_context.get("message", "")
            
            # Only prepend emotion message for certain emotions that need acknowledgment
            if emotion_mood in ["sad", "angry", "fear", "anxious"]:
                if not any(word in english_response.lower() for word in ["sorry", "understand", "hear"]):
                    english_response = f"{emotion_message}\n\n{english_response}"
        
        # If medical disclaimer is needed, prepend it to the response
        if response_data.get("medical_disclaimer"):
            english_response = "I'm an AI assistant, not a medical professional. " + english_response
        
        # If safety flag is triggered, ensure crisis resources are included
        if response_data.get("safety_flag"):
            crisis_info = "\n\nCrisis Resources:\n"
            for resource in response_data.get("crisis_resources", []):
                crisis_info += f"- {resource['name']}: {resource['contact']}\n"
            english_response += crisis_info
        
        # Step 3: Translate response back to user's language if needed
        # Translate if detected language is not English
        if detected_lang and detected_lang != 'en':
            final_response = translate_response(english_response, session_id, detected_lang)
        else:
            final_response = english_response
        
        # Store messages in database
        if current_user.is_authenticated:
            # Store original user message and translated response
            user_message = ChatMessage(sender="user", message=original_message, user=current_user)
            bot_message = ChatMessage(sender="bot", message=final_response, user=current_user)
            db.session.add(user_message)
            db.session.add(bot_message)
            db.session.commit()
            
            # Record for self-learning (store user pattern and intent)
            try:
                intent_tag = response_data.get("intent_tag", "unknown")
                learning_engine.learning_data["user_patterns"][original_message] = {
                    "intent_tag": intent_tag,
                    "timestamp": datetime.now().isoformat(),
                    "language": detected_lang
                }
                learning_engine._save_learning_data()
            except Exception as learn_err:
                print(f"Learning record error: {learn_err}")
        
        # Return response with translation metadata
        # Always return detected language info, not just when translated
        return jsonify({
            "msg": final_response,
            "safety_flag": response_data.get("safety_flag", False),
            "detected_language": detected_lang,
            "language_name": get_language_name(detected_lang),
            "was_translated": is_translated,
            "response_translated": detected_lang != 'en' and detected_lang is not None
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in chatting route: {e}")
        return jsonify({
            "msg": "I'm sorry, I encountered an error. Please try again.", 
            "safety_flag": False,
            "detected_language": None,
            "was_translated": False
        }), 500


# Topic, Post request, get contents from topic and add all messages to database
@chatbot.route("/topic", methods=["POST"])
def topic():
    try:
        title = request.form["title"]
        contents = get_content(title)
        if current_user.is_authenticated:
            user_message = ChatMessage(sender="user", message=title, user=current_user)
            db.session.add(user_message)
            for content in contents:
                bot_message = ChatMessage(sender="bot", message=content, user=current_user)
                db.session.add(bot_message)
            db.session.commit()
        return jsonify({"contents": contents})
    except Exception as e:
        db.session.rollback()
        print(f"Error in topic route: {e}")
        return jsonify({"contents": ["I'm sorry, I encountered an error. Please try again."]}), 500



# Test, Post request, get questions from test
@chatbot.route("/test", methods=["POST"])
def test():
    title = request.form["title"]
    questions = get_questions(title)
    if current_user.is_authenticated:
        user_message = ChatMessage(sender="user", message=title, user=current_user)
        db.session.add(user_message)
        db.session.commit()
    return jsonify({"questions": questions})


# Test Score, Post request, get score message from test and add result to database
@chatbot.route("/score", methods=["POST"])
def score():
    try:
        score = request.form["score"]
        title = request.form["title"]
        score_message = get_test_messages(title, score)
        if current_user.is_authenticated:
            bot_score_message = ChatMessage(
                sender="bot", message=score_message, user=current_user
            )
            db.session.add(bot_score_message)
            db.session.commit()
        return jsonify({"score_message": score_message})
    except Exception as e:
        db.session.rollback()
        print(f"Error in score route: {e}")
        return jsonify({"score_message": "I'm sorry, I encountered an error processing your test results. Please try again."}), 500


# Mindfulness, Post request, get description, file_name from mindfulness exercise
@chatbot.route("/mindfulness", methods=["POST"])
def mindfulness():
    title = request.form["title"]
    description, file_name = get_description(title)
    return jsonify({"description": description, "file_name": file_name})


# Edit Message, Post request to update message text
@chatbot.route("/edit_message", methods=["POST"])
def edit_message():
    if not current_user.is_authenticated:
        return jsonify({"success": False, "msg": "Unauthorized"}), 401
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "msg": "Invalid JSON"}), 400
        
        message_id = data.get("message_id")
        new_text = data.get("new_text")
        
        if not message_id or not new_text:
            return jsonify({"success": False, "msg": "Missing fields"}), 400
            
        msg = db.session.get(ChatMessage, message_id)
        if msg and msg.user_id == current_user.id and msg.sender == "user":
            msg.message = new_text
            db.session.commit()
            return jsonify({"success": True, "msg": "Message updated successfully"})
        return jsonify({"success": False, "msg": "Message not found or forbidden"}), 403
    except Exception as e:
        db.session.rollback()
        print(f"Error in edit_message route: {e}")
        return jsonify({"success": False, "msg": "An error occurred"}), 500


# Get Supported Languages
@chatbot.route("/languages", methods=["GET"])
def get_languages():
    """Return list of supported languages for translation."""
    from ChatbotWebsite.chatbot.translator import SUPPORTED_LANGUAGES
    languages = [{"code": code, "name": name} for code, name in SUPPORTED_LANGUAGES.items()]
    return jsonify({"languages": languages})


# Detect Language
@chatbot.route("/detect_language", methods=["POST"])
def detect_language_route():
    """Detect the language of provided text."""
    try:
        text = request.form.get("text", "")
        if not text:
            return jsonify({"language": "en", "language_name": "English", "confidence": 1.0})
        
        from ChatbotWebsite.chatbot.translator import detect_language, get_language_name
        lang_code = detect_language(text)
        lang_name = get_language_name(lang_code)
        
        return jsonify({
            "language": lang_code,
            "language_name": lang_name,
            "confidence": 0.9
        })
    except Exception as e:
        print(f"Error in detect_language route: {e}")
        return jsonify({"language": "en", "language_name": "English", "confidence": 1.0})


# Translation Health Check
@chatbot.route("/translation_status", methods=["GET"])
def translation_status():
    """Check if translation service is available."""
    try:
        from ChatbotWebsite.chatbot.translator import translate_from_english
        # Test with a simple translation
        test = translate_from_english("hello", "es")
        return jsonify({
            "status": "available",
            "supported_languages": 104,
            "test_translation": test['translated_text'] if test['is_translated'] else "hola"
        })
    except Exception as e:
        return jsonify({
            "status": "unavailable",
            "error": str(e)
        }), 503


# Facial Emotion Detection Endpoint
@chatbot.route("/detect_emotion", methods=["POST"])
def detect_emotion_endpoint():
    """
    Endpoint to detect emotion from webcam image
    Expects base64 encoded image in request
    """
    try:
        # Check if emotion detection is available
        if not EMOTION_DETECTION_AVAILABLE or detect_emotion is None:
            print("Emotion detection not available, returning fallback")
            return jsonify({
                "success": True,  # Return success with fallback
                "emotion": "neutral",
                "confidence": 100,
                "face_detected": False,
                "context": {
                    "mood": "neutral",
                    "response_style": "gentle",
                    "message": "How are you feeling today? I'm here to chat whenever you're ready.",
                    "color": "#6b7280",
                    "icon": "😐"
                },
                "note": "Emotion detection not available. Using neutral response."
            })
        
        # Get image data from request
        try:
            data = request.get_json()
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            return jsonify({
                "success": False,
                "error": "Invalid JSON data"
            }), 400
            
        if not data or 'image' not in data:
            return jsonify({
                "success": False,
                "error": "No image data provided"
            }), 400
        
        image_data = data['image']
        
        # Validate image data
        if not image_data or not isinstance(image_data, str):
            return jsonify({
                "success": False,
                "error": "Invalid image data"
            }), 400
        
        # Detect emotion
        result = detect_emotion(image_data)
        
        # Store emotion detection in session for context
        if result.get('success'):
            session['last_detected_emotion'] = result.get('emotion', 'neutral')
            session['emotion_confidence'] = result.get('confidence', 0)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in detect_emotion_endpoint: {e}")
        import traceback
        traceback.print_exc()
        # Return a fallback response instead of error
        return jsonify({
            "success": True,  # Return success with fallback
            "emotion": "neutral",
            "confidence": 100,
            "face_detected": False,
            "context": {
                "mood": "neutral",
                "response_style": "gentle",
                "message": "How are you feeling today? I'm here to chat whenever you're ready.",
                "color": "#6b7280",
                "icon": "😐"
            },
            "note": "An error occurred. Using neutral response."
        })


# Get emotion-based suggestion
@chatbot.route("/emotion_suggestion", methods=["GET"])
def emotion_suggestion():
    """
    Get suggestion based on detected emotion
    """
    try:
        # Check if emotion detection is available
        if not EMOTION_DETECTION_AVAILABLE or get_emotion_suggestion is None:
            return jsonify({
                "success": False,
                "error": "Emotion detection not available",
                "emotion": "neutral",
                "suggestion": {
                    "mood": "neutral",
                    "response_style": "gentle",
                    "message": "How are you feeling today? I'm here to chat whenever you're ready.",
                    "color": "#6b7280",
                    "icon": "😐"
                }
            }), 503
        
        emotion = request.args.get('emotion', session.get('last_detected_emotion', 'neutral'))
        suggestion = get_emotion_suggestion(emotion)
        
        return jsonify({
            "success": True,
            "emotion": emotion,
            "suggestion": suggestion
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Emotion Detection Status/Debug Endpoint
@chatbot.route("/emotion_status", methods=["GET"])
def emotion_status():
    """
    Check emotion detection system status
    """
    try:
        status = {
            "emotion_detection_available": EMOTION_DETECTION_AVAILABLE,
            "detect_emotion_function": detect_emotion is not None,
            "get_emotion_suggestion_function": get_emotion_suggestion is not None
        }
        
        # Try to get more info from emotion_detection module
        try:
            from ChatbotWebsite.chatbot.emotion_detection import DEEPFACE_AVAILABLE, DEEPFACE_ERROR, EMOTION_CONTEXT
            status["deepface_available"] = DEEPFACE_AVAILABLE
            status["deepface_error"] = DEEPFACE_ERROR
            status["available_emotions"] = list(EMOTION_CONTEXT.keys())
        except Exception as e:
            status["deepface_check_error"] = str(e)
        
        return jsonify({
            "success": True,
            "status": status
        })
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500
