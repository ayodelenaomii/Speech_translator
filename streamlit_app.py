import streamlit as st
import speech_recognition as sr
import tempfile
import os
import io
import base64
from gtts import gTTS
import pygame
import threading
import time
from Speech_translator import translate_text_with_mbart, translate_text_with_spitch, translate_text_fallback
from dotenv import load_dotenv
import logging



try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    st.error("speech_recognition module not found. Please install it using: pip install SpeechRecognition")
# Add Spitch TTS import
try:
    from spitch import Client
    SPITCH_TTS_AVAILABLE = True
except ImportError:
    SPITCH_TTS_AVAILABLE = False
    logging.warning("Spitch SDK not available for TTS")

# Load environment variables
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
    logger.warning("Pygame not available")

# Language configurations
AFRICAN_LANGUAGES = {
    "yo": "Yoruba",
    "ha": "Hausa", 
    "ig": "Igbo",
    "am": "Amharic",
    "en": "English",
    "sw": "Swahili",
    "zu": "Zulu",
    "xh": "Xhosa",
    "af": "Afrikaans"
}

OTHER_LANGUAGES = {
    "en_XX": "English",
    "fr_XX": "French",
    "es_XX": "Spanish", 
    "de_DE": "German",
    "it_IT": "Italian",
    "pt_XX": "Portuguese",
    "nl_XX": "Dutch",
    "pl_PL": "Polish",
    "ru_RU": "Russian",
    "zh_CN": "Chinese (Simplified)",
    "ja_XX": "Japanese",
    "ko_KR": "Korean",
    "hi_IN": "Hindi",
    "ar_AR": "Arabic"
}

GTTS_LANGUAGE_MAP = {
    'yo': 'yo', 'ha': 'ha', 'ig': 'ig', 'sw': 'sw', 'zu': 'zu', 'xh': 'xh', 
    'af': 'af', 'am': 'am', 'en': 'en', 'en_XX': 'en', 'fr_XX': 'fr', 
    'es_XX': 'es', 'de_DE': 'de', 'it_IT': 'it', 'pt_XX': 'pt', 
    'nl_XX': 'nl', 'pl_PL': 'pl', 'ru_RU': 'ru', 'zh_CN': 'zh', 
    'ja_XX': 'ja', 'ko_KR': 'ko', 'hi_IN': 'hi', 'ar_AR': 'ar'
}

# Spitch language mapping for TTS
SPITCH_TTS_LANGUAGE_MAP = {
    'yo': 'yo',  # Yoruba
    'ha': 'ha',  # Hausa
    'ig': 'ig',  # Igbo
    'am': 'am',  # Amharic
    'en': 'en',  # English
}

SR_LANGUAGE_MAP = {
    "yo": "en-US", "ha": "en-US", "ig": "en-US", "am": "en-US",
    "sw": "sw-KE", "zu": "en-US", "xh": "en-US", "af": "af-ZA",
    "en": "en-US", "en_XX": "en-US", "fr_XX": "fr-FR", "es_XX": "es-ES",
    "de_DE": "de-DE", "it_IT": "it-IT", "pt_XX": "pt-PT", "nl_XX": "nl-NL",
    "pl_PL": "pl-PL", "ru_RU": "ru-RU", "zh_CN": "zh-CN", "ja_XX": "ja-JP",
    "ko_KR": "ko-KR", "hi_IN": "hi-IN", "ar_AR": "ar-AR"
}

def get_audio_player_html(audio_bytes, autoplay=False):
    """Create HTML audio player"""
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f"""
    <audio controls {'autoplay' if autoplay else ''}>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        Your browser does not support the audio element.
    </audio>
    """
    return audio_html

def process_audio_file(audio_file, source_lang):
    """Process uploaded audio file and convert to text"""
    try:
        recognizer = sr.Recognizer()
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_file.read())
            tmp_file_path = tmp_file.name
        
        # Load audio file
        with sr.AudioFile(tmp_file_path) as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
        
        # Get appropriate language for speech recognition
        sr_lang = SR_LANGUAGE_MAP.get(source_lang, "en-US")
        
        # Recognize speech
        try:
            text = recognizer.recognize_google(audio, language=sr_lang)
        except sr.UnknownValueError:
            # Fallback to English if recognition fails
            if sr_lang != "en-US":
                text = recognizer.recognize_google(audio, language="en-US")
            else:
                raise
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        return text.strip()
        
    except Exception as e:
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        raise Exception(f"Speech recognition failed: {str(e)}")

def record_audio_from_mic(source_lang, duration=5):
    """Record audio from microphone"""
    try:
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
        
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
        
        with microphone as source:
            audio = recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
        
        # Get appropriate language for speech recognition
        sr_lang = SR_LANGUAGE_MAP.get(source_lang, "en-US")
        
        # Recognize speech
        try:
            text = recognizer.recognize_google(audio, language=sr_lang)
        except sr.UnknownValueError:
            # Fallback to English if recognition fails
            if sr_lang != "en-US":
                text = recognizer.recognize_google(audio, language="en-US")
            else:
                raise
        
        return text.strip()
        
    except sr.WaitTimeoutError:
        raise Exception("No speech detected within the time limit")
    except sr.UnknownValueError:
        raise Exception("Could not understand the audio")
    except Exception as e:
        raise Exception(f"Recording failed: {str(e)}")

