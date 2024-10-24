from pydub import AudioSegment
import common

def start(file_names, path=None):

    combined = AudioSegment.empty()

    # Loop through the file names and append them to the combined audio
    for file_name in file_names:
        audio = AudioSegment.from_wav(file_name)
        combined += audio

    # Export the combined audio to a new WAV file
    audio_path = path if path else f'audio/{common.generate_random_string()}.wav'
    combined.export(audio_path, format='wav')
    return audio_path