# services.py

import logging
from google.cloud import speech, translate_v2 as translate, texttospeech
from google.api_core.exceptions import GoogleAPICallError
from pydub import AudioSegment
import io

class GoogleCloudServices:
    def __init__(self, credentials):
        try:
            self.speech_client = speech.SpeechClient(credentials=credentials)
            self.translate_client = translate.Client(credentials=credentials)
            self.tts_client = texttospeech.TextToSpeechClient(credentials=credentials)
            logging.info("Google Cloud clients initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize Google Cloud clients: {e}")
            raise

    def transcribe_audio(self, audio_bytes, language_code):
        logging.info("Audio received. Attempting to convert to WAV format...")
        try:
            # Step 1: Convert audio from browser format
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            
            # Key Step for fixing 32-bit error: Force audio to 16-bit standard
            audio_segment = audio_segment.set_sample_width(2) # 2 bytes = 16 bits
            
            # Export the converted 16-bit audio as WAV
            wav_buffer = io.BytesIO()
            audio_segment.export(wav_buffer, format="wav")
            wav_bytes = wav_buffer.getvalue()

            sample_rate = audio_segment.frame_rate
            logging.info(f"Audio successfully converted to 16-bit WAV. Detected sample rate: {sample_rate} Hz.")
            
        except Exception as e:
            logging.error(f"Failed to convert audio: {e}. Ensure FFMPEG is installed in the container.")
            return None

        logging.info(f"Sending WAV audio for transcription in language: {language_code}")
        try:
            # Step 2: Send the WAV audio to Google
            audio_config = speech.RecognitionAudio(content=wav_bytes)
            recognition_config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate,
                language_code=language_code,
            )
            response = self.speech_client.recognize(config=recognition_config, audio=audio_config)
            
            if not response.results:
                logging.warning("API could not detect any speech in the converted audio.")
                return None
                
            transcript = response.results[0].alternatives[0].transcript
            logging.info(f"Original Text: {transcript}")
            return transcript
        except GoogleAPICallError as e:
            logging.error(f"API error during transcription: {e}")
            return None

    def translate_text(self, text, target_language):
        if not text: return None
        logging.info(f"Translating text to '{target_language}'...")
        try:
            result = self.translate_client.translate(text, target_language=target_language)
            translated_text = result["translatedText"]
            logging.info(f"Translated Text: {translated_text}")
            return translated_text
        except GoogleAPICallError as e:
            logging.error(f"API error during translation: {e}")
            return None

    def text_to_speech(self, text, voice_code):
        if not text: return None
        logging.info(f"Synthesizing speech with voice code: {voice_code}")
        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice_params = texttospeech.VoiceSelectionParams(
                language_code=voice_code[:5], name=voice_code
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                sample_rate_hertz=24000
            )
            response = self.tts_client.synthesize_speech(
                input=synthesis_input, voice=voice_params, audio_config=audio_config
            )
            return response.audio_content
        except GoogleAPICallError as e:
            logging.error(f"API error during text-to-speech: {e}")
            return None