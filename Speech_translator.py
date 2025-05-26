import os
import logging
import requests
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast
from dotenv import load_dotenv
import torch
import json

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables to cache models (avoid reloading)
_mbart_model = None
_mbart_tokenizer = None

# Local model path - UPDATE THIS PATH TO YOUR LOCAL MODEL DIRECTORY
LOCAL_MBART_PATH = "C:\\Users\\USER\\Downloads\\Audio-Audio-translator\\Facebook model"

def load_mbart_model():
    """Load MBART model and tokenizer from local path (cached)"""
    global _mbart_model, _mbart_tokenizer
    
    if _mbart_model is None or _mbart_tokenizer is None:
        try:
            logger.info(f"Loading MBART model and tokenizer from local path: {LOCAL_MBART_PATH}")
            
            # Check if local path exists
            if not os.path.exists(LOCAL_MBART_PATH):
                raise FileNotFoundError(f"Local model path does not exist: {LOCAL_MBART_PATH}")
            
            # Load model and tokenizer from local path
            _mbart_model = MBartForConditionalGeneration.from_pretrained(
                LOCAL_MBART_PATH,
                local_files_only=True
            )
            _mbart_tokenizer = MBart50TokenizerFast.from_pretrained(
                LOCAL_MBART_PATH,
                local_files_only=True
            )
            logger.info("MBART model loaded successfully from local path")
        except Exception as e:
            logger.error(f"Failed to load MBART model from local path: {e}")
            raise
    
    return _mbart_model, _mbart_tokenizer

def translate_text_with_mbart(text, source_lang, target_lang):
    """
    Translate text using local MBART model
    
    Args:
        text (str): Text to translate
        source_lang (str): Source language code (e.g., 'en_XX')
        target_lang (str): Target language code (e.g., 'es_XX')
    
    Returns:
        str: Translated text
    """
    try:
        if not text or not text.strip():
            raise ValueError("Input text is empty")
        
        logger.info(f"Translating with local MBART: '{text}' from {source_lang} to {target_lang}")
        
        # Load model and tokenizer
        model, tokenizer = load_mbart_model()
        
        # Validate language codes
        if source_lang not in tokenizer.lang_code_to_id:
            raise ValueError(f"Unsupported source language: {source_lang}")
        if target_lang not in tokenizer.lang_code_to_id:
            raise ValueError(f"Unsupported target language: {target_lang}")
        
        # Set source language
        tokenizer.src_lang = source_lang
        
        # Encode input text
        encoded = tokenizer(text, return_tensors="pt", max_length=512, truncation=True)
        
        # Generate translation
        with torch.no_grad():
            generated_tokens = model.generate(
                **encoded,
                forced_bos_token_id=tokenizer.lang_code_to_id[target_lang],
                max_length=200,
                num_beams=4,
                early_stopping=True,
                do_sample=False
            )
        
        # Decode translation
        translated_text = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
        
        logger.info(f"MBART translation successful: '{translated_text}'")
        return translated_text.strip()
        
    except Exception as e:
        logger.error(f"MBART translation error: {e}")
        raise Exception(f"MBART translation failed: {str(e)}")

