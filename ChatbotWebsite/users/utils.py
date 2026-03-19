from flask import url_for, current_app
from flask_mail import Message
import secrets
import os
from PIL import Image
from ChatbotWebsite import mail
import numpy as np
from typing import List, Dict, Any, Optional


# function to save the user profile picture
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(
        current_app.root_path, "static/profile_images", picture_fn
    )
    output_size = (190, 190)
    image = Image.open(form_picture).convert("RGB")
    image.thumbnail(output_size)
    image.save(picture_path)

    return picture_fn


# function to send the reset password email
def send_reset_email(user):
    if user is None:
        raise ValueError("Cannot send reset email: user is None")
    
    token = user.get_reset_token()
    reset_url = url_for('users.reset_token', token=token, _external=True)
    
    # Check if we should use console mode (for development)
    use_console = current_app.config.get('MAIL_USE_CONSOLE', False)
    
    if use_console:
        # Print to console for development
        print("\n" + "="*70)
        print("PASSWORD RESET LINK (Development Mode - Email not sent)")
        print("="*70)
        print(f"User: {user.username} ({user.email})")
        print(f"Reset Link: {reset_url}")
        print("="*70 + "\n")
        # Return the URL so it can be displayed on the page
        return reset_url


def _score_text_sentiment(texts: List[str]) -> Dict[str, Any]:
    """
    Lightweight sentiment-style scoring over a list of texts.
    Uses numpy vectorized operations to keep things fast even for large histories.
    """
    if not texts:
        return {
            "positive_score": 0.0,
            "negative_score": 0.0,
            "neutral_score": 1.0,
            "total_tokens": 0,
        }

    # Basic keyword lists – intentionally small and transparent.
    positive_words = np.array(
        [
            "happy",
            "great",
            "good",
            "calm",
            "relaxed",
            "hopeful",
            "better",
            "okay",
            "fine",
            "loved",
            "confident",
        ]
    )
    negative_words = np.array(
        [
            "sad",
            "depressed",
            "anxious",
            "anxiety",
            "stressed",
            "stress",
            "angry",
            "upset",
            "worried",
            "tired",
            "lonely",
            "hopeless",
            "bad",
        ]
    )

    joined = " ".join(t.lower() for t in texts if t)
    if not joined.strip():
        return {
            "positive_score": 0.0,
            "negative_score": 0.0,
            "neutral_score": 1.0,
            "total_tokens": 0,
        }

    tokens = np.array(joined.split())
    total_tokens = int(tokens.size)

    # Vectorized membership checks – this leverages fast CPU instructions via numpy.
    pos_hits = np.isin(tokens, positive_words)
    neg_hits = np.isin(tokens, negative_words)

    pos_count = float(pos_hits.sum())
    neg_count = float(neg_hits.sum())

    if total_tokens == 0:
        return {
            "positive_score": 0.0,
            "negative_score": 0.0,
            "neutral_score": 1.0,
            "total_tokens": 0,
        }

    positive_score = pos_count / total_tokens
    negative_score = neg_count / total_tokens
    neutral_score = max(0.0, 1.0 - (positive_score + negative_score))

    return {
        "positive_score": positive_score,
        "negative_score": negative_score,
        "neutral_score": neutral_score,
        "total_tokens": total_tokens,
    }


def _analyze_sentiment_tally(texts: List[str]) -> Dict[str, int]:
    """
    Analyze sentiment tally - count of positive, negative, and neutral interactions.
    Returns counts for each sentiment category.
    """
    positive_words = [
        "happy", "great", "good", "calm", "relaxed", "hopeful", "better",
        "okay", "fine", "loved", "confident", "joy", "excited", "grateful",
        "peaceful", "content", "cheerful", "optimistic", "proud", "energetic"
    ]
    negative_words = [
        "sad", "depressed", "anxious", "anxiety", "stressed", "stress",
        "angry", "upset", "worried", "tired", "lonely", "hopeless", "bad",
        "frustrated", "overwhelmed", "scared", "hurt", "disappointed", "miserable"
    ]
    
    tally = {"positive": 0, "negative": 0, "neutral": 0}
    
    for text in texts:
        if not text:
            continue
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            tally["positive"] += 1
        elif neg_count > pos_count:
            tally["negative"] += 1
        else:
            tally["neutral"] += 1
    
    return tally


