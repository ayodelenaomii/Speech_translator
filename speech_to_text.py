import speech_recognition as sr
from Speech_translator import translate_text_with_mbart, translate_text_with_spitch, translate_text_fallback
from text_to_speech import speak_text
import logging
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('speech_to_text.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize speech recognition
recognizer = sr.Recognizer()
mic = sr.Microphone()

# Language options for African languages (Spitch)
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

# Language options for MBART (Non-African languages)
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

# Speech recognition language mapping
SR_LANGUAGE_MAP = {
    "yo": "en-US",  # Fallback to English for African languages not supported by Google SR
    "ha": "en-US",
    "ig": "en-US", 
    "am": "en-US",
    "sw": "sw-KE",  # Swahili (Kenya)
    "zu": "en-US",
    "xh": "en-US",
    "af": "af-ZA",  # Afrikaans (South Africa)
    "en": "en-US",
    "en_XX": "en-US",
    "fr_XX": "fr-FR",
    "es_XX": "es-ES",
    "de_DE": "de-DE",
    "it_IT": "it-IT",
    "pt_XX": "pt-PT",
    "nl_XX": "nl-NL",
    "pl_PL": "pl-PL",
    "ro_RO": "ro-RO",
    "bg_BG": "bg-BG",
    "fi_FI": "fi-FI",
    "sv_SE": "sv-SE",
    "no_NO": "no-NO",
    "ru_RU": "ru-RU",
    "zh_CN": "zh-CN",
    "zh_TW": "zh-TW",
    "ja_XX": "ja-JP",
    "ko_KR": "ko-KR",
    "hi_IN": "hi-IN",
    "bn_IN": "bn-IN",
    "pa_IN": "pa-IN",
    "ur_PK": "ur-PK",
    "th_TH": "th-TH",
    "vi_VN": "vi-VN",
    "id_ID": "id-ID",
    "ms_MY": "ms-MY"
}

def display_languages(language_dict, title):
    """Display available languages in a formatted way"""
    print(f"\n {title}:")
    print("-" * 50)
    for code, name in language_dict.items():
        print(f"  {code:<8} : {name}")

def get_user_choice(prompt, valid_options):
    """Get user input with validation"""
    while True:
        choice = input(f"\n{prompt}: ").strip()
        if choice.lower() in [opt.lower() for opt in valid_options]:
            return choice
        print(f" Invalid choice. Please choose from: {', '.join(valid_options)}")

def get_language_choice(language_type):
    """Get language choice from user with validation"""
    if language_type.lower() == "african":
        display_languages(AFRICAN_LANGUAGES, "Available African Languages")
        while True:
            code = input(f"\n Enter {language_type} language code: ").strip().lower()
            if code in AFRICAN_LANGUAGES:
                return code
            print(f" Invalid code. Please choose from: {', '.join(AFRICAN_LANGUAGES.keys())}")
    
    elif language_type.lower() == "others":
        display_languages(OTHER_LANGUAGES, "Available Other Languages")
        while True:
            code = input(f"\n Enter {language_type} language code: ").strip()
            if code in OTHER_LANGUAGES:
                return code
            print(f" Invalid code. Please choose from: {', '.join(OTHER_LANGUAGES.keys())}")
    
    else:
        logger.error(f"Invalid language type: {language_type}")
        return None

def setup_microphone():
    """Setup and test microphone"""
    try:
        print("\n Setting up microphone...")
        
        # List available microphones
        mic_list = sr.Microphone.list_microphone_names()
        print(f" Found {len(mic_list)} microphone(s)")
        
        # Show first few microphones
        for i, name in enumerate(mic_list[:3]):
            print(f"  {i}: {name}")
        
        # Calibrate microphone
        with mic as source:
            print(" Calibrating microphone for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=2)
            print(" Microphone setup complete")
            
        return True
        
    except Exception as e:
        logger.error(f"Microphone setup failed: {e}")
        print(f" Microphone setup failed: {e}")
        return False

def capture_speech(source_lang, timeout=10, phrase_time_limit=5):
    """Capture and recognize speech"""
    try:
        # Get appropriate language for speech recognition
        sr_lang = SR_LANGUAGE_MAP.get(source_lang, "en-US")
        
        with mic as source:
            print(" Listening... Speak now!")
            
            # Listen for audio
            audio = recognizer.listen(
                source, 
                timeout=timeout, 
                phrase_time_limit=phrase_time_limit
            )
            
        print(" Converting speech to text...")
        
        # Try to recognize speech in the appropriate language
        try:
            recognized_text = recognizer.recognize_google(audio, language=sr_lang)
        except sr.UnknownValueError:
            # Fallback to English if recognition fails
            if sr_lang != "en-US":
                logger.info("Retrying with English language model...")
                recognized_text = recognizer.recognize_google(audio, language="en-US")
            else:
                raise
        
        return recognized_text.strip()
        
    except sr.WaitTimeoutError:
        raise Exception("No speech detected within timeout period")
    except sr.UnknownValueError:
        raise Exception("Could not understand the audio - please speak more clearly")
    except sr.RequestError as e:
        raise Exception(f"Speech recognition service error: {e}")
    except Exception as e:
        raise Exception(f"Speech capture failed: {e}")

def translate_speech(text, source_lang, target_lang, source_type, target_type):
    """Translate recognized speech text"""
    try:
        logger.info(f"Translating: '{text}' from {source_lang} ({source_type}) to {target_lang} ({target_type})")
        
        # Determine translation method based on language types
        if source_type.lower() == "others" and target_type.lower() == "others":
            # Both are non-African languages - use MBART
            translation = translate_text_with_mbart(text, source_lang, target_lang)
            logger.info(f"MBART translation: '{translation}'")
            
        else:
            # At least one is African language - try Spitch first
            spitch_available = bool(os.getenv('SPITCH_API_KEY'))
            
            if spitch_available:
                try:
                    translation = translate_text_with_spitch(text, source_lang, target_lang)
                    logger.info(f"Spitch translation: '{translation}'")
                except Exception as e:
                    logger.warning(f"Spitch translation failed: {e}")
                    logger.info("Falling back to fallback translator")
                    translation = translate_text_fallback(text, source_lang, target_lang)
            else:
                logger.info("Spitch API not available, using fallback")
                translation = translate_text_fallback(text, source_lang, target_lang)
        
        return translation
        
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        # Final fallback
        try:
            translation = translate_text_fallback(text, source_lang, target_lang)
            logger.info(f"Emergency fallback translation: '{translation}'")
            return translation
        except Exception as fe:
            raise Exception(f"All translation methods failed: {e}")

def main():
    """Main speech-to-speech translation function"""
    print(" Speech-to-Speech Translator")
    print("=" * 60)
    
    try:
        # Check API availability
        spitch_available = bool(os.getenv('SPITCH_API_KEY'))
        print(f" Spitch API: {'Available' if spitch_available else 'Not Available'}")
        
        # Setup microphone
        if not setup_microphone():
            print(" Cannot proceed without microphone")
            return
        
        # Get source language configuration
        print("\n SOURCE LANGUAGE CONFIGURATION")
        source_type = get_user_choice(
            "Choose source language type (African/Others)", 
            ["African", "Others"]
        )
        source_lang = get_language_choice(source_type)
        if not source_lang:
            print(" Invalid source language selection")
            return
        
        # Get target language configuration
        print("\n TARGET LANGUAGE CONFIGURATION")
        target_type = get_user_choice(
            "Choose target language type (African/Others)",
            ["African", "Others"]
        )
        target_lang = get_language_choice(target_type)
        if not target_lang:
            print(" Invalid target language selection")
            return
        
        # Display configuration summary
        print(f"\n CONFIGURATION SUMMARY")
        print("-" * 50)
        source_name = AFRICAN_LANGUAGES.get(source_lang) or OTHER_LANGUAGES.get(source_lang)
        target_name = AFRICAN_LANGUAGES.get(target_lang) or OTHER_LANGUAGES.get(target_lang)
        print(f"   Source: {source_lang} ({source_name}) [{source_type}]")
        print(f"   Target: {target_lang} ({target_name}) [{target_type}]")
        
        # Main translation loop
        print(f"\n Starting speech-to-speech translation session...")
        print(" Tips:")
        print("   - Speak clearly and at normal pace")
        print("   - Pause between sentences")
        print("   - Press Ctrl+C to exit anytime")
        
        MAX_ATTEMPTS = 5
        attempt = 0
        
        while attempt < MAX_ATTEMPTS:
            try:
                print(f"\n--- Attempt {attempt + 1}/{MAX_ATTEMPTS} ---")
                
                # Capture and recognize speech
                recognized_text = capture_speech(source_lang)
                print(f" Recognized: '{recognized_text}'")
                
                # Translate the recognized text
                translated_text = translate_speech(
                    recognized_text, source_lang, target_lang,
                    source_type, target_type
                )
                
                # Display translation results
                print("=" * 70)
                print(f" ORIGINAL  : {recognized_text}")
                print(f" TRANSLATED: {translated_text}")
                print("=" * 70)
                
                # Convert translated text to speech
                print(" Converting to speech...")
                speech_success = speak_text(
                    translated_text, source_lang, target_lang, 
                    source_type, target_type
                )
                
                if speech_success:
                    print("Speech output completed")
                else:
                    print(" Speech output failed, but translation was successful")
                
                # Ask if user wants to continue
                if attempt < MAX_ATTEMPTS - 1:
                    print("\n" + "="*70)
                    continue_choice = input("⏯  Continue with another translation? (y/n): ").strip().lower()
                    if continue_choice in ['n', 'no', 'exit', 'quit']:
                        break
                
            except KeyboardInterrupt:
                print("\n\n Session interrupted by user")
                break
            except Exception as e:
                print(f" Error in attempt {attempt + 1}: {e}")
                logger.error(f"Translation attempt {attempt + 1} failed: {e}")
                
                if attempt < MAX_ATTEMPTS - 1:
                    retry_choice = input("\n Try again? (y/n): ").strip().lower()
                    if retry_choice in ['n', 'no']:
                        break
            
            attempt += 1
        
        print(f"\n Speech-to-speech translation session completed")
        print("Thank you for using the Speech-to-Speech Translator! 👋")
        
    except KeyboardInterrupt:
        print("\n\n Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f" Application error: {e}")
        print("Please check the logs for more details")

def test_speech_recognition():
    """Test speech recognition functionality"""
    print(" Testing Speech Recognition")
    print("=" * 40)
    
    if not setup_microphone():
        print(" Microphone setup failed")
        return
    
    test_languages = ["en", "fr_XX", "yo"]
    
    for lang in test_languages:
        try:
            print(f"\n Testing speech recognition for {lang}")
            print("Speak something in a few seconds...")
            
            text = capture_speech(lang, timeout=5, phrase_time_limit=3)
            print(f" Recognized: '{text}'")
            
        except Exception as e:
            print(f" Failed: {e}")

if __name__ == "__main__":
    # Ask user what they want to do
    print(" Speech-to-Text Module")
    print("1. Run full speech-to-speech translation")
    print("2. Test speech recognition only")
    
    choice = input("\nEnter your choice (1/2): ").strip()
    
    if choice == "2":
        test_speech_recognition()
    else:
        main()