def translate_text(text, source_lang, target_lang, source_type, target_type):
    """Translate text using appropriate method"""
    try:
        if source_type.lower() == "others" and target_type.lower() == "others":
            # Use MBART for non-African languages
            return translate_text_with_mbart(text, source_lang, target_lang)
        else:
            # Try Spitch first for African languages
            spitch_available = bool(os.getenv('SPITCH_API_KEY'))
            
            if spitch_available:
                try:
                    return translate_text_with_spitch(text, source_lang, target_lang)
                except Exception as e:
                    logger.warning(f"Spitch translation failed: {e}")
                    return translate_text_fallback(text, source_lang, target_lang)
            else:
                return translate_text_fallback(text, source_lang, target_lang)
                
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return translate_text_fallback(text, source_lang, target_lang)

def spitch_tts_bytes(text, target_lang):
    """Convert text to speech using Spitch API and return audio bytes"""
    try:
        if not SPITCH_TTS_AVAILABLE:
            raise Exception("Spitch SDK not available")
            
        spitch_api_key = os.getenv("SPITCH_API_KEY")
        if not spitch_api_key:
            raise Exception("Spitch API key not found")

        client = Client(api_key=spitch_api_key)
        spitch_lang = SPITCH_TTS_LANGUAGE_MAP.get(target_lang, target_lang)

        logger.info(f"Using Spitch TTS for {spitch_lang}: '{text}'")

        response = client.speech.generate(
            text=text,
            language=spitch_lang,
            voice='sade'
        )

        audio_bytes = response.read()
        
        if not audio_bytes:
            raise Exception("No audio content received from Spitch")
            
        logger.info("Spitch TTS successful")
        return audio_bytes
        
    except Exception as e:
        logger.error(f"Spitch TTS failed: {e}")
        raise

def google_tts_bytes(text, target_lang):
    """Convert text to speech using Google TTS and return audio bytes"""
    try:
        gtts_lang = GTTS_LANGUAGE_MAP.get(target_lang, target_lang.split('_')[0] if '_' in target_lang else target_lang)
        
        logger.info(f"Using Google TTS for {gtts_lang}: '{text}'")
        
        try:
            tts = gTTS(text=text, lang=gtts_lang, slow=False)
        except Exception as e:
            if "Language not supported" in str(e):
                if gtts_lang != 'en':
                    logger.info("Falling back to English for Google TTS")
                    tts = gTTS(text=text, lang='en', slow=False)
                else:
                    raise
            else:
                raise
        
        # Save to bytes
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        logger.info("Google TTS successful")
        return audio_buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Google TTS failed: {e}")
        raise

def text_to_speech_bytes(text, target_lang):
    """Convert text to speech and return audio bytes - with Spitch TTS support"""
    try:
        if not text or not text.strip():
            raise Exception("Empty text provided for TTS")
            
        # Check if target language is African and Spitch TTS is available
        african_langs = ['yo', 'ha', 'ig', 'sw', 'zu', 'xh', 'af', 'am']
        
        if target_lang in african_langs and SPITCH_TTS_AVAILABLE and os.getenv('SPITCH_API_KEY'):
            logger.info(f"Attempting Spitch TTS for African language: {target_lang}")
            try:
                return spitch_tts_bytes(text, target_lang)
            except Exception as e:
                logger.warning(f"Spitch TTS failed, falling back to Google TTS: {e}")
        
        # Fallback to Google TTS
        return google_tts_bytes(text, target_lang)
        
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise Exception(f"Text-to-speech conversion failed: {str(e)}")

def main():
    st.set_page_config(
        page_title="Speech-to-Speech Translator",
        page_icon="🎤",
        layout="wide"
    )
    
    st.title("🎤 Speech-to-Speech Translator")
    st.markdown("Real-time audio translation with support for African and international languages")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Status
        spitch_available = bool(os.getenv('SPITCH_API_KEY'))
        st.write("**API Status:**")
        st.write(f"🔹 Spitch Translation: {'✅ Available' if spitch_available else '❌ Not Available'}")
        st.write(f"🔹 Spitch TTS: {'✅ Available' if (spitch_available and SPITCH_TTS_AVAILABLE) else '❌ Not Available'}")
        st.write("🔹 MBART Model: ✅ Available")
        st.write("🔹 Google TTS: ✅ Available")
        
        st.divider()
        
        # Source Language
        st.subheader("🎯 Source Language")
        source_type = st.selectbox(
            "Language Type:",
            ["African", "Others"],
            key="source_type"
        )
        
        if source_type == "African":
            source_lang = st.selectbox(
                "Select Language:",
                list(AFRICAN_LANGUAGES.keys()),
                format_func=lambda x: f"{x} - {AFRICAN_LANGUAGES[x]}",
                key="source_lang"
            )
        else:
            source_lang = st.selectbox(
                "Select Language:",
                list(OTHER_LANGUAGES.keys()),
                format_func=lambda x: f"{x} - {OTHER_LANGUAGES[x]}",
                key="source_lang"
            )
        
        # Target Language
        st.subheader("🎯 Target Language")
        target_type = st.selectbox(
            "Language Type:",
            ["African", "Others"],
            key="target_type"
        )
        
        if target_type == "African":
            target_lang = st.selectbox(
                "Select Language:",
                list(AFRICAN_LANGUAGES.keys()),
                format_func=lambda x: f"{x} - {AFRICAN_LANGUAGES[x]}",
                key="target_lang"
            )
        else:
            target_lang = st.selectbox(
                "Select Language:",
                list(OTHER_LANGUAGES.keys()),
                format_func=lambda x: f"{x} - {OTHER_LANGUAGES[x]}",
                key="target_lang"
            )
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("🎤 Input Audio")
        
        # Input method selection
        input_method = st.radio(
            "Choose input method:",
            ["Upload Audio File", "Record from Microphone"],
            horizontal=True
        )
        
        recognized_text = ""
        
        if input_method == "Upload Audio File":
            uploaded_file = st.file_uploader(
                "Upload an audio file",
                type=['wav', 'mp3', 'ogg', 'flac'],
                help="Upload an audio file containing speech to translate"
            )
            
            if uploaded_file is not None:
                st.audio(uploaded_file)
                
                if st.button("🔄 Process Audio", type="primary"):
                    with st.spinner("Processing audio..."):
                        try:
                            recognized_text = process_audio_file(uploaded_file, source_lang)
                            st.success("Audio processed successfully!")
                        except Exception as e:
                            st.error(f"Error processing audio: {str(e)}")
                            recognized_text = ""
        
        else:  # Record from Microphone
            st.info("🎙️ Click the button below to start recording")
            
            # Recording duration
            duration = st.slider("Recording duration (seconds)", 3, 10, 5)
            
            if st.button("🔴 Start Recording", type="primary"):
                with st.spinner(f"Recording for {duration} seconds... Speak now!"):
                    try:
                        recognized_text = record_audio_from_mic(source_lang, duration)
                        st.success("Recording completed!")
                    except Exception as e:
                        st.error(f"Recording failed: {str(e)}")
                        recognized_text = ""
        
        # Display recognized text
        if recognized_text:
            st.subheader("📝 Recognized Text")
            st.text_area("Original Text:", recognized_text, height=100, disabled=True)
    
    with col2:
        st.header("🌐 Translation Output")
        
        if recognized_text:
            with st.spinner("Translating..."):
                try:
                    # Translate text
                    translated_text = translate_text(
                        recognized_text, source_lang, target_lang, source_type, target_type
                    )
                    
                    # Display translation
                    st.subheader("📋 Translated Text")
                    st.text_area("Translated Text:", translated_text, height=100, disabled=True)
                    
                    # Generate audio
                    with st.spinner("Converting to speech..."):
                        try:
                            audio_bytes = text_to_speech_bytes(translated_text, target_lang)
                            
                            st.subheader("🔊 Audio Output")
                            
                            # Show which TTS method was used
                            african_langs = ['yo', 'ha', 'ig', 'sw', 'zu', 'xh', 'af', 'am']
                            if target_lang in african_langs and SPITCH_TTS_AVAILABLE and os.getenv('SPITCH_API_KEY'):
                                st.info("🎯 Generated using Spitch TTS")
                            else:
                                st.info("🌐 Generated using Google TTS")
                            
                            st.audio(audio_bytes, format='audio/mp3')
                            
                            # Download button
                            st.download_button(
                                label="💾 Download Audio",
                                data=audio_bytes,
                                file_name=f"translated_audio_{target_lang}.mp3",
                                mime="audio/mp3"
                            )
                            
                        except Exception as e:
                            st.error(f"Text-to-speech failed: {str(e)}")
                    
                except Exception as e:
                    st.error(f"Translation failed: {str(e)}")
        else:
            st.info("👆 Please provide audio input to see translation results")
    
    # Footer
    st.divider()
    st.markdown(
        """
        ### 📋 Translation & TTS Methods
        - **African Language Translation**: Uses Spitch API (if available) or fallback translator
        - **Other Language Translation**: Uses MBART model for high-quality translations
        - **African Language TTS**: Uses Spitch TTS (if available) with Google TTS fallback
        - **Other Language TTS**: Uses Google TTS
        
        ### 🔧 Requirements
        - Microphone access for recording
        - Internet connection for translation APIs
        - Spitch API key (optional) for enhanced African language support
        """
    )

if __name__ == "__main__":
    main()