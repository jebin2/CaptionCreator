from moviepy.editor import VideoFileClip
import common
import logger_config

def get(videoPath):
    # Extract the audio
    video = VideoFileClip(videoPath)
    audio = video.audio

    path = f'audio/{common.generate_random_string()}.wav'
    audio.write_audiofile(path)

    logger_config.success(f'Retrieved audio path:: {path}')

    audio.close()
    video.close()

    return path