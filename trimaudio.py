import common
import logger_config
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

def get(audio_path, fromText=None, endText=None, segments=None):
    path = f'audio/{common.generate_random_string()}.wav'

    audio = AudioFileClip(audio_path)
    start = 0
    original_end = audio.duration
    end = audio.duration

    for i, segment in enumerate(segments):
        if fromText and fromText in segment['text']:
            start = segments[i+1]['start']
        if endText and endText in segment['text']:
            end = segments[i-1]['end']
            break
    
    audio = audio.subclip(start, end)
    audio.write_audiofile(path)
    logger_config.success(f'Trimmed end audio path:: {path}')

    audio.close()
    if start == 0 and end == original_end:
        return None

    return path

if __name__ == "__main__":
	get("audio/AaZcGQ.wav", "Hello everyone", "Thank you for listening")