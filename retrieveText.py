from logger_config import setup_logging
import whisper

logging = setup_logging()

def parse(audio_path):
    try:
        logging.info(f"Starting audio transcription for: {audio_path}")

        # Load the Whisper model without weights_only parameter
        model = whisper.load_model("base")
        logging.info("Whisper model loaded successfully")

        result = model.transcribe(audio_path, word_timestamps=True)
        logging.info(f"Transcription completed successfully:")
        logging.info(f"{result['text']}")
        
        return result['text'], result['segments']
    except Exception as e:
        logging.error(f"Failed to transcribe audio {audio_path}: {str(e)}", exc_info=True)
        return "", []

# if __name__ == "__main__":
#     parse("audio/Untitled notebook.wav")