import whisper

# Load Whisper model
model = whisper.load_model("base")

# Transcribe with timestamps
result= model.transcribe("audio/audio9.wav", word_timestamps=True)

print(f"Text: {result}")
# Get the transcription with timestamps
for segment in result['segments']:
    print(f"Text: {segment['text']}, Start: {segment['start']}, End: {segment['end']} All {segment}")