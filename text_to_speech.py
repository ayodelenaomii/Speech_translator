from gtts import gTTS
import os
import pygame
import io
from Speech_translator import translate_text_with_mbart, translate_text_with_spitch, translate_text_fallback
from dotenv import load_dotenv
import logging
import requests
import tempfile
import platform
import json

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize pygame mixer for audio playback
try:
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except:
    PYGAME_AVAILABLE = False
    logger.warning("Pygame not available, will use system audio playback")

# Language mapping for gTTS (Google TTS supported languages)
GTTS_LANGUAGE_MAP = {
    # African languages supported by gTTS
    'yo': 'yo',      # Yoruba - Note: Limited support
    'ha': 'ha',      # Hausa  - Note: Limited support
    'ig': 'ig',      # Igbo - Note: Limited support
    'sw': 'sw',      # Swahili
    'zu': 'zu',      # Zulu
    'xh': 'xh',      # Xhosa
    'af': 'af',      # Afrikaans
    'am': 'am',      # Amharic - Note: Limited support
    'en': 'en',      # English
    
    # Other languages - map MBART codes to gTTS codes
    'en_XX': 'en',   # English
    'fr_XX': 'fr',   # French
    'es_XX': 'es',   # Spanish
    'de_DE': 'de',   # German
    'it_IT': 'it',   # Italian
    'pt_XX': 'pt',   # Portuguese
    'nl_XX': 'nl',   # Dutch
    'pl_PL': 'pl',   # Polish
    'ro_RO': 'ro',   # Romanian
    'bg_BG': 'bg',   # Bulgarian
    'fi_FI': 'fi',   # Finnish
    'sv_SE': 'sv',   # Swedish
    'no_NO': 'no',   # Norwegian
    'ru_RU': 'ru',   # Russian
    'zh_CN': 'zh',   # Chinese (Simplified)
    'zh_TW': 'zh-tw', # Chinese (Traditional)
    'ja_XX': 'ja',   # Japanese
    'ko_KR': 'ko',   # Korean
    'hi_IN': 'hi',   # Hindi
    'bn_IN': 'bn',   # Bengali
    'pa_IN': 'pa',   # Punjabi
    'ur_PK': 'ur',   # Urdu
    'th_TH': 'th',   # Thai
    'vi_VN': 'vi',   # Vietnamese
    'id_ID': 'id',   # Indonesian
    'ms_MY': 'ms',   # Malay
}

def play_audio_file(file_path):
    """Play audio file using pygame"""
    try:
        if not PYGAME_AVAILABLE:
            return False
            
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
            
        logger.info(f"Audio playback completed: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Audio playback failed: {e}")
        return False

def cross_platform_play_audio(file_path):
    """Cross-platform audio playback"""
    try:
        # Try pygame first (cross-platform)
        if PYGAME_AVAILABLE and play_audio_file(file_path):
            return True
            
        # Fallback to system-specific commands
        system = platform.system().lower()
        
        if system == "windows":
            os.system(f'start /min "" "{file_path}"')
        elif system == "darwin":  # macOS
            os.system(f'open "{file_path}"')
        elif system == "linux":
            os.system(f'xdg-open "{file_path}" > /dev/null 2>&1')
        else:
            logger.warning(f"Unsupported platform: {system}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Cross-platform audio playback failed: {e}")
        return False

def speak_text(text, src_lang, tgt_lang, src_type="Others", tgt_type="Others"):
    """
    Translate text and convert to speech
    
    Args:
        text (str): Input text to translate and speak
        src_lang (str): Source language code
        tgt_lang (str): Target language code
        src_type (str): Source language type ("African" or "Others")
        tgt_type (str): Target language type ("African" or "Others")
    """
    try:
        if not text or not text.strip():
            logger.warning("Empty text provided")
            return False
            
        logger.info(f"Processing text: '{text}' from {src_lang} to {tgt_lang}")
        
        # Translate the text
        translated_text = translate_text_logic(text, src_lang, tgt_lang, src_type, tgt_type)
        
        if not translated_text:
            logger.error("Translation failed")
            return False
            
        print(f" Translated text: {translated_text}")
        
        # Convert to speech
        success = text_to_speech(translated_text, tgt_lang)
        
        return success
        
    except Exception as e:
        logger.error(f"speak_text failed: {e}")
        return False

def translate_text_logic(text, src_lang, tgt_lang, src_type, tgt_type):
    """
    Translate text using appropriate method based on language types
    """
    try:
        logger.info(f"Translating: '{text}' from {src_lang} ({src_type}) to {tgt_lang} ({tgt_type})")
        
        # Determine translation method
        if src_type.lower() == "others" and tgt_type.lower() == "others":
            # Both are non-African languages - use MBART
            return translate_text_with_mbart(text, src_lang, tgt_lang)
            
        else:
            # At least one is African language - try Spitch first
            spitch_api_key = os.getenv('SPITCH_API_KEY')
            
            if spitch_api_key:
                try:
                    return translate_text_with_spitch(text, src_lang, tgt_lang)
                except Exception as e:
                    logger.warning(f"Spitch translation failed: {e}")
                    logger.info("Falling back to fallback translator")
                    return translate_text_fallback(text, src_lang, tgt_lang)
            else:
                logger.info("Spitch API key not available, using fallback")
                return translate_text_fallback(text, src_lang, tgt_lang)
                
    except Exception as e:
        logger.error(f"Translation logic failed: {e}")
        # Final fallback
        return translate_text_fallback(text, src_lang, tgt_lang)

