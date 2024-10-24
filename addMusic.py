from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
from moviepy.audio.fx.all import audio_loop  # Import the audio looping function

# Load your video file
video = VideoFileClip("video/XsZOTR.mp4")
video_duration = video.duration

# Load your new audio file
new_audio = AudioFileClip("background_music/Whispering Shadows.mp3")
new_audio = new_audio.subclip(130, 140)
new_audio = audio_loop(new_audio, duration=video_duration)

# Get the original audio from the video
original_audio = video.audio

# Adjust the volume of each audio track if needed (0 to 1 range)
original_audio = original_audio.volumex(0.9)  # Reduce original audio to 50%
new_audio = new_audio.volumex(0.1)            # Reduce new audio to 50%

# Combine the original and new audio tracks
combined_audio = CompositeAudioClip([original_audio, new_audio])

# Set the combined audio to the video
video = video.set_audio(combined_audio)

# Define the output file name
output_file = "output_video_with_combined_audio.mp4"

# Write the result to a file
video.write_videofile(output_file)

# Close the clips to release resources
video.close()
original_audio.close()
new_audio.close()
