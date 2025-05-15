import logging
from transformers import MBartForConditionalGeneration, MBart50Tokenizer
import requests
import os
from dotenv import load_dotenv
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load environment variables
logging.debug("Loading environment variables from .env file...")
load_dotenv()
SPITCH_API_KEY = os.getenv("SPITCH_API_KEY")
logging.debug(f"SPITCH_API_KEY loaded: {'Yes' if SPITCH_API_KEY else 'No'}")

# European Translation function using MBART
def translate_text_with_mbart(text, source_lang, target_lang):
    """
    Translates text using the MBART model.
    """
    logging.debug("Starting MBART translation...")
    logging.debug(f"Input text: {text}")
    logging.debug(f"Source language: {source_lang}")
    logging.debug(f"Target language: {target_lang}")

    try:
        model_path = r"C:\Users\USER\Downloads\Audio-Audio-translator\Facebook model"
        logging.debug(f"Loading tokenizer and model from {model_path}")
        tokenizer = MBart50Tokenizer.from_pretrained(model_path)
        model = MBartForConditionalGeneration.from_pretrained(model_path)

        logging.debug("Tokenizing input...")
        inputs = tokenizer(text, return_tensors='pt', src_lang=source_lang)
        logging.debug(f"Tokenized inputs: {inputs}")

        logging.debug("Generating translation...")
        translated_tokens = model.generate(**inputs, tgt_lang=target_lang)
        translated_text = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)

        logging.debug(f"Translated text: {translated_text}")
        return translated_text

    except Exception as e:
        logging.error(f"Error during MBART translation: {e}")
        return f"MBART Translation Error: {e}"

# Spitch API Translation function for African Languages
def translate_text_with_spitch(text, source_lang, target_lang):
    logging.debug("Starting Spitch API translation...")
    logging.debug(f"Input text: {text}")
    logging.debug(f"Source language: {source_lang}")
    logging.debug(f"Target language: {target_lang}")

    url = "https://api.spi-tch.com/v1/speech"
    payload = {
        "text": text,
        "source": source_lang,
        "target": target_lang
    }

    logging.debug(f"Payload for Spitch API: {payload}")
    headers = {"Authorization": f"Bearer {SPITCH_API_KEY}"} if SPITCH_API_KEY else {}

    try:
        logging.debug("Sending POST request to Spitch API...")
        response = requests.post(url, json=payload, headers=headers)
        logging.debug(f"response: {response}")
        logging.debug(f"Response Status Code: {response.status_code}")
        response.raise_for_status()

        result = response.json()
        logging.debug(f"Response JSON: {result}")

        translated_text = result.get("text", "")
        audio_url = result.get("audio_url", None)

        if not translated_text:
            logging.warning("Translation text not returned in response.")
            return "Translation text not returned."

        if audio_url:
            logging.debug("Audio URL returned with translation.")
            return f"Translated Text: {translated_text}\nAudio URL: {audio_url}"
        else:
            logging.debug("No audio URL returned.")
            return f"Translated Text: {translated_text} (No audio returned)"

    except requests.exceptions.RequestException as e:
        logging.error(f"Spitch API Error: {e}")
        return f"Spitch API Error: {e}"
