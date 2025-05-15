from gtts import gTTS
import os
from Speech_translator import translate_text_with_mbart, translate_text_with_spitch
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Define the function to speak the text using TTS
def speak_text(text, tgt_lang):
    """
    This function will choose the appropriate TTS model (Spitch or MBART) based on the target language.
    """
    if tgt_lang in ['yor', 'hau', 'ibo', 'sw']:  # African Languages: Spitch model
        # Translate text using Spitch model for African languages
        translated_text = translate_text_with_spitch(text, tgt_lang)
        print(f"Translated text using Spitch: {translated_text}")
        # Use Spitch API for TTS 
        spitch_speak(translated_text, tgt_lang)
    else:
        # Translate text using MBART model for other languages
        translated_text = translate_text_with_mbart(text, tgt_lang)
        print(f"Translated text using MBART: {translated_text}")
        # Use Google TTS for other languages or any TTS of choice
        google_speak(translated_text, tgt_lang)

def spitch_speak(text, tgt_lang):
    """
    Use Spitch API (or SDK) for text-to-speech in African languages.
    """
    # Load Spitch API key from environment
    spitch_api_key = os.getenv("SPITCH_API_KEY")
    
    # Replace the placeholder function below with actual Spitch API call
    print(f"Using Spitch API for text-to-speech in {tgt_lang}")
    
    # Example: spitch_api_call(spitch_api_key, text, tgt_lang)
    print(f"Spitch speaking: {text}")
    
    # save the output using Google TTS 
    tts = gTTS(text=text, lang=tgt_lang, slow=False)
    tts.save("output_spitch.mp3")
    os.system("start output_spitch.mp3")

def google_speak(text, tgt_lang):
    """
    Use Google TTS for text-to-speech in other languages.
    """
    print(f"Using Google TTS for text-to-speech in {tgt_lang}")
    tts = gTTS(text=text, lang=tgt_lang, slow=False)
    tts.save("output_google.mp3")
    os.system("start output_google.mp3")
