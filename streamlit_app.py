import streamlit as st

st.set_page_config(
    page_title="Speech-to-Speech Translator",
    page_icon="🗣️",
    layout="wide"
)
import tempfile
import time
from io import BytesIO
import base64
import os

# Handle imports with error checking
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    st.error("SpeechRecognition module not found. Please install it with: pip install SpeechRecognition")
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None

# Add audio recorder import
try:
    from audio_recorder_streamlit import audio_recorder
    AUDIO_RECORDER_AVAILABLE = True
except ImportError:
    st.warning("audio-recorder-streamlit not found. Install with: pip install audio-recorder-streamlit")
    AUDIO_RECORDER_AVAILABLE = False

try:
    from Speech_translator import translate_text_with_mbart, translate_text_with_spitch, translate_text_fallback
    TRANSLATOR_AVAILABLE = True
except ImportError:
    st.warning("Translation modules not found. Using placeholder functions.")
    TRANSLATOR_AVAILABLE = False
    
    # Placeholder functions
    def translate_text_with_mbart(text, source, target):
        return f"[MBART Translation] {text} (from {source} to {target})"
    
    def translate_text_with_spitch(text, source, target):
        return f"[Spitch Translation] {text} (from {source} to {target})"
    
    def translate_text_fallback(text, source, target):
        return f"[Fallback Translation] {text} (from {source} to {target})"

try:
    from text_to_speech import text_to_speech
    TTS_AVAILABLE = True
except ImportError:
    st.warning("Text-to-speech module not found. Using placeholder function.")
    TTS_AVAILABLE = False
    
    def text_to_speech(text, lang):
        st.info(f"Would play: '{text}' in language: {lang}")
        return True

try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except:
    PYGAME_AVAILABLE = False

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    st.warning("python-dotenv not found. Environment variables may not load properly.")

# Language configurations
AFRICAN_LANGUAGES = {
    "yo": "Yoruba",
    "ha": "Hausa", 
    "ig": "Igbo",
    "am": "Amharic",
    "sw": "Swahili",
    "zu": "Zulu",
    "xh": "Xhosa",
    "af": "Afrikaans",
    "en": "English"
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
    "ro_RO": "Romanian",
    "bg_BG": "Bulgarian",
    "fi_FI": "Finnish",
    "sv_SE": "Swedish",
    "no_NO": "Norwegian",
    "ru_RU": "Russian",
    "zh_CN": "Chinese (Simplified)",
    "zh_TW": "Chinese (Traditional)", 
    "ja_XX": "Japanese",
    "ko_KR": "Korean",
    "hi_IN": "Hindi",
    "bn_IN": "Bengali",
    "pa_IN": "Punjabi",
    "ur_PK": "Urdu",
    "th_TH": "Thai",
    "vi_VN": "Vietnamese",
    "id_ID": "Indonesian",
    "ms_MY": "Malay"
}

def initialize_session_state():
    """Initialize session state variables"""
    if SPEECH_RECOGNITION_AVAILABLE:
        if 'recognizer' not in st.session_state:
            st.session_state.recognizer = sr.Recognizer()
        if 'microphone' not in st.session_state:
            try:
                st.session_state.microphone = sr.Microphone()
            except:
                st.warning("Microphone not available")
                st.session_state.microphone = None
    if 'translation_history' not in st.session_state:
        st.session_state.translation_history = []
    if 'recorded_audio' not in st.session_state:
        st.session_state.recorded_audio = None
    if 'transcribed_text' not in st.session_state:
        st.session_state.transcribed_text = ""
    
    # NEW: Store current translation results
    if 'current_original' not in st.session_state:
        st.session_state.current_original = ""
    if 'current_translation' not in st.session_state:
        st.session_state.current_translation = ""
    if 'current_source_lang' not in st.session_state:
        st.session_state.current_source_lang = ""
    if 'current_target_lang' not in st.session_state:
        st.session_state.current_target_lang = ""
    if 'translation_completed' not in st.session_state:
        st.session_state.translation_completed = False

def setup_microphone():
    """Setup and test microphone"""
    if not SPEECH_RECOGNITION_AVAILABLE or st.session_state.microphone is None:
        return False
    try:
        with st.session_state.microphone as source:
            st.session_state.recognizer.adjust_for_ambient_noise(source, duration=1)
        return True
    except Exception as e:
        st.error(f"Microphone setup failed: {e}")
        return False