def _calculate_stability_score(
    sentiment_tally: Dict[str, int],
    journal_moods: List[str],
    messages: List
) -> int:
    """
    Calculate emotional stability score (1-10) based on:
    - Sentiment consistency
    - Mood variation in journals
    - Message frequency and patterns
    """
    total_interactions = sum(sentiment_tally.values())
    if total_interactions == 0:
        return 5  # Default neutral score
    
    # Calculate sentiment consistency (higher positive ratio = higher stability)
    positive_ratio = sentiment_tally["positive"] / total_interactions
    negative_ratio = sentiment_tally["negative"] / total_interactions
    
    # Base score from sentiment (0-6 points)
    sentiment_score = (positive_ratio * 6) - (negative_ratio * 2)
    
    # Mood consistency bonus (0-2 points)
    mood_consistency = 0
    if journal_moods:
        unique_moods = len(set(journal_moods))
        total_moods = len(journal_moods)
        if total_moods > 0:
            # More consistent moods = higher score
            mood_consistency = max(0, 2 - (unique_moods / total_moods * 2))
    
    # Activity engagement bonus (0-2 points)
    activity_score = min(2, total_interactions / 20)  # Max at 20 interactions
    
    # Calculate final score (1-10 range)
    stability = 5 + sentiment_score + mood_consistency + activity_score
    stability = max(1, min(10, int(stability)))  # Clamp between 1-10
    
    return stability


def _generate_self_care_suggestions(
    risk_level: str,
    dominant_mood: Optional[str],
    sentiment_tally: Dict[str, int],
    stability_score: int
) -> List[str]:
    """
    Generate three specific, actionable self-care suggestions based on analysis.
    """
    suggestions = []
    
    # Suggestion 1: Based on risk level and stability
    if risk_level == "high" or stability_score <= 4:
        suggestions.append(
            "Practice the 5-4-3-2-1 grounding technique: Name 5 things you see, 4 you can touch, 3 you hear, 2 you smell, and 1 you taste. Use this when feeling overwhelmed."
        )
    elif risk_level == "moderate" or stability_score <= 6:
        suggestions.append(
            "Schedule a 10-minute 'worry time' daily. Write down concerns during this window, then set them aside. This helps contain anxiety."
        )
    else:
        suggestions.append(
            "Start a gratitude practice: Write down 3 specific things you're thankful for each morning to reinforce positive patterns."
        )
    
    # Suggestion 2: Based on dominant mood
    if dominant_mood:
        mood_lower = dominant_mood.lower()
        if "anxious" in mood_lower or "stress" in mood_lower:
            suggestions.append(
                "Try box breathing: Inhale for 4 counts, hold for 4, exhale for 4, hold for 4. Repeat 5 cycles when anxiety rises."
            )
        elif "sad" in mood_lower or "depress" in mood_lower:
            suggestions.append(
                "Engage in behavioral activation: Schedule one pleasant activity daily (walk, music, hobby). Action precedes motivation."
            )
        elif "angry" in mood_lower or "frustrat" in mood_lower:
            suggestions.append(
                "Use the STOP technique: Stop, Take a breath, Observe your feelings, Proceed mindfully. Practice when irritation builds."
            )
        elif "tired" in mood_lower or "exhaust" in mood_lower:
            suggestions.append(
                "Implement sleep hygiene: Set a consistent bedtime, avoid screens 1 hour before sleep, and create a relaxing wind-down routine."
            )
        else:
            suggestions.append(
                "Practice self-compassion: Speak to yourself as you would a good friend. Write a kind letter to yourself during difficult moments."
            )
    else:
        suggestions.append(
            "Begin mood tracking: Rate your emotional state (1-10) three times daily to identify patterns and triggers."
        )
    
    # Suggestion 3: Based on sentiment distribution
    if sentiment_tally["negative"] > sentiment_tally["positive"]:
        suggestions.append(
            "Challenge negative thoughts using CBT: When a negative thought arises, ask 'What evidence supports this? What contradicts it? What's a balanced view?'"
        )
    elif sentiment_tally["positive"] > sentiment_tally["negative"]:
        suggestions.append(
            "Build on your strengths: Identify one thing that went well today and note what YOU did to make it happen. Amplify these actions."
        )
    else:
        suggestions.append(
            "Create a coping toolkit: List 5 activities that soothe you (music, nature, talking to a friend). Use one when you notice mood shifts."
        )
    
    return suggestions