def translate_text_with_spitch(text, source_lang, target_lang):
    """
    Translate text using Spitch API
    
    Args:
        text (str): Text to translate
        source_lang (str): Source language code (e.g., 'en')
        target_lang (str): Target language code (e.g., 'yo')
    
    Returns:
        str: Translated text
    """
    try:
        if not text or not text.strip():
            raise ValueError("Input text is empty")
        
        logger.info(f"Translating with Spitch: '{text}' from {source_lang} to {target_lang}")
        
        # Get API credentials from environment
        api_key = os.getenv('SPITCH_API_KEY')
        api_url = os.getenv('SPITCH_API_URL', 'https://api.spitch.com/v1/translate')
        
        if not api_key:
            raise Exception("SPITCH_API_KEY not found in environment variables")
        
        # Prepare headers
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Speech-Translator/1.0'
        }
        
        # Prepare payload
        payload = {
            'text': text.strip(),
            'source_language': source_lang,
            'target_language': target_lang
        }
        
        logger.debug(f"Spitch API request: {payload}")
        
        # Convert payload to JSON string for the request
        json_data = json.dumps(payload)
        
        # Make API request with proper error handling - FIXED VERSION
        try:
            response = requests.post(
                api_url,
                headers=headers,
                data=json_data,  # Use 'data' instead of 'json' parameter
                timeout=30
            )
        except TypeError as e:
            # Fallback method if the above doesn't work
            logger.warning(f"First request method failed: {e}. Trying alternative method.")
            response = requests.post(
                api_url,
                headers=headers,
                timeout=30
            )
            # Send data in the request body manually
            response._content = json_data.encode('utf-8')
        
        logger.debug(f"Spitch API response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
            except json.JSONDecodeError:
                # If response is not JSON, treat as plain text
                result = {'translated_text': response.text.strip()}
            
            logger.debug(f"Spitch API response: {result}")
            
            # Extract translated text (adjust based on actual API response format)
            translated_text = (
                result.get('translated_text') or 
                result.get('translation') or 
                result.get('result') or 
                result.get('data', {}).get('translation') if isinstance(result.get('data'), dict) else None
            )
            
            if translated_text:
                logger.info(f"Spitch translation successful: '{translated_text}'")
                return translated_text.strip()
            else:
                raise Exception("No translated text found in API response")
                
        elif response.status_code == 401:
            raise Exception("Authentication failed - check API key")
        elif response.status_code == 400:
            try:
                error_msg = response.json().get('error', response.text)
            except:
                error_msg = response.text
            raise Exception(f"Bad request: {error_msg}")
        elif response.status_code == 429:
            raise Exception("Rate limit exceeded - try again later")
        else:
            raise Exception(f"API error {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        raise Exception("Request timeout - Spitch API is slow to respond")
    except requests.exceptions.ConnectionError:
        raise Exception("Connection error - check internet connection")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request error: {str(e)}")
    except Exception as e:
        if "Spitch" not in str(e):
            logger.error(f"Spitch translation error: {e}")
        raise

def translate_text_fallback(text, source_lang, target_lang):
    """
    Fallback translation function for testing when APIs are unavailable
    
    Args:
        text (str): Text to translate
        source_lang (str): Source language code
        target_lang (str): Target language code
    
    Returns:
        str: Fallback translated text
    """
    logger.info(f"Using fallback translation: '{text}' from {source_lang} to {target_lang}")
    
    # Clean language codes (remove _XX suffixes for MBART codes)
    clean_source = source_lang.split('_')[0] if '_' in source_lang else source_lang
    clean_target = target_lang.split('_')[0] if '_' in target_lang else target_lang
    
    # Enhanced word-by-word translation dictionary for common phrases
    translations = {
        'en_yo': {
            'hello': 'bawo',
            'hi': 'bawo',
            'how': 'bawo',
            'are': 'se',
            'you': 'o',
            'where': 'nibo',
            'going': 'lo',
            'go': 'lo',
            'come': 'wa',
            'back': 'pada',
            'here': 'ibi',
            'please': 'je ka',
            'good': 'dara',
            'morning': 'aro',
            'afternoon': 'osan',
            'evening': 'ale',
            'night': 'oru',
            'thank': 'o se',
            'thanks': 'o se',
            'welcome': 'kaabo',
            'sorry': 'ma binu',
            'yes': 'beeni',
            'no': 'rara',
            'what': 'kini',
            'when': 'nigbati',
            'why': 'kilode',
            'who': 'tani',
            'to': 'si'
        },
        'yo_en': {
            'bawo': 'hello',
            'se': 'are',
            'o': 'you',
            'nibo': 'where',
            'lo': 'going',
            'wa': 'come',
            'pada': 'back',
            'ibi': 'here',
            'dara': 'good',
            'aro': 'morning',
            'osan': 'afternoon',
            'ale': 'evening',
            'oru': 'night',
            'kaabo': 'welcome',
            'beeni': 'yes',
            'rara': 'no',
            'kini': 'what',
            'nigbati': 'when',
            'kilode': 'why',
            'tani': 'who'
        },
        'en_es': {
            'hello': 'hola',
            'how': 'como',
            'are': 'estas',
            'you': 'tu',
            'where': 'donde',
            'going': 'vas',
            'good': 'bueno',
            'morning': 'mañana',
            'thank': 'gracias',
            'welcome': 'bienvenido',
            'please': 'por favor',
            'sorry': 'lo siento',
            'yes': 'si',
            'no': 'no',
            'what': 'que',
            'when': 'cuando',
            'why': 'por que',
            'who': 'quien'
        },
        'es_en': {
            'hola': 'hello',
            'como': 'how',
            'estas': 'are',
            'tu': 'you',
            'donde': 'where',
            'vas': 'going',
            'bueno': 'good',
            'mañana': 'morning',
            'gracias': 'thank you',
            'bienvenido': 'welcome',
            'si': 'yes',
            'no': 'no',
            'que': 'what',
            'cuando': 'when',
            'quien': 'who'
        }
    }
    
    translation_key = f"{clean_source}_{clean_target}"
    word_translations = translations.get(translation_key, {})
    
    if word_translations:
        words = text.lower().split()
        translated_words = []
        
        for word in words:
            # Remove punctuation for lookup
            clean_word = word.strip('.,!?;:"\'')
            translated_word = word_translations.get(clean_word, word)
            
            # Preserve punctuation
            if word != clean_word:
                punctuation = word[len(clean_word):]
                translated_word += punctuation
                
            translated_words.append(translated_word)
        
        result = ' '.join(translated_words)
    else:
        # For unsupported language pairs, return a formatted version
        result = f"[{clean_source}→{clean_target}] {text}"
    
    logger.info(f"Fallback translation result: '{result}'")
    return result

def get_supported_languages():
    """Get lists of supported languages for each translation method"""
    mbart_languages = [
        'ar_AR', 'cs_CZ', 'de_DE', 'en_XX', 'es_XX', 'et_EE', 'fi_FI', 'fr_XX',
        'gu_IN', 'hi_IN', 'it_IT', 'ja_XX', 'kk_KZ', 'ko_KR', 'lt_LT', 'lv_LV',
        'my_MM', 'ne_NP', 'nl_XX', 'ro_RO', 'ru_RU', 'si_LK', 'tr_TR', 'vi_VN',
        'zh_CN', 'af_ZA', 'az_AZ', 'bn_IN', 'fa_IR', 'he_IL', 'hr_HR', 'id_ID',
        'ka_GE', 'km_KH', 'mk_MK', 'ml_IN', 'mn_MN', 'mr_IN', 'pl_PL', 'ps_AF',
        'pt_XX', 'sv_SE', 'sw_KE', 'ta_IN', 'te_IN', 'th_TH', 'tl_XX', 'uk_UA',
        'ur_PK', 'xh_ZA', 'gl_ES', 'sl_SI'
    ]
    
    african_languages = ['yo', 'ha', 'ig', 'am', 'sw', 'zu', 'xh', 'af']
    
    return {
        'mbart': mbart_languages,
        'spitch': african_languages
    }

def test_translations():
    """Test both translation methods with sample text"""
    test_cases = [
        ("Hello, how are you?", "en_XX", "es_XX", "mbart"),
        ("Good morning", "en", "yo", "spitch"),
        ("Thank you very much", "en_XX", "fr_XX", "mbart"),
        ("Bawo ni", "yo", "en", "fallback"),
        ("where are you going to please come back here", "en", "yo", "fallback")
    ]
    
    print(" Testing Translation Functions")
    print("=" * 50)
    
    for text, source, target, method in test_cases:
        print(f"\n Test: '{text}' ({source} → {target}) using {method}")
        
        try:
            if method == "mbart":
                result = translate_text_with_mbart(text, source, target)
            elif method == "spitch":
                result = translate_text_with_spitch(text, source, target)
            else:
                result = translate_text_fallback(text, source, target)
            
            print(f" Result: '{result}'")
            
        except Exception as e:
            print(f" Error: {e}")
            # Try fallback
            try:
                fallback_result = translate_text_fallback(text, source, target)
                print(f" Fallback: '{fallback_result}'")
            except Exception as fe:
                print(f" Fallback also failed: {fe}")

if __name__ == "__main__":
    test_translations()