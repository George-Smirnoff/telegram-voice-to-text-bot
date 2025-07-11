
# Voice-to-Text Telegram Bot

This project is a Telegram bot that transcribes voice messages using Google Cloud Speech-to-Text v2 API (with Belarusian language support) and falls back to local speech recognition if needed.

---

## Features

- Transcribes Telegram voice messages to text  
- Supports Belarusian language via Google Cloud Speech-to-Text v2  
- Automatic recognizer creation and management  
- Fallback to local speech recognition (English) if Google API fails  
- Handles `.ogg` voice messages and converts audio as needed  

---

## Prerequisites

- Python 3.8+  
- Google Cloud project with Speech-to-Text API enabled and billing activated  
- Telegram bot token from [BotFather](https://core.telegram.org/bots#6-botfather)  
- Service account credentials (JSON) with Speech-to-Text permissions  

---

## Environment Setup

### 1. Install Dependencies

Install all required Python packages using the provided `requirements.txt`:

```

pip install -r requirements.txt

```

### 2. Create a `.env` File

Add your Telegram bot token to a file named `.env` in your project directory:

```

BOT_TOKEN=your-telegram-bot-token-here

```

### 3. Set Required Environment Variables

Export the following variables in your shell **before running the bot**:

```

export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account.json"

```

- `GOOGLE_CLOUD_PROJECT` is your Google Cloud project ID.  
- `GOOGLE_APPLICATION_CREDENTIALS` is the absolute path to your service account JSON key.  

---

## Google Cloud Setup Notes

- **Enable the Speech-to-Text API** for your project in the [Google Cloud Console](https://console.cloud.google.com/apis/library/speech.googleapis.com).  
- **Create a service account** with the **Speech-to-Text User** or **Editor** role and download its JSON key.  
- **Choose a region** that supports your model (e.g., `asia-southeast1` for `chirp_2`) and use it in your code.  

---

## Usage

1. **Start the bot**:

```

python main.py

```

2. **Send a voice message** to your bot in Telegram.  
3. **Receive the transcribed text** as a reply.  

---

## Code Highlights

- Tries Google Cloud Speech-to-Text v2 (Belarusian) first.  
- Falls back to local SpeechRecognition (English) on failure.  
- Automatically creates or reuses a recognizer resource in the specified region.  
- Converts OGG to FLAC for Google API and to WAV for local recognition.  

---

## Example `.env` File

```

BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ

```

---

```

> **Note:** You must have `ffmpeg` installed on your system (not via pip) for `pydub` to handle audio conversion.

---

## Troubleshooting

- **400 errors about model or location:** Ensure your recognizer and client use the same region (e.g., `asia-southeast1`).  
- **Permission errors:** Verify your service account roles and that the API is enabled.  
- **Audio conversion errors:** Ensure `ffmpeg` is installed and on your system path.  

---

## References

- [Google Cloud Speech-to-Text v2 Documentation](https://cloud.google.com/speech-to-text/v2/docs/)  
- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)  
- [pydub Documentation](https://pydub.com/)  

---

**Security Note:**  
Never commit your `.env` file or service account JSON key to version control. Store credentials securely.  

