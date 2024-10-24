import common
import logger_config
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

def get(audio_path, fromText=None, endText=None, segments=None):
    path = f'audio/{common.generate_random_string()}.wav'

    audio = AudioFileClip(audio_path)
    start = 0 if fromText is None else None
    end = audio.duration if endText is None else None

    for i, segment in enumerate(segments):
        if fromText is not None:
            for text in fromText:
                if text.lower() in segment['text'].lower():
                    start = segments[i+1]['start']
                    break

        if endText is not None:
            for text in endText:
                if text.lower() in segment['text'].lower():
                    end = segments[i-1]['end']
                    break

        if start is not None and end is not None:
            break
    
    if start is None or end is None:
        return None

    audio = audio.subclip(start, end)
    audio.write_audiofile(path)
    logger_config.success(f'Trimmed end audio path:: {path} start:: {start}, end:: {end}')

    audio.close()
    

    return path

# if __name__ == "__main__":
	# get("background_music/Untitled notebook.wav", "Hello everyone", "Thank you for listening")
    # audio = AudioFileClip("audio/AaZcGQ.wav")
    # audio = audio.subclip(78.4, 82.5)
    # audio = AudioFileClip("background_music/Untitled notebook.wav")
    # audio = audio.subclip(0, 1.6)
    # audio.write_audiofile("background_music/next_puzzle.wav")
    