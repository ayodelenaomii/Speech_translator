# Speech-to-Speech Translator

A Flask-based real-time translator that takes speech audio, translates it using either MBART or Spitch API, and outputs translated speech audio.

## Features
- Real-time microphone input
- Supports MBART (open-source multilingual model)
- Optional Spitch API integration
- Audio output in target language

## Usage
```bash
pip install -r requirements.txt
python app.py


##Dependencies
Flask: Web framework for the application.
SpeechRecognition: For converting speech to text.
transformers: For using the MBART model to translate text.
gTTS: For converting translated text back to speech.


##Acknowledgement
MBART (Multilingual BART): The translation model used in this project is the MBART model from Hugging Face. It is a powerful pre-trained model for multilingual text translation, which supports over 50 languages.

SpeechRecognition Library: This project utilizes the SpeechRecognition library for speech-to-text conversion. It's a popular Python library that interfaces with various speech recognition services.

gTTS (Google Text-to-Speech): The text-to-speech conversion in this project is powered by gTTS, which uses Google's Text-to-Speech API.

Spitch API:This project can integrate with the Spitch API for advanced speech-to-speech translation mainly for African Languages 


##License
This project is open-source and available under the MIT License. See the LICENSE file for more details.

##Disclaimer
This project uses third-party libraries and APIs, and we are not responsible for any changes made by the external services.


