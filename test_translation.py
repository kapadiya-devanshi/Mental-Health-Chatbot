"""
Test script for multilingual translation functionality
"""

import sys
sys.path.insert(0, 'g:\\SoulMate')

from ChatbotWebsite.chatbot.translator import (
    detect_language,
    translate_to_english,
    translate_from_english,
    get_language_name,
    process_multilingual_chat,
    translate_response,
    SUPPORTED_LANGUAGES
)

def test_language_detection():
    """Test language detection for various languages."""
    print("=" * 60)
    print("TESTING LANGUAGE DETECTION")
    print("=" * 60)
    
    test_phrases = [
        ("Hello, how are you?", "en"),
        ("नमस्ते, आप कैसे हैं?", "hi"),
        ("નમસ્તે, તમે કેમ છો?", "gu"),
        ("Hola, ¿cómo estás?", "es"),
        ("Bonjour, comment allez-vous?", "fr"),
        ("مرحبا، كيف حالك؟", "ar"),
        ("你好，你好吗？", "zh-cn"),
        ("こんにちは、お元気ですか？", "ja"),
        ("안녕하세요, 어떻게 지내세요?", "ko"),
    ]
    
    for phrase, expected in test_phrases:
        detected = detect_language(phrase)
        lang_name = get_language_name(detected)
        status = "✓" if detected == expected else "✗"
        print(f"{status} Text: {phrase[:30]}...")
        print(f"  Detected: {detected} ({lang_name}) | Expected: {expected}")
        print()

def test_translation_to_english():
    """Test translation to English."""
    print("=" * 60)
    print("TESTING TRANSLATION TO ENGLISH")
    print("=" * 60)
    
    test_phrases = [
        "नमस्ते, मैं तनाव में हूं",
        "નમસ્તે, હું તણાવમાં છું",
        "Hola, estoy estresado",
        "Bonjour, je suis stressé",
        "مرحبا، أنا متوتر",
        "你好，我感到压力",
    ]
    
    for phrase in test_phrases:
        result = translate_to_english(phrase)
        print(f"Original ({result['source_lang']}): {phrase}")
        print(f"Translated: {result['translated_text']}")
        print(f"Confidence: {result.get('confidence', 'N/A')}")
        print()

def test_translation_from_english():
    """Test translation from English to other languages."""
    print("=" * 60)
    print("TESTING TRANSLATION FROM ENGLISH")
    print("=" * 60)
    
    english_text = "I understand you're going through a difficult time. I'm here to help you."
    target_languages = ['hi', 'gu', 'es', 'fr', 'ar', 'zh-cn']
    
    print(f"English: {english_text}\n")
    
    for lang in target_languages:
        result = translate_from_english(english_text, lang)
        lang_name = get_language_name(lang)
        print(f"{lang_name} ({lang}): {result['translated_text']}")
        print()

def test_full_pipeline():
    """Test the complete multilingual chat pipeline."""
    print("=" * 60)
    print("TESTING FULL MULTILINGUAL PIPELINE")
    print("=" * 60)
    
    # Simulate user messages in different languages
    user_messages = [
        "I am feeling very anxious today",
        "मुझे आज बहुत चिंता हो रही है",
        "Hoy me siento muy ansioso",
        "我今天感觉很焦虑",
    ]
    
    for msg in user_messages:
        print(f"User Message: {msg}")
        
        # Step 1: Process input (detect + translate to English)
        input_data = process_multilingual_chat(msg, session_id="test_session")
        print(f"  Detected Language: {input_data['language_name']} ({input_data['detected_language']})")
        print(f"  Translated (EN): {input_data['processed_text']}")
        
        # Step 2: Simulate NLP response (English)
        english_response = "I hear that you're feeling anxious. Let's take a moment to breathe together. Try inhaling slowly for 4 counts..."
        print(f"  Bot Response (EN): {english_response}")
        
        # Step 3: Translate response back
        final_response = translate_response(english_response, session_id="test_session")
        print(f"  Bot Response ({input_data['language_name']}): {final_response}")
        print("-" * 60)
        print()

def test_supported_languages():
    """Display all supported languages."""
    print("=" * 60)
    print("SUPPORTED LANGUAGES")
    print("=" * 60)
    
    print(f"Total supported languages: {len(SUPPORTED_LANGUAGES)}\n")
    
    # Group by region for display
    indian_languages = ['hi', 'gu', 'bn', 'ta', 'te', 'mr', 'ur', 'pa', 'ml', 'kn', 'or', 'as', 'ne', 'si']
    european = ['en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'ru', 'uk']
    asian = ['zh-cn', 'zh-tw', 'ja', 'ko', 'th', 'vi', 'id', 'ms', 'tl', 'my']
    middle_eastern = ['ar', 'fa', 'he', 'ps', 'ku']
    african = ['af', 'am', 'ha', 'sw', 'so', 'ny', 'xh', 'yo', 'zu']
    
    print("Indian Languages:")
    for lang in indian_languages:
        if lang in SUPPORTED_LANGUAGES:
            print(f"  {lang}: {SUPPORTED_LANGUAGES[lang]}")
    
    print("\nEuropean Languages:")
    for lang in european:
        if lang in SUPPORTED_LANGUAGES:
            print(f"  {lang}: {SUPPORTED_LANGUAGES[lang]}")
    
    print("\nAsian Languages:")
    for lang in asian:
        if lang in SUPPORTED_LANGUAGES:
            print(f"  {lang}: {SUPPORTED_LANGUAGES[lang]}")
    
    print()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SOULMATE CHATBOT - TRANSLATION SYSTEM TEST")
    print("=" * 60 + "\n")
    
    try:
        # Run all tests
        test_supported_languages()
        test_language_detection()
        test_translation_to_english()
        test_translation_from_english()
        test_full_pipeline()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
