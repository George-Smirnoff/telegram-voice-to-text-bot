import telebot
import speech_recognition as sr
import os
from dotenv import load_dotenv
from io import BytesIO
from pydub import AudioSegment
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

# Replace with your bot token
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))

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
        
        # Convert OGG to WAV
        wav_buffer = convert_ogg_to_wav(downloaded_file)
        
        if wav_buffer:
            # Transcribe audio
            text = transcribe_audio(wav_buffer)
            
            # Send the transcription
            if text.startswith("Could not understand") or text.startswith("Error"):
                bot.edit_message_text(
                    f"❌ {text}",
                    chat_id=message.chat.id,
                    message_id=processing_msg.message_id
                )
            else:
                bot.edit_message_text(
                    f"📝 Transcription:\n\n{text}",
                    chat_id=message.chat.id,
                    message_id=processing_msg.message_id
                )
        else:
            bot.edit_message_text(
                "❌ Error converting audio format. Please try again.",
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

