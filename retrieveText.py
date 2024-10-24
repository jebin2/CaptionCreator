import logger_config
import whisper

def parse(audio_path):
    try:
        logger_config.info(f"Starting audio transcription for: {audio_path}")

        # Load the Whisper model without weights_only parameter
        model = whisper.load_model("base")
        logger_config.info("Whisper model loaded successfully")

        result = model.transcribe(audio_path, word_timestamps=True)
        logger_config.info(f"Transcription completed successfully:")
        logger_config.info(f"{result['text']}")
        
        return result['text'], result['segments']
    except Exception as e:
        logger_config.error(f"Failed to transcribe audio {audio_path}: {str(e)}")
        return "", []

# if __name__ == "__main__":
#     parse("audio/Untitled notebook.wav")