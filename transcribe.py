import whisper

# Load the Whisper model
model = whisper.load_model("base")  # You can choose different models: tiny, base, small, medium, large

# Transcribe audio
result = model.transcribe("your_audio_file.wav")

# Print the transcription
print("Transcription:", result['text'])