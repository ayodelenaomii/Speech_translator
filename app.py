import speech_recognition as sr
from Speech_translator import translate_text_with_mbart, translate_text_with_spitch, translate_text_fallback
from text_to_speech import text_to_speech
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
        logging.FileHandler('speech_translator.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize speech recognition
recognizer = sr.Recognizer()
mic = sr.Microphone()

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

def display_languages(language_dict, title):
    """Display available languages in a formatted way"""
    print(f"\n {title}:")
    print("-" * 40)
    for code, name in language_dict.items():
        print(f"  {code:<8} : {name}")

def get_user_choice(prompt, valid_options):
    """Get user input with validation"""
    while True:
        choice = input(f"\n{prompt}: ").strip()
        if choice.lower() in [opt.lower() for opt in valid_options]:
            return choice
        print(f" Invalid choice. Please choose from: {', '.join(valid_options)}")

def get_language_code(language_type):
    """Get language code from user with validation"""
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
        raise ValueError(f"Invalid language type: {language_type}")

def setup_microphone():
    """Setup and test microphone"""
    try:
        print("\n Setting up microphone...")
        
        # List available microphones
        mic_list = sr.Microphone.list_microphone_names()
        print(f" Available microphones: {len(mic_list)}")
        for i, name in enumerate(mic_list[:3]):  # Show first 3
            print(f"  {i}: {name}")
        
        # Test microphone
        with mic as source:
            print(" Calibrating microphone for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=2)
            print(" Microphone setup complete")
            
        return True
        
    except Exception as e:
        logger.error(f"Microphone setup failed: {e}")
        print(f" Microphone setup failed: {e}")
        return False

def capture_and_recognize_speech(timeout=10, phrase_time_limit=5):
    """Capture audio and convert to text"""
    try:
        with mic as source:
            print(" Listening... Speak now!")
            audio = recognizer.listen(
                source, 
                timeout=timeout, 
                phrase_time_limit=phrase_time_limit
            )
            
        print(" Converting speech to text...")
        text = recognizer.recognize_google(audio, language='en-US')
        return text.strip()
        
    except sr.WaitTimeoutError:
        raise Exception("No speech detected within timeout period")
    except sr.UnknownValueError:
        raise Exception("Could not understand the audio")
    except sr.RequestError as e:
        raise Exception(f"Speech recognition service error: {e}")

def translate_text(text, source_lang, target_lang, source_type, target_type):
    """Translate text using appropriate method"""
    try:
        print(f" Translating: '{text}'")
        print(f" From {source_lang} ({source_type}) to {target_lang} ({target_type})")
        
        # Determine translation method
        if source_type.lower() == "others" and target_type.lower() == "others":
            # Both are non-African languages - use MBART
            translation = translate_text_with_mbart(text, source_lang, target_lang)
            print(f" MBART Translation: '{translation}'")
            
        else:
            # At least one is African language - try Spitch first
            spitch_available = bool(os.getenv('SPITCH_API_KEY'))
            
            if spitch_available:
                try:
                    translation = translate_text_with_spitch(text, source_lang, target_lang)
                    print(f" Spitch Translation: '{translation}'")
                except Exception as e:
                    logger.warning(f"Spitch failed: {e}")
                    print(f" Spitch failed, using fallback...")
                    translation = translate_text_fallback(text, source_lang, target_lang)
                    print(f" Fallback Translation: '{translation}'")
            else:
                print(" Spitch API not available, using fallback...")
                translation = translate_text_fallback(text, source_lang, target_lang)
                print(f" Fallback Translation: '{translation}'")
        
        return translation
        
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        # Final fallback
        try:
            translation = translate_text_fallback(text, source_lang, target_lang)
            print(f" Emergency Fallback: '{translation}'")
            return translation
        except Exception as fe:
            raise Exception(f"All translation methods failed: {e}, {fe}")

def convert_to_speech(text, target_lang):
    """Convert translated text to speech"""
    try:
        print(f" Converting to speech: '{text}' in {target_lang}")
        success = text_to_speech(text, target_lang)
        
        if success:
            print(" Speech conversion successful - Audio played")
        else:
            print(" Speech conversion failed")
            
        return success
        
    except Exception as e:
        logger.error(f"Speech conversion failed: {e}")
        print(f" Speech conversion error: {e}")
        return False

def main():
    """Main application function"""
    print(" Speech-to-Speech Translator")
    print("=" * 50)
    
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
        source_lang = get_language_code(source_type)
        
        # Get target language configuration  
        print("\n TARGET LANGUAGE CONFIGURATION")
        target_type = get_user_choice(
            "Choose target language type (African/Others)",
            ["African", "Others"] 
        )
        target_lang = get_language_code(target_type)
        
        # Display configuration summary
        print(f"\n TRANSLATION CONFIGURATION")
        print(f"   Source: {source_lang} ({AFRICAN_LANGUAGES.get(source_lang) or OTHER_LANGUAGES.get(source_lang)}) [{source_type}]")
        print(f"   Target: {target_lang} ({AFRICAN_LANGUAGES.get(target_lang) or OTHER_LANGUAGES.get(target_lang)}) [{target_type}]")
        
        # Main translation loop
        print(f"\n Starting speech translation session...")
        print(" Tips:")
        print("   - Speak clearly and at normal pace")
        print("   - Pause between sentences") 
        print("   - Press Ctrl+C to exit")
        
        MAX_ATTEMPTS = 5
        attempt = 0
        
        while attempt < MAX_ATTEMPTS:
            try:
                print(f"\n--- Attempt {attempt + 1}/{MAX_ATTEMPTS} ---")
                
                # Capture and recognize speech
                recognized_text = capture_and_recognize_speech()
                print(f" Recognized: '{recognized_text}'")
                
                # Translate text
                translation = translate_text(
                    recognized_text, source_lang, target_lang, 
                    source_type, target_type
                )
                
                # Display results
                print("=" * 60)
                print(f" ORIGINAL  : {recognized_text}")
                print(f" TRANSLATED: {translation}")
                print("=" * 60)
                
                # Convert translated text to speech
                speech_success = convert_to_speech(translation, target_lang)
                
                if not speech_success:
                    print(" Warning: Translation completed but speech output failed")
                    # Show the translated text anyway
                    print(f" You can read the translation: '{translation}'")
                
                # Ask user if they want to continue
                if attempt < MAX_ATTEMPTS - 1:
                    continue_choice = input("\n Continue? (y/n): ").strip().lower()
                    if continue_choice in ['n', 'no', 'exit', 'quit']:
                        break
                
            except KeyboardInterrupt:
                print("\n\n Session interrupted by user")
                break
            except Exception as e:
                print(f" Error in attempt {attempt + 1}: {e}")
                logger.error(f"Translation attempt {attempt + 1} failed: {e}")
            
            attempt += 1
        
        print(f"\n Translation session completed")
        print("Thank you for using Speech-to-Speech Translator!")
        
    except KeyboardInterrupt:
        print("\n\n Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f" Application error: {e}")
        print("Please check the logs for more details")

if __name__ == "__main__":
    main()