import telebot
import speech_recognition as sr
import os
from dotenv import load_dotenv
from io import BytesIO
from pydub import AudioSegment
import logging
# ADDED
from google.cloud import speech_v2 as speech
from google.api_core.client_options import ClientOptions


# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

# Replace with your bot token
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
REGION = "asia-southeast1"  # Use a region that supports Belarusian language
api_endpoint = f"{REGION}-speech.googleapis.com"

client_options = ClientOptions(api_endpoint=api_endpoint)

# Initialize Google Cloud Speech client
speech_client = speech.SpeechClient(client_options=client_options)  # ADDED
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')  # ADDED

def convert_ogg_to_wav(ogg_data):
    """Convert OGG audio data to WAV format"""
    try:
        # Load OGG data using pydub
        audio = AudioSegment.from_ogg(BytesIO(ogg_data))
        
        # Convert to WAV format in memory
        wav_buffer = BytesIO()
        audio.export(wav_buffer, format="wav")
        wav_buffer.seek(0)
        
        return wav_buffer
    except Exception as e:
        logging.error(f"Error converting OGG to WAV: {e}")
        return None

def convert_ogg_to_flac(ogg_data):  # ADDED
    """Convert OGG audio data to FLAC format for Google STT v2"""
    try:
        # Load OGG data using pydub
        audio = AudioSegment.from_ogg(BytesIO(ogg_data))
        
        # Convert to FLAC format in memory
        flac_buffer = BytesIO()
        audio.export(flac_buffer, format="flac")
        flac_buffer.seek(0)
        
        return flac_buffer
    except Exception as e:
        logging.error(f"Error converting OGG to FLAC: {e}")
        return None

def get_or_create_recognizer(recognizer_id="belarusian-recognizer"):  # ADDED
    """Get existing recognizer or create new one for Belarusian language"""
    try:
        recognizer_name = f"projects/{PROJECT_ID}/locations/asia-southeast1/recognizers/{recognizer_id}"
        
        # Try to get existing recognizer
        try:
            recognizer = speech_client.get_recognizer(name=recognizer_name)
            logging.info(f"Using existing recognizer: {recognizer_name}")
            return recognizer_name
        except Exception:
            # Recognizer doesn't exist, create new one
            logging.info(f"Creating new recognizer: {recognizer_name}")
            
            request = speech.CreateRecognizerRequest(
                parent=f"projects/{PROJECT_ID}/locations/asia-southeast1",  # Use a specific region with Belarusian language support
                recognizer_id=recognizer_id,
                recognizer=speech.Recognizer(
                    default_recognition_config=speech.RecognitionConfig(
                        language_codes=["be-BY"],  # Belarusian language code
                        model="chirp_2",
                        # TODO: Fix the error: 
                        # ERROR:root:Error transcribing Belarusian: 400 The RecognitionConfig proto is invalid:
                        #   * decoding_config: required oneof field 'decoding_config' must have one initialized field
                        auto_decoding_config=speech.RecognitionConfig.AutoDecodingConfig(),
                        features=speech.RecognitionFeatures(
                            enable_automatic_punctuation=True
                        )
                    )
                )
            )
            
            operation = speech_client.create_recognizer(request=request)
            recognizer = operation.result(timeout=30)
            logging.info(f"Created recognizer: {recognizer.name}")
            return recognizer.name
            
    except Exception as e:
        logging.error(f"Error with recognizer: {e}")
        return None

def transcribe_audio(wav_buffer):
    """Transcribe audio using speech recognition"""
    try:
        # Initialize speech recognizer
        recognizer = sr.Recognizer()
        
        # Process audio
        with sr.AudioFile(wav_buffer) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # Record the audio
            audio_data = recognizer.record(source)
            
            # Recognize speech using Google Speech Recognition
            text = recognizer.recognize_google(audio_data, language="en-US")
            return text
            
    except sr.UnknownValueError:
        return "Could not understand the audio"
    except sr.RequestError as e:
        return f"Error with speech recognition service: {e}"
    except Exception as e:
        return f"Transcription error: {e}"

def transcribe_belarusian(flac_buffer):  # ADDED
    """Transcribe Belarusian audio using Google Cloud Speech-to-Text v2"""
    try:
        recognizer_name = get_or_create_recognizer()
        if not recognizer_name:
            return None
            
        audio_bytes = flac_buffer.read()
        
        request = speech.RecognizeRequest(
            recognizer=recognizer_name,
            content=audio_bytes
        )
        
        response = speech_client.recognize(request=request)
        
        # Extract transcriptions
        transcripts = []
        for result in response.results:
            if result.alternatives:
                transcripts.append(result.alternatives[0].transcript)
        
        return " ".join(transcripts) if transcripts else None
        
    except Exception as e:
        logging.error(f"Error transcribing Belarusian: {e}")
        return None

@bot.message_handler(commands=['start'])
def start_command(message):
    """Handle the /start command"""
    welcome_text = """
🎤 Welcome to the Voice-to-Text Bot!

Send me a voice message and I'll transcribe it to text for you.

Features:
• High accuracy speech recognition
• Fast processing
• Support for various audio qualities

Just send a voice message to get started!
    """
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=['voice'])
def handle_voice_message(message):
    """Handle incoming voice messages"""
    try:
        # Send processing message
        processing_msg = bot.reply_to(message, "🎧 Processing your voice message...")
        
        # Get file info from Telegram
        file_info = bot.get_file(message.voice.file_id)
        
        # Download the voice file using bot.download_file
        downloaded_file = bot.download_file(file_info.file_path)
        
        # First try Belarusian transcription via Google STT v2
        flac_buffer = convert_ogg_to_flac(downloaded_file)
        text = None
        
        if flac_buffer:
            text = transcribe_belarusian(flac_buffer)
        
        # Fallback to original recognizer if Google STT v2 fails
        if not text:
            wav_buffer = convert_ogg_to_wav(downloaded_file)
            if wav_buffer:
                text = transcribe_audio(wav_buffer)
        
        # Send the transcription
        if text and not text.startswith("Could not understand") and not text.startswith("Error"):
            bot.edit_message_text(
                f"📝 Transcription:\n\n{text}",
                chat_id=message.chat.id,
                message_id=processing_msg.message_id
            )
        else:
            bot.edit_message_text(
                f"❌ {text or 'Could not transcribe the audio'}",
                chat_id=message.chat.id,
                message_id=processing_msg.message_id
            )
            
    except Exception as e:
        logging.error(f"Error processing voice message: {e}")
        bot.reply_to(message, f"❌ An error occurred: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    """Handle non-voice messages"""
    bot.reply_to(message, "Please send me a voice message to transcribe! 🎤")

if __name__ == "__main__":
    print("Voice-to-Text Bot is starting...")
    bot.infinity_polling()