def text_to_speech(text, tgt_lang):
    """
    Convert text to speech using appropriate TTS service
    
    Args:
        text (str): Text to convert to speech
        tgt_lang (str): Target language code
        
    Returns:
        bool: Success status
    """
    try:
        if not text or not text.strip():
            logger.warning("Empty text for TTS")
            return False
            
        # Check if it's an African language that might be supported by Spitch
        african_langs = ['yo', 'ha', 'ig', 'sw', 'zu', 'xh', 'af', 'am']
        
        if tgt_lang in african_langs and os.getenv('SPITCH_API_KEY'):
            logger.info(f"Attempting Spitch TTS for {tgt_lang}")
            success = spitch_tts(text, tgt_lang)
            if success:
                return True
            else:
                logger.info("Spitch TTS failed, falling back to Google TTS")
        
        # Use Google TTS (fallback or primary choice)
        return google_tts(text, tgt_lang)
        
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        return False

def spitch_tts(text, tgt_lang):
    """
    Use Spitch API for text-to-speech in African languages
    
    Args:
        text (str): Text to convert to speech
        tgt_lang (str): Target language code
        
    Returns:
        bool: Success status
    """
    try:
        # Load Spitch API credentials
        spitch_api_key = os.getenv("SPITCH_API_KEY")
        spitch_tts_url = os.getenv("SPITCH_TTS_URL", "https://api.spitch.com/v1/tts")
        
        if not spitch_api_key:
            logger.warning("Spitch API key not found")
            return False
            
        logger.info(f"Using Spitch TTS for {tgt_lang}: '{text}'")
        
        # Prepare headers
        headers = {
            'Authorization': f'Bearer {spitch_api_key}',
            'Content-Type': 'application/json',
            'Accept': 'audio/mpeg'
        }
        
        # Prepare payload
        payload = {
            'text': text.strip(),
            'language': tgt_lang,
            'voice': 'default',  # You can add voice selection later
            'speed': 1.0,
            'pitch': 1.0
        }
        
        # Convert payload to JSON string
        json_data = json.dumps(payload)
        
        # Make API request - FIXED VERSION
        try:
            response = requests.post(
                spitch_tts_url,
                headers=headers,
                data=json_data,  # Use 'data' instead of 'json' parameter
                timeout=30
            )
        except TypeError as e:
            # Alternative method if the above fails
            logger.warning(f"First TTS request method failed: {e}. Trying alternative.")
            response = requests.post(
                spitch_tts_url,
                headers=headers,
                timeout=30
            )
        
        if response.status_code == 200:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
                
            logger.info(f"Spitch TTS audio saved to: {temp_file_path}")
            
            # Play the audio
            success = cross_platform_play_audio(temp_file_path)
            
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")
                
            return success
            
        else:
            logger.error(f"Spitch TTS API error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Spitch TTS failed: {e}")
        return False

def google_tts(text, tgt_lang):
    """
    Use Google TTS for text-to-speech
    
    Args:
        text (str): Text to convert to speech
        tgt_lang (str): Target language code
        
    Returns:
        bool: Success status
    """
    try:
        # Map language code to gTTS format
        gtts_lang = GTTS_LANGUAGE_MAP.get(tgt_lang, tgt_lang.split('_')[0] if '_' in tgt_lang else tgt_lang)
        
        logger.info(f"Using Google TTS for {gtts_lang}: '{text}'")
        
        # Check if language is supported by gTTS
        try:
            # Create TTS object
            tts = gTTS(text=text, lang=gtts_lang, slow=False)
        except Exception as e:
            if "Language not supported" in str(e):
                logger.error(f"Google TTS failed: Language not supported: {gtts_lang}")
                # Try with English as fallback
                if gtts_lang != 'en':
                    logger.info("Falling back to English for TTS")
                    tts = gTTS(text=text, lang='en', slow=False)
                else:
                    raise Exception(f"Language not supported: {gtts_lang}")
            else:
                raise e
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            tts.save(temp_file.name)
            temp_file_path = temp_file.name
            
        logger.info(f"Google TTS audio saved to: {temp_file_path}")
        
        # Play the audio
        success = cross_platform_play_audio(temp_file_path)
        
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except Exception as e:
            logger.warning(f"Failed to delete temp file: {e}")
            
        return success
        
    except Exception as e:
        logger.error(f"Google TTS failed: {e}")
        return False

def test_tts():
    """Test TTS functionality"""
    test_cases = [
        ("Hello, how are you?", "en"),
        ("Bonjour, comment allez-vous?", "fr"),
        ("Bawo ni o se wa?", "yo"),
        ("Hola, ¿cómo estás?", "es")
    ]
    
    print(" Testing TTS Functions")
    print("=" * 40)
    
    for text, lang in test_cases:
        print(f"\n Testing: '{text}' in {lang}")
        success = text_to_speech(text, lang)
        print(f"Result: {' Success' if success else ' Failed'}")

if __name__ == "__main__":
    test_tts()