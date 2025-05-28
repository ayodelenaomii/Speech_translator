import os
import logging
import requests
from urllib.parse import urlparse
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast
from dotenv import load_dotenv
import torch
import json

logger = logging.getLogger(__name__)

# Load environment variables first
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables to cache models (avoid reloading)
_mbart_model = None
_mbart_tokenizer = None

# Local model path - UPDATE THIS PATH TO YOUR LOCAL MODEL DIRECTORY
LOCAL_MBART_PATH = "C:\\Users\\USER\\Downloads\\Audio-Audio-translator\\Facebook model"

# Spitch API configuration
SPITCH_API_KEY = os.getenv("SPITCH_API_KEY", "sk_hQD6CYG6pOypyPIunknn7Bg4DcDRvAYvW71hjBLJ")
SPITCH_BASE_URL = "https://api.spi-tch.com/v1"

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

def test_connection(url, timeout=10):
    """Test if we can connect to the API endpoint"""
    try:
        parsed_url = urlparse(url)
        test_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        response = requests.get(test_url, timeout=timeout)
        logger.info(f"Connection test successful to {test_url}")
        return True
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to {test_url}")
        return False
    except requests.exceptions.Timeout:
        logger.error(f"Connection timeout to {test_url}")
        return False
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False

def translate_text_with_spitch_api(text, source_lang, target_lang):
    """
    Translate text using Spitch API with improved error handling and API format
    """
    if not text or not text.strip():
        raise ValueError("Input text is empty")
    
    logger.info(f"Translating with Spitch API: '{text}' from {source_lang} to {target_lang}")
    
    headers = {
        "Authorization": f"Bearer {SPITCH_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Updated payload format based on common API patterns
    payload = {
        "text": text.strip(),
        "source_language": source_lang,  # Try different parameter names
        "target_language": target_lang,
        "source": source_lang,  # Keep original format as backup
        "target": target_lang
    }
    
    try:
        # Convert payload to JSON string manually to avoid 'json' parameter issue
        json_payload = json.dumps(payload)
        
        response = requests.post(
            f"{SPITCH_BASE_URL}/translate",
            headers=headers,
            data=json_payload,  # Use 'data' instead of 'json'
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Try multiple possible response field names
            translated_text = (
                result.get('translated_text') or 
                result.get('translation') or 
                result.get('output') or 
                result.get('text') or
                result.get('result', '')
            )
            
            if translated_text:
                logger.info(f"Translation successful: '{translated_text}'")
                return translated_text.strip()
            else:
                logger.error(f"No translated text found in response: {result}")
                raise Exception("Translation failed: No translated text found")
        else:
            logger.error(f"API error {response.status_code}: {response.text}")
            raise Exception(f"Translation failed: HTTP {response.status_code} - {response.text}")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise Exception(f"Translation request failed: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        raise Exception(f"Translation failed: Invalid JSON response")
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise

def translate_text_with_spitch_sdk():
    """
    Alternative method using Spitch SDK if available
    Install with: pip install spitch
    """
    try:
        import spitch
        
        # Initialize client
        client = spitch.Client(api_key=SPITCH_API_KEY)
        
        def translate_with_sdk(text, source_lang, target_lang):
            logger.info(f"Using Spitch SDK: '{text}' from {source_lang} to {target_lang}")
            
            response = client.translate(
                text=text,
                source_language=source_lang,
                target_language=target_lang
            )
            
            return response.translated_text
        
        return translate_with_sdk
        
    except ImportError:
        logger.warning("Spitch SDK not installed. Use: pip install spitch")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Spitch SDK: {e}")
        return None

# Create an alias for backward compatibility
translate_text_with_spitch = translate_text_with_spitch_api

def test_spitch_connection():
    """Test Spitch API connection with multiple methods"""
    print(" Testing Spitch API connection")

    # Test 1: Direct API call
    try:
        translated = translate_text_with_spitch_api("Hello", "en", "yo")
        print(f" Direct API translation successful: {translated}")
        return True
    except Exception as e:
        print(f" Direct API test failed: {e}")
    
    # Test 2: Try SDK if available
    sdk_translate = translate_text_with_spitch_sdk()
    if sdk_translate:
        try:
            translated = sdk_translate("Hello", "en", "yo")
            print(f" SDK translation successful: {translated}")
            return True
        except Exception as e:
            print(f" SDK test failed: {e}")
    
    # Test 3: Alternative API endpoints
    alternative_endpoints = [
        f"{SPITCH_BASE_URL}/translation",
        f"{SPITCH_BASE_URL}/translate-text",
        "https://api.spitch.app/v1/translate"
    ]
    
    for endpoint in alternative_endpoints:
        try:
            headers = {
                "Authorization": f"Bearer {SPITCH_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = json.dumps({
                "text": "Hello",
                "source": "en",
                "target": "yo"
            })
            
            response = requests.post(endpoint, headers=headers, data=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print(f" Alternative endpoint {endpoint} works: {result}")
                return True
            else:
                print(f" Alternative endpoint {endpoint} failed: {response.status_code}")
                
        except Exception as e:
            print(f" Alternative endpoint {endpoint} error: {e}")
    
    return False

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
                result = translate_text_with_spitch_api(text, source, target)
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
    # First test the connection
    print(" Testing Spitch API Connection")
    print("-" * 30)
    connection_success = test_spitch_connection()
    
    print("\n" + "=" * 50)
    
    # Then test translations
    test_translations()
    
    # Print requests version for debugging
    print(f"\n Requests version: {requests.__version__}")