def analyze_user_activity(
    user,
    messages: List["ChatMessage"],
    journals: List["Journal"],
    extra_text: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compute a comprehensive mental state snapshot with CBT-based analysis.

    - Uses numpy-based scoring for performance.
    - Relies only on local keywords; no external ML calls.
    - Designed to be fast enough to run frequently.
    """
    # Collect user-authored content
    text_chunks: List[str] = []
    for m in messages:
        # Treat non-bot messages as user content where applicable
        try:
            sender = getattr(m, "sender", "").lower()
        except Exception:
            sender = ""
        if sender in ("user", "you", ""):
            text_chunks.append(getattr(m, "message", "") or "")
        else:
            # Some datasets only store user messages – be permissive
            text_chunks.append(getattr(m, "message", "") or "")

    journal_moods: List[str] = []
    journal_texts: List[str] = []
    for j in journals:
        journal_moods.append((getattr(j, "mood", "") or "").lower())
        journal_texts.append(getattr(j, "content", "") or "")

    if extra_text:
        text_chunks.append(extra_text)

    sentiment = _score_text_sentiment(text_chunks + journal_texts)
    
    # NEW: Sentiment Tally Analysis
    sentiment_tally = _analyze_sentiment_tally(text_chunks + journal_texts)

    # Simple mood aggregation from journal moods
    mood_array = np.array([m for m in journal_moods if m])
    top_mood: Optional[str] = None
    mood_counts: Dict[str, int] = {}
    if mood_array.size > 0:
        unique, counts = np.unique(mood_array, return_counts=True)
        mood_counts = {str(k): int(v) for k, v in zip(unique, counts)}
        top_mood = str(unique[int(np.argmax(counts))])

    # Coarse-grained mental state inference based on sentiment indicators
    pos = sentiment["positive_score"]
    neg = sentiment["negative_score"]
    neu = sentiment.get("neutral_score", 0.0)

    if neg > 0.12 and neg > pos:
        mental_state = "Elevated distress indicators detected. Prioritizing self-care and professional support is recommended."
        risk_level = "high"
    elif neg > 0.06 and neg > pos:
        mental_state = "Moderate distress signals present. Implementing coping strategies and monitoring mood changes is advised."
        risk_level = "moderate"
    elif pos > 0.15 and pos > neg:
        mental_state = "Generally stable and improving mood patterns observed. Continue current wellness practices."
        risk_level = "low"
    elif neu >= 0.6 and pos >= neg:
        mental_state = "Neutral mood indicators. Maintaining balance through regular self-care activities."
        risk_level = "low"
    else:
        mental_state = "Mixed emotional signals. Further observation and journaling recommended for clarity."
        risk_level = "unknown"

    # NEW: Calculate Stability Score
    stability_score = _calculate_stability_score(sentiment_tally, journal_moods, messages)
    
    # NEW: Generate Self-Care Suggestions
    suggestions = _generate_self_care_suggestions(
        risk_level, top_mood, sentiment_tally, stability_score
    )

    return {
        "user_id": getattr(user, "id", None),
        "username": getattr(user, "username", ""),
        "sentiment": sentiment,
        "sentiment_tally": sentiment_tally,
        "journal_mood_counts": mood_counts,
        "dominant_journal_mood": top_mood,
        "mental_state_summary": mental_state,
        "risk_level": risk_level,
        "stability_score": stability_score,
        "suggestions": suggestions,
        "message_count": len(messages),
        "journal_count": len(journals),
    }
    
    # Try to send actual email
    try:
        msg = Message(
            "Password Reset Request", 
            sender=current_app.config.get('MAIL_USERNAME', 'noreply@chatbot.com'), 
            recipients=[user.email]
        )
        msg.body = f"""To reset your password, visit the following link:
{reset_url}
Please do not reply to this email and share this email with anyone.
    
If you did not make this request then simply ignore this email and no changes will be made.
"""
        mail.send(msg)
        return None  # Email sent successfully, no URL to display
    except Exception as e:
        # If email sending fails, fall back to console mode
        current_app.logger.warning(f"Failed to send email, using console mode: {e}")
        print("\n" + "="*70)
        print("PASSWORD RESET LINK (Email sending failed - using console)")
        print("="*70)
        print(f"User: {user.username} ({user.email})")
        print(f"Reset Link: {reset_url}")
        print("="*70 + "\n")
        # Return the URL so it can be displayed on the page as fallback
        return reset_url
