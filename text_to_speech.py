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
import threading
import base64
from spitch import Client



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
    'yo': 'yo', 'ha': 'ha', 'ig': 'ig', 'sw': 'sw', 'zu': 'zu', 'xh': 'xh', 'af': 'af', 'am': 'am', 'en': 'en',
    'en_XX': 'en', 'fr_XX': 'fr', 'es_XX': 'es', 'de_DE': 'de', 'it_IT': 'it', 'pt_XX': 'pt', 'nl_XX': 'nl',
    'pl_PL': 'pl', 'ro_RO': 'ro', 'bg_BG': 'bg', 'fi_FI': 'fi', 'sv_SE': 'sv', 'no_NO': 'no', 'ru_RU': 'ru',
    'zh_CN': 'zh', 'zh_TW': 'zh-tw', 'ja_XX': 'ja', 'ko_KR': 'ko', 'hi_IN': 'hi', 'bn_IN': 'bn', 'pa_IN': 'pa',
    'ur_PK': 'ur', 'th_TH': 'th', 'vi_VN': 'vi', 'id_ID': 'id', 'ms_MY': 'ms'
}

# Spitch language mapping for proper language codes
SPITCH_LANGUAGE_MAP = {
    'yo': 'yo',  # Yoruba
    'ha': 'ha',  # Hausa
    'ig': 'ig',  # Igbo
    'am': 'am',  # Amharic
    'en': 'en',  # English
}


def play_audio_file(file_path):
    try:
        if not PYGAME_AVAILABLE:
            return False
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
        logger.info(f"Audio playback completed: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Audio playback failed: {e}")
        return False

def cross_platform_play_audio(file_path):
    try:
        if PYGAME_AVAILABLE and play_audio_file(file_path):
            return True
        system = platform.system().lower()
        if system == "windows":
            os.system(f'start /min "" "{file_path}"')
        elif system == "darwin":
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

def delete_temp_file_later(path, delay=5):
    def delayed_delete():
        try:
            os.unlink(path)
            logger.info(f"Temp file deleted: {path}")
        except Exception as e:
            logger.warning(f"Failed to delete temp file: {e}")
    threading.Timer(delay, delayed_delete).start()

def speak_text(text, src_lang, tgt_lang, src_type="Others", tgt_type="Others"):
    try:
        if not text.strip():
            logger.warning("Empty text provided")
            return False
        logger.info(f"Processing text: '{text}' from {src_lang} to {tgt_lang}")
        translated_text = translate_text_logic(text, src_lang, tgt_lang, src_type, tgt_type)
        if not translated_text:
            logger.error("Translation failed")
            return False
        print(f" Translated text: {translated_text}")
        return text_to_speech(translated_text, tgt_lang)
    except Exception as e:
        logger.error(f"speak_text failed: {e}")
        return False

def translate_text_logic(text, src_lang, tgt_lang, src_type, tgt_type):
    try:
        logger.info(f"Translating: '{text}' from {src_lang} ({src_type}) to {tgt_lang} ({tgt_type})")
        if src_type.lower() == "others" and tgt_type.lower() == "others":
            return translate_text_with_mbart(text, src_lang, tgt_lang)
        spitch_api_key = os.getenv('SPITCH_API_KEY')
        if spitch_api_key:
            try:
                return translate_text_with_spitch(text, src_lang, tgt_lang)
            except Exception as e:
                logger.warning(f"Spitch translation failed: {e}")
        logger.info("Using fallback translator")
        return translate_text_fallback(text, src_lang, tgt_lang)
    except Exception as e:
        logger.error(f"Translation logic failed: {e}")
        return translate_text_fallback(text, src_lang, tgt_lang)

def text_to_speech(text, tgt_lang):
    try:
        if not text.strip():
            logger.warning("Empty text for TTS")
            return False
        african_langs = ['yo', 'ha', 'ig', 'sw', 'zu', 'xh', 'af', 'am']
        if tgt_lang in african_langs and os.getenv('SPITCH_API_KEY'):
            logger.info(f"Attempting Spitch TTS for {tgt_lang}")
            if spitch_tts(text, tgt_lang):
                return True
            logger.info("Spitch TTS failed, falling back to Google TTS")
        return google_tts(text, tgt_lang)
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        return False

def spitch_tts(text, tgt_lang):
    try:
        spitch_api_key = os.getenv("SPITCH_API_KEY")
        if not spitch_api_key:
            logger.warning("Spitch API key not found in environment variables")
            return False

        client = Client(api_key=spitch_api_key)

        spitch_lang = SPITCH_LANGUAGE_MAP.get(tgt_lang, tgt_lang)

        logger.info(f"Generating speech for language: {spitch_lang} and text: {text}")

        response = client.speech.generate(
            text=text,
            language=spitch_lang,
            voice='sade'
        )
  
        audio_bytes = response.read()

        if not audio_bytes:
            logger.error("No audio content received from Spitch")
            return False

        # Save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_file.write(audio_bytes)
            temp_path = tmp_file.name

        # Play the audio
        played = cross_platform_play_audio(temp_path)

        # Schedule file deletion
        delete_temp_file_later(temp_path)

        return played
    except Exception as e:
        logger.error(f"Spitch TTS failed: {e}")
        return False

def google_tts(text, tgt_lang):
    try:
        gtts_lang = GTTS_LANGUAGE_MAP.get(tgt_lang, tgt_lang.split('_')[0] if '_' in tgt_lang else tgt_lang)
        logger.info(f"Using Google TTS for {gtts_lang}: '{text}'")
        try:
            tts = gTTS(text=text, lang=gtts_lang, slow=False)
        except Exception as e:
            if "Language not supported" in str(e):
                logger.error(f"Google TTS failed: Language not supported: {gtts_lang}")
                if gtts_lang != 'en':
                    logger.info("Falling back to English for TTS")
                    tts = gTTS(text=text, lang='en', slow=False)
                else:
                    raise
            else:
                raise
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            tts.save(temp_file.name)
            temp_file_path = temp_file.name
        logger.info(f"Google TTS audio saved to: {temp_file_path}")
        success = cross_platform_play_audio(temp_file_path)
        delete_temp_file_later(temp_file_path)
        return success
    except Exception as e:
        logger.error(f"Google TTS failed: {e}")
        return False

def test_tts():
    test_cases = [
        ("Hello, how are you?", "en"),
        ("Bonjour, comment allez-vous?", "fr"),
        ("Bawo ni o se wa?", "yo"),
        ("Hola, ¿como estás?", "es")
    ]
    print(" Testing TTS Functions")
    print("=" * 40)
    for text, lang in test_cases:
        print(f"\n Testing: '{text}' in {lang}")
        success = text_to_speech(text, lang)
        print(f"Result: {' Success' if success else ' Failed'}")

if __name__ == "__main__":
    test_tts()