def process_recorded_audio(audio_bytes):
    """Process recorded audio bytes"""
    if not SPEECH_RECOGNITION_AVAILABLE:
        raise Exception("Speech recognition not available")
    
    try:
        # Save audio bytes to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name
        
        # Recognize speech from file
        with sr.AudioFile(tmp_file_path) as source:
            audio = st.session_state.recognizer.record(source)
        
        text = st.session_state.recognizer.recognize_google(audio, language='en-US')
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        return text.strip()
    except Exception as e:
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        raise Exception(f"Audio processing failed: {e}")

def capture_audio_from_upload(audio_file):
    """Process uploaded audio file"""
    if not SPEECH_RECOGNITION_AVAILABLE:
        raise Exception("Speech recognition not available")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(audio_file.read())
            tmp_file_path = tmp_file.name
        
        # Recognize speech from file
        with sr.AudioFile(tmp_file_path) as source:
            audio = st.session_state.recognizer.record(source)
        
        text = st.session_state.recognizer.recognize_google(audio, language='en-US')
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        return text.strip()
    except Exception as e:
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        raise Exception(f"Audio processing failed: {e}")

def translate_text_logic(text, source_lang, target_lang, source_type, target_type):
    """Handle translation logic"""
    try:
        st.info(f"Translating: '{text}' from {source_lang} ({source_type}) to {target_lang} ({target_type})")
        
        if source_type == "Others" and target_type == "Others":
            # Both are non-African languages - use MBART
            translation = translate_text_with_mbart(text, source_lang, target_lang)
            st.success("MBART translation completed")
            
        else:
            # At least one is African language - try Spitch first
            spitch_available = bool(os.getenv('SPITCH_API_KEY'))
            
            if spitch_available and TRANSLATOR_AVAILABLE:
                try:
                    translation = translate_text_with_spitch(text, source_lang, target_lang)
                    st.success("Spitch translation completed")
                except Exception as e:
                    st.warning(f"Spitch failed: {e}. Using fallback...")
                    translation = translate_text_fallback(text, source_lang, target_lang)
                    st.info("Fallback translation completed")
            else:
                st.info("Spitch API not available, using fallback...")
                translation = translate_text_fallback(text, source_lang, target_lang)
        
        return translation
        
    except Exception as e:
        st.error(f"Translation failed: {e}")
        # Final fallback
        try:
            translation = translate_text_fallback(text, source_lang, target_lang)
            st.warning("Using emergency fallback translation")
            return translation
        except Exception as fe:
            raise Exception(f"All translation methods failed: {e}, {fe}")

def convert_to_speech_streamlit(text, target_lang):
    """Convert text to speech for Streamlit with better error handling"""
    try:
        if not TTS_AVAILABLE:
            st.info(f"🔊 Text-to-speech not available. Would play: '{text}' in {target_lang}")
            return True
            
        success = text_to_speech(text, target_lang)
        if success:
            st.success("🔊 Audio generated and played successfully!")
        else:
            st.warning("🔊 Audio generation completed but may not have played correctly")
        return success
    except Exception as e:
        st.error(f"🔊 Speech conversion failed: {e}")
        return False

def display_translation_result(original, translated, source_lang, target_lang):
    """Display translation results in a formatted way"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Original Text")
        st.info(f"**Language:** {source_lang}")
        st.write(original)
    
    with col2:
        st.subheader("Translated Text")  
        st.success(f"**Language:** {target_lang}")
        st.write(translated)

def add_to_history(original, translated, source_lang, target_lang):
    """Add translation to history"""
    st.session_state.translation_history.append({
        'original': original,
        'translated': translated,
        'source_lang': source_lang,
        'target_lang': target_lang,
        'timestamp': time.strftime("%H:%M:%S")
    })

def main():
    st.set_page_config(
        page_title="Speech-to-Speech Translator",
        page_icon="🗣️",
        layout="wide"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.title("🗣️ Speech-to-Speech Translator")
    st.markdown("---")
    
    # Show module status
    st.subheader("System Status")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.write("**Speech Recognition:**")
        st.write("✅ Available" if SPEECH_RECOGNITION_AVAILABLE else "❌ Not Available")
    
    with col2:
        st.write("**Audio Recorder:**")
        st.write("✅ Available" if AUDIO_RECORDER_AVAILABLE else "❌ Not Available")
    
    with col3:
        st.write("**Translation:**")
        st.write("✅ Available" if TRANSLATOR_AVAILABLE else "⚠️ Placeholder")
    
    with col4:
        st.write("**Text-to-Speech:**")
        st.write("✅ Available" if TTS_AVAILABLE else "⚠️ Placeholder")
    
    with col5:
        st.write("**Audio Processing:**")
        st.write("✅ Available" if PYGAME_AVAILABLE else "❌ Not Available")
    
    st.markdown("---")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # API Status
        spitch_available = bool(os.getenv('SPITCH_API_KEY'))
        st.write("**API Status:**")
        st.write(f"Spitch API: {'Available' if spitch_available else '❌ Not Available'}")
        
        st.markdown("---")
        
        # Source Language Configuration
        st.subheader("Source Language")
        source_type = st.selectbox(
            "Source Language Type",
            ["African", "Others"],
            key="source_type"
        )
        
        if source_type == "African":
            source_lang = st.selectbox(
                "Select Source Language",
                list(AFRICAN_LANGUAGES.keys()),
                format_func=lambda x: f"{x} - {AFRICAN_LANGUAGES[x]}",
                key="source_lang"
            )
        else:
            source_lang = st.selectbox(
                "Select Source Language", 
                list(OTHER_LANGUAGES.keys()),
                format_func=lambda x: f"{x} - {OTHER_LANGUAGES[x]}",
                key="source_lang"
            )
        
        # Target Language Configuration
        st.subheader("Target Language")
        target_type = st.selectbox(
            "Target Language Type",
            ["African", "Others"],
            key="target_type"
        )
        
        if target_type == "African":
            target_lang = st.selectbox(
                "Select Target Language",
                list(AFRICAN_LANGUAGES.keys()),
                format_func=lambda x: f"{x} - {AFRICAN_LANGUAGES[x]}",
                key="target_lang"
            )
        else:
            target_lang = st.selectbox(
                "Select Target Language",
                list(OTHER_LANGUAGES.keys()),
                format_func=lambda x: f"{x} - {OTHER_LANGUAGES[x]}",
                key="target_lang"
            )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Translation Interface")
        
        # Configuration Summary
        with st.expander("Current Configuration", expanded=True):
            source_name = AFRICAN_LANGUAGES.get(source_lang) or OTHER_LANGUAGES.get(source_lang)
            target_name = AFRICAN_LANGUAGES.get(target_lang) or OTHER_LANGUAGES.get(target_lang)
            
            st.write(f"**Source:** {source_lang} ({source_name}) [{source_type}]")
            st.write(f"**Target:** {target_lang} ({target_name}) [{target_type}]")
        
        # Input methods
        st.subheader("Input Methods")
        input_method = st.radio(
            "Choose input method:",
            ["Text Input", "Audio Upload", "Live Recording"],
            horizontal=True
        )
        
        text_input = ""
        
        if input_method == "Text Input":
            text_input = st.text_area(
                "Enter text to translate:",
                placeholder="Type your text here...",
                height=100
            )
            
        elif input_method == "Audio Upload":
            uploaded_file = st.file_uploader(
                "Upload audio file",
                type=['wav', 'mp3', 'flac', 'm4a'],
                help="Upload an audio file to transcribe and translate"
            )
            
            if uploaded_file is not None:
                st.audio(uploaded_file)
                
                if st.button("🎵 Process Audio File"):
                    if SPEECH_RECOGNITION_AVAILABLE:
                        try:
                            with st.spinner("Processing audio file..."):
                                text_input = capture_audio_from_upload(uploaded_file)
                                st.success(f"Transcribed text: {text_input}")
                        except Exception as e:
                            st.error(f"Audio processing failed: {e}")
                    else:
                        st.error("Speech recognition not available")
                        
        elif input_method == "Live Recording":
            if AUDIO_RECORDER_AVAILABLE and SPEECH_RECOGNITION_AVAILABLE:
                st.info("🎤 Click the record button below to start recording")
                
                # Audio recorder component
                audio_bytes = audio_recorder(
                    text="Click to record",
                    recording_color="#e8b62c",
                    neutral_color="#6aa36f",
                    icon_name="microphone",
                    icon_size="6x",
                )
                
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/wav")
                    
                    if st.button("🎵 Process Recording"):
                        try:
                            with st.spinner("Processing recorded audio..."):
                                text_input = process_recorded_audio(audio_bytes)
                                st.session_state.transcribed_text = text_input
                                st.success(f"Transcribed text: {text_input}")
                        except Exception as e:
                            st.error(f"Audio processing failed: {e}")
                
                # Show previously transcribed text
                if st.session_state.transcribed_text:
                    text_input = st.session_state.transcribed_text
                    st.info(f"Current transcribed text: {text_input}")
                    
                    if st.button("Clear Transcribed Text"):
                        st.session_state.transcribed_text = ""
                        st.rerun()
                        
            else:
                st.error("Live recording requires both audio-recorder-streamlit and SpeechRecognition modules")
                st.info("Install with: pip install audio-recorder-streamlit SpeechRecognition")
                
                if not AUDIO_RECORDER_AVAILABLE:
                    st.warning("❌ Audio recorder component not available")
                if not SPEECH_RECOGNITION_AVAILABLE:
                    st.warning("❌ Speech recognition not available")
        
        # Translation button
        if st.button("Translate", type="primary", disabled=not text_input):
            if text_input:
                try:
                    with st.spinner("Translating..."):
                        translated_text = translate_text_logic(
                            text_input, source_lang, target_lang, 
                            source_type, target_type
                        )
                    
                    # Store results in session state
                    st.session_state.current_original = text_input
                    st.session_state.current_translation = translated_text
                    st.session_state.current_source_lang = f"{source_lang} ({source_name})"
                    st.session_state.current_target_lang = f"{target_lang} ({target_name})"
                    st.session_state.translation_completed = True
                    
                    # Add to history
                    add_to_history(text_input, translated_text, source_lang, target_lang)
                    
                    st.success("Translation completed!")
                    
                except Exception as e:
                    st.error(f"Translation failed: {e}")
                    st.session_state.translation_completed = False
            else:
                st.warning("Please enter text to translate")
        
        # Display translation results and audio controls if translation is completed
        if st.session_state.translation_completed and st.session_state.current_translation:
            st.markdown("---")
            
            # Display results
            display_translation_result(
                st.session_state.current_original, 
                st.session_state.current_translation, 
                st.session_state.current_source_lang,
                st.session_state.current_target_lang
            )
            
            # Text-to-Speech section
            st.subheader("Text-to-Speech")
            
            # Create columns for audio buttons
            col_tts1, col_tts2 = st.columns(2)
            
            with col_tts1:
                if st.button("Play Original", key="play_original_btn"):
                    with st.spinner("Generating speech for original text..."):
                        try:
                            # Extract language code from current source lang
                            source_code = st.session_state.current_source_lang.split(' (')[0] if '(' in st.session_state.current_source_lang else source_lang
                            success = convert_to_speech_streamlit(st.session_state.current_original, source_code)
                            if not success:
                                st.error("Failed to generate/play original audio")
                        except Exception as e:
                            st.error(f"Error playing original: {e}")
            
            with col_tts2:
                if st.button("Play Translation", key="play_translation_btn"):
                    with st.spinner("Generating speech for translation..."):
                        try:
                            # Extract language code from current target lang
                            target_code = st.session_state.current_target_lang.split(' (')[0] if '(' in st.session_state.current_target_lang else target_lang
                            success = convert_to_speech_streamlit(st.session_state.current_translation, target_code)
                            if not success:
                                st.error("Failed to generate/play translation audio")
                        except Exception as e:
                            st.error(f"Error playing translation: {e}")
            
            # Clear results button
            if st.button("Clear Translation Results"):
                st.session_state.translation_completed = False
                st.session_state.current_original = ""
                st.session_state.current_translation = ""
                st.session_state.current_source_lang = ""
                st.session_state.current_target_lang = ""
                st.rerun()
    
    with col2:
        st.header("Translation History")
        
        if st.session_state.translation_history:
            if st.button("Clear History"):
                st.session_state.translation_history = []
                st.rerun()
            
            st.markdown("---")
            
            for i, item in enumerate(reversed(st.session_state.translation_history)):
                with st.expander(f" {item['timestamp']} - {item['source_lang']} → {item['target_lang']}"):
                    st.write("**Original:**")
                    st.write(item['original'])
                    st.write("**Translation:**")
                    st.write(item['translated'])
        else:
            st.info("No translations yet")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            <p><strong> Speech-to-Speech Translator</strong> | Built with Streamlit</p>
            <p><small>Supports African languages through Spitch API and international languages through MBART</small></p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()