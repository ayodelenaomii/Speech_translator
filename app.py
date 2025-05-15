import speech_recognition as sr
from Speech_translator import translate_text_with_mbart, translate_text_with_spitch

recognizer = sr.Recognizer()
mic = sr.Microphone()

# Language options for Spitch (African languages)
African_languages = {
    "yo": "Yoruba",
    "ha": "Hausa",
    "ig": "Igbo",
    "am": "Amharic",
    "en": "English"
}

# Language options for MBART (Non-African languages)
Other_languages = {
    "en_XX": "English",
    "fr_XX": "French",
    "es_XX": "Spanish",
    "de_XX": "German",
    "it_XX": "Italian",
    "pt_XX": "Portuguese",
    "nl_XX": "Dutch",
    "pl_XX": "Polish",
    "ro_XX": "Romanian",
    "bg_XX": "Bulgarian",
    "fi_XX": "Finnish",
    "sv_XX": "Swedish",
    "no_XX": "Norwegian",
    "ru_RU": "Russian",
    "zh_CN": "Chinese (Simplified)",
    "zh_TW": "Chinese (Traditional)",
    "ja_XX": "Japanese",
    "ko_XX": "Korean",
    "hi_XX": "Hindi",
    "bn_XX": "Bengali",
    "pa_XX": "Punjabi",
    "ur_XX": "Urdu",
    "th_XX": "Thai",
    "vi_XX": "Vietnamese",
    "id_XX": "Indonesian",
    "ms_XX": "Malay"
}

# Ask the user which model they want to use
best_option_source = input("Choose the source model (African/Others): ").strip()
best_option_target = input("Choose the target model (African/Others): ").strip()

# Get source language code
if best_option_source == "African":
    print("Available languages for African Languages:")
    for code, language in African_languages.items():
        print(f"{code}: {language}")
    source_lang = input("Enter source language code (African): ").strip()

elif best_option_source == "Others":
    print("Available languages for Other Languages:")
    for code, language in Other_languages.items():
        print(f"{code}: {language}")
    source_lang = input("Enter source language code (Others): ").strip()

else:
    print("Invalid source choice.")
    exit()

# Get target language code
if best_option_target == "African":
    print("Available languages for African Languages:")
    for code, language in African_languages.items():
        print(f"{code}: {language}")
    target_lang = input("Enter target language code (African): ").strip()

elif best_option_target == "Others":
    print("Available languages for Other Languages:")
    for code, language in Other_languages.items():
        print(f"{code}: {language}")
    target_lang = input("Enter target language code (Others): ").strip()

else:
    print("Invalid target choice.")
    exit()




print(f"Source language: {source_lang} | Target language: {target_lang}")
print("Listening for speech...")

MAX_ATTEMPTS = 5
attempt = 0

while attempt < MAX_ATTEMPTS:
    with mic as source:
        try:
            print("Calibrating microphone for noise... Please be silent.")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening... Speak now!")
            audio = recognizer.listen(source, timeout=5)
            recognized_text = recognizer.recognize_google(audio)
            print(f"Recognized text: {recognized_text}")

            # Automatically select translator based on lang codes
            if best_option_source == "Others" and best_option_target == "Others":
                # Use MBART only if both are non-African
                translation = translate_text_with_mbart(recognized_text, source_lang, target_lang)
                print(f"Translated with MBART: {translation}")
            else:
                 # Use Spitch if either source or target is African
                translation = translate_text_with_spitch(recognized_text, source_lang, target_lang)
                print(f"Translated with Spitch: {translation}")

        except sr.UnknownValueError:
            print("Could not understand the audio.")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition; {e}")
        except Exception as err:
            print(f"Error: {err}")
        
        attempt += 1
        print(f"Attempt {attempt}/{MAX_ATTEMPTS}\n")

print("Finished listening after 5 attempts.")
