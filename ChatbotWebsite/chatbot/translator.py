"""
Multilingual Translation Module for Soulmate Chatbot
Uses deep-translator library for translation and langdetect for language detection
"""

from deep_translator import GoogleTranslator
from langdetect import detect as langdetect_detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
import re
import time

# Set seed for consistent language detection
DetectorFactory.seed = 0

# Initialize translator cache
translator_cache = {}

def get_translator(target_lang='en'):
    """Get translator instance for target language with caching."""
    cache_key = target_lang
    if cache_key not in translator_cache:
        try:
            if target_lang == 'en':
                # For auto-detect to English
                translator_cache[cache_key] = None  # Will use single_detection
            else:
                translator_cache[cache_key] = GoogleTranslator(source='en', target=target_lang)
        except Exception as e:
            print(f"Error initializing translator for {target_lang}: {e}")
            return None
    return translator_cache.get(cache_key)

# Supported languages - Only Hindi, Gujarati, and English
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi',
    'gu': 'Gujarati'
}


def detect_language(text):
    """
    Detect the language of the input text using langdetect.
    Only supports English, Hindi, and Gujarati.
    
    Args:
        text (str): Input text to detect language
        
    Returns:
        str: Language code ('en', 'hi', or 'gu')
    """
    try:
        if not text or not isinstance(text, str):
            return 'en'
        
        # Clean text for detection
        cleaned_text = text.strip()
        if not cleaned_text:
            return 'en'
        
        # Limit text length for efficiency
        detection_text = cleaned_text[:500] if len(cleaned_text) > 500 else cleaned_text
        
        # Use langdetect for language detection
        lang_code = langdetect_detect(detection_text)
        
        if lang_code and len(lang_code) >= 2:
            # Normalize language codes
            detected_lang = lang_code.split('-')[0].lower()
            
            # Only allow supported languages: en, hi, gu
            if detected_lang in SUPPORTED_LANGUAGES:
                return detected_lang
            else:
                # Default to English for unsupported languages
                print(f"Language '{detected_lang}' not supported. Defaulting to English.")
                return 'en'
        return 'en'
    except LangDetectException as e:
        print(f"Language detection error (LangDetect): {e}")
        return 'en'
    except Exception as e:
        print(f"Language detection error: {e}")
        return 'en'


def translate_to_english(text, source_lang=None):
    """
    Translate text to English.
    
    Args:
        text (str): Text to translate
        source_lang (str, optional): Source language code. If None, auto-detect.
        
    Returns:
        dict: Contains 'translated_text', 'source_lang', 'confidence'
    """
    try:
        if not text or not isinstance(text, str):
            return {
                'translated_text': text,
                'source_lang': 'en',
                'confidence': 1.0,
                'is_translated': False
            }
        
        # Detect language if not provided
        if source_lang is None:
            source_lang = detect_language(text)
        
        # If already English, no translation needed
        if source_lang == 'en':
            return {
                'translated_text': text,
                'source_lang': 'en',
                'confidence': 1.0,
                'is_translated': False
            }
        
        # Validate source language is supported
        if source_lang not in SUPPORTED_LANGUAGES:
            print(f"Warning: Language '{source_lang}' may not be fully supported")
        
        # Perform translation using deep-translator
        for attempt in range(2):
            try:
                translator = GoogleTranslator(source=source_lang, target='en')
                translated = translator.translate(text)
                
                return {
                    'translated_text': translated,
                    'source_lang': source_lang,
                    'confidence': 0.9,
                    'is_translated': True
                }
            except Exception as inner_e:
                if attempt == 0:
                    time.sleep(0.5)
                    continue
                raise inner_e
        
        # If all attempts failed, return original
        return {
            'translated_text': text,
            'source_lang': source_lang,
            'confidence': 0.0,
            'is_translated': False,
            'error': 'Translation failed after retries'
        }
    except Exception as e:
        print(f"Translation to English error: {e}")
        return {
            'translated_text': text,
            'source_lang': source_lang if source_lang else 'en',
            'confidence': 0.0,
            'is_translated': False,
            'error': str(e)
        }


def translate_from_english(text, target_lang):
    """
    Translate English text to target language.
    Only supports Hindi and Gujarati (English returns as-is).
    
    Args:
        text (str): English text to translate
        target_lang (str): Target language code ('hi' or 'gu')
        
    Returns:
        dict: Contains 'translated_text', 'target_lang', 'is_translated'
    """
    try:
        if not text or not isinstance(text, str):
            return {
                'translated_text': text,
                'target_lang': target_lang,
                'is_translated': False
            }
        
        # If target is English, no translation needed
        if target_lang == 'en':
            return {
                'translated_text': text,
                'target_lang': 'en',
                'is_translated': False
            }
        
        # Validate target language - only allow supported languages
        if target_lang not in SUPPORTED_LANGUAGES:
            print(f"Warning: Target language '{target_lang}' is not supported. Returning English.")
            return {
                'translated_text': text,
                'target_lang': 'en',
                'is_translated': False
            }
        
        # Perform translation using deep-translator with retry
        for attempt in range(2):
            try:
                translator = GoogleTranslator(source='en', target=target_lang)
                translated = translator.translate(text)
                
                return {
                    'translated_text': translated,
                    'target_lang': target_lang,
                    'is_translated': True
                }
            except Exception as inner_e:
                if attempt == 0:
                    time.sleep(0.5)
                    continue
                raise inner_e
        
        # If all attempts failed, return original
        return {
            'translated_text': text,
            'target_lang': target_lang,
            'is_translated': False,
            'error': 'Translation failed after retries'
        }
    except Exception as e:
        print(f"Translation from English error: {e}")
        return {
            'translated_text': text,
            'target_lang': target_lang,
            'is_translated': False,
            'error': str(e)
        }


def get_language_name(lang_code):
    """
    Get the full name of a language from its code.
    
    Args:
        lang_code (str): Language code
        
    Returns:
        str: Full language name
    """
    return SUPPORTED_LANGUAGES.get(lang_code, 'Unknown')


def is_language_supported(lang_code):
    """
    Check if a language is supported.
    
    Args:
        lang_code (str): Language code to check
        
    Returns:
        bool: True if supported
    """
    return lang_code in SUPPORTED_LANGUAGES


class TranslationPipeline:
    """
    Pipeline for handling multilingual chatbot conversations.
    Manages translation before NLP processing and after response generation.
    """
    
    def __init__(self):
        self.conversation_context = {}  # Store language preferences per session
    
    def process_input(self, text, session_id=None):
        """
        Process user input: detect language and translate to English.
        
        Args:
            text (str): User input text
            session_id (str, optional): Session identifier for context
            
        Returns:
            dict: Processing results with translated text and metadata
        """
        # Detect language
        detected_lang = detect_language(text)
        
        # Store language preference for this session
        if session_id:
            self.conversation_context[session_id] = detected_lang
        
        # Translate to English
        translation_result = translate_to_english(text, detected_lang)
        
        return {
            'original_text': text,
            'processed_text': translation_result['translated_text'],
            'detected_language': detected_lang,
            'language_name': get_language_name(detected_lang),
            'is_translated': translation_result['is_translated'],
            'confidence': translation_result.get('confidence', 1.0)
        }
    
    def process_output(self, english_response, session_id=None, target_lang=None):
        """
        Process chatbot output: translate from English to user's language.
        
        Args:
            english_response (str): English response from chatbot
            session_id (str, optional): Session identifier for context
            target_lang (str, optional): Target language (overrides session context)
            
        Returns:
            dict: Processing results with translated response
        """
        # Determine target language
        if target_lang is None and session_id:
            target_lang = self.conversation_context.get(session_id, 'en')
        elif target_lang is None:
            target_lang = 'en'
        
        # Translate from English
        translation_result = translate_from_english(english_response, target_lang)
        
        return {
            'original_response': english_response,
            'translated_response': translation_result['translated_text'],
            'target_language': target_lang,
            'language_name': get_language_name(target_lang),
            'is_translated': translation_result['is_translated']
        }
    
    def clear_context(self, session_id=None):
        """
        Clear conversation context.
        
        Args:
            session_id (str, optional): Specific session to clear, or all if None
        """
        if session_id:
            self.conversation_context.pop(session_id, None)
        else:
            self.conversation_context.clear()


# Global pipeline instance
translation_pipeline = TranslationPipeline()


def process_multilingual_chat(user_message, session_id=None):
    """
    Complete pipeline for processing multilingual chat.
    
    Workflow:
    1. Detect user message language
    2. Translate to English if needed
    3. Return processed data for NLP
    
    Args:
        user_message (str): Original user message
        session_id (str, optional): Session identifier
        
    Returns:
        dict: Complete processing information
    """
    return translation_pipeline.process_input(user_message, session_id)


def translate_response(english_response, session_id=None, target_lang=None):
    """
    Translate chatbot response back to user's language.
    
    Args:
        english_response (str): English response from NLP model
        session_id (str, optional): Session identifier
        target_lang (str, optional): Target language override
        
    Returns:
        str: Translated response in user's language
    """
    result = translation_pipeline.process_output(english_response, session_id, target_lang)
    return result['translated_response']


def batch_translate(texts, target_lang):
    """
    Translate multiple texts at once for efficiency.
    
    Args:
        texts (list): List of texts to translate
        target_lang (str): Target language code
        
    Returns:
        list: List of translated texts
    """
    try:
        if target_lang == 'en':
            return texts
        
        translator = GoogleTranslator(source='en', target=target_lang)
        translations = [translator.translate(text) for text in texts]
        return translations
    except Exception as e:
        print(f"Batch translation error: {e}")
        return texts
