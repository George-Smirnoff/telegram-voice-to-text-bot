import pyttsx3
from pydub import AudioSegment
# import ffmpeg

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.save_to_file("Hello world", "hello_world.mp3")
engine.runAndWait()

# Convert to WAV using pydub
sound = AudioSegment.from_mp3("hello_world.mp3")
sound.export("hello_world.wav", format="wav")

print("WAV file created: hello_world.wav")
