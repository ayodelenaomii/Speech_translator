import speech_recognition as sr

def listen_to_speech(mic, recognizer, duration=2):
    """
    This function listens to the microphone input and returns the audio.
    It calibrates for ambient noise to improve speech recognition accuracy.
    
    Args:
        mic: The microphone object to listen from.
        recognizer: The recognizer instance from the speech_recognition library.
        duration: The number of seconds for calibrating the microphone for ambient noise.
    
    Returns:
        audio: The recorded audio.
    """
    try:
        with mic as source:
            print("Calibrating microphone for noise... Please be silent.")
            recognizer.adjust_for_ambient_noise(source, duration=duration)  
            print("Listening... Speak now!")
            audio = recognizer.listen(source)  
            return audio
    except sr.WaitTimeoutError:
        print("Timeout while waiting for speech input. Please try again.")
    except sr.RequestError as e:
        print(f"API request error: {e}")
    except sr.UnknownValueError:
        print("Sorry, I could not understand what you said.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return None
