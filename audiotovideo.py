import whisper
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import os
import time
import random
import sqlite3
import logging

BACKGROUND_IMAGES_N = 7  # Total number of background images available

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    handlers=[
        logging.StreamHandler()  # Log to console
    ]
)

def transcribe_audio(audio_path):
    """Transcribe the given audio file using Whisper."""
    model = whisper.load_model("base")  # Choose the appropriate model size
    result = model.transcribe(audio_path)
    logging.info("Transcription completed.")
    return result['text']

def get_random_background_image(n):
    """Select a random background image from the available ones."""
    random_number = random.randint(1, n)
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the script
    return os.path.join(script_dir, "background_images", f"background-{random_number}.jpg")

def create_text_image(text, background_path, temp_filename, font_size=70, img_size=(1920, 1080), padding=50, extra_space=100, stroke_width=2, static_text="", bottom_static_text=""):
    """Create an image with bold text, a black border around each letter, and static text at the top and bottom."""
    # Open and resize the background image
    background = Image.open(background_path).resize(img_size)
    draw = ImageDraw.Draw(background)

    # Use a bold font (ensure the path points to a bold font, or adjust as needed)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Path to a bold font
    font = ImageFont.truetype(font_path, font_size)  # Load the bold font

    # Draw static text at the top
    if static_text:
        static_font_size = int(font_size * 0.8)  # Slightly smaller font for static text
        static_font = ImageFont.truetype(font_path, static_font_size)
        static_text_bbox = draw.textbbox((0, 0), static_text, font=static_font)
        static_text_width = static_text_bbox[2] - static_text_bbox[0]
        static_x = (img_size[0] - static_text_width) / 2
        static_y = padding
        # Draw the black border (stroke) for the static text at the top
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((static_x + dx, static_y + dy), static_text, font=static_font, fill="black")
        draw.text((static_x, static_y), static_text, font=static_font, fill="white")

    # Draw static text at the bottom
    if bottom_static_text:
        bottom_font_size = int(font_size * 0.8)
        bottom_font = ImageFont.truetype(font_path, bottom_font_size)
        bottom_text_bbox = draw.textbbox((0, 0), bottom_static_text, font=bottom_font)
        bottom_text_width = bottom_text_bbox[2] - bottom_text_bbox[0]
        bottom_x = (img_size[0] - bottom_text_width) / 2
        bottom_y = img_size[1] - bottom_text_bbox[3] - padding
        # Draw the black border for bottom static text
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((bottom_x + dx, bottom_y + dy), bottom_static_text, font=bottom_font, fill="black")
        draw.text((bottom_x, bottom_y), bottom_static_text, font=bottom_font, fill="white")

    # Process the main text
    wrapped_text = []
    lines = text.splitlines()

    for line in lines:
        words = line.split()
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            if line_width <= img_size[0] - (2 * padding) - (2 * extra_space):
                current_line = test_line
            else:
                wrapped_text.append(current_line)
                current_line = word
        wrapped_text.append(current_line)

    total_height = len(wrapped_text) * (font_size + 10)
    x = (img_size[0] - (img_size[0] - (2 * padding) - (2 * extra_space))) / 2
    y = (img_size[1] - total_height) / 2

    # Draw the black border for each letter of dynamic text
    for i, line in enumerate(wrapped_text):
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + extra_space + dx, y + i * (font_size + 10) + dy), line, font=font, fill="black")

    # Draw the white bold text on top of the black stroke
    for i, line in enumerate(wrapped_text):
        draw.text((x + extra_space, y + i * (font_size + 10)), line, font=font, fill="white")

    # Save the image
    background.save(temp_filename)
    logging.info(f"Text image created and saved to {temp_filename}.")
    return temp_filename

def resize_thumbnail(thumbnail_path):
    """Resize and compress the thumbnail image if it's larger than 2 MB."""
    max_file_size = 2 * 1024 * 1024  # 2 MB
    img = Image.open(thumbnail_path)

    # Check file size
    file_size = os.path.getsize(thumbnail_path)
    if file_size > max_file_size:
        logging.info(f"Thumbnail {thumbnail_path} is larger than 2 MB. Resizing...")

        # Resize the image (optional, adjust dimensions as needed)
        img.thumbnail((1280, 720))  # Resize to a max of 1280x720 while maintaining aspect ratio
        
        # Save with reduced quality
        quality = 95  # Start with high quality
        while file_size > max_file_size and quality > 20:  # Reduce until below 2 MB
            img.save(thumbnail_path, format='PNG', quality=quality)  # Use 'PNG' or 'JPEG'
            file_size = os.path.getsize(thumbnail_path)
            quality -= 5  # Reduce quality
            
        logging.info(f"Resized thumbnail to {file_size / 1024:.2f} KB with quality {quality}%.")
    else:
        logging.info(f"Thumbnail {thumbnail_path} is within size limits.")

    return thumbnail_path

def create_video_from_audio(audio_path):
    """Create a video from audio with transcribed text as subtitles."""
    logging.info(f"Transcribing audio: {audio_path}")
    transcript = transcribe_audio(audio_path)

    if not transcript:
        logging.error("No transcript generated. Cannot create video.")
        return

    # Extract the filename without extension
    filename = os.path.basename(audio_path)

    # Initialize static texts and output filename
    top_static_text = ""
    bottom_static_text = ""
    output_filename = filename.replace(".wav", ".mp4")  # Default output filename

    # Fetch thumbnailText from the database
    conn = sqlite3.connect('ContentData/entries.db')  # Connect to your database
    cursor = conn.cursor()
    cursor.execute("SELECT thumbnailText FROM entries WHERE audioPath = ?", (audio_path,))
    result = cursor.fetchone()
    thumbnailText = result[0] if result else ""  # Ensure there is a valid result
    conn.close()

    # Get a random background image for the video
    background_path = get_random_background_image(BACKGROUND_IMAGES_N)

    logging.info(f"Selected Background Image :: {background_path}")

    audio = AudioFileClip(audio_path)
    total_duration = audio.duration

    sentences = transcript.split('. ')
    total_words = sum(len(sentence.split()) for sentence in sentences)
    
    subtitles = []
    current_time = 0
    for sentence in sentences:
        word_count = len(sentence.split())
        sentence_duration = (word_count / total_words) * total_duration if total_words > 0 else 0
        
        end_time = current_time + sentence_duration
        subtitles.append((current_time, end_time, sentence))
        current_time = end_time

    txt_clips = []
    for start, end, sentence in subtitles:
        try:
            # Determine if we are in the last 4 seconds of the video
            is_near_end = (end >= total_duration - 4)

            # Create text image with the dynamic and static texts
            temp_image_path = create_text_image(
                sentence, 
                background_path,
                "temp_text_image.png",
                static_text=top_static_text,  
                bottom_static_text=bottom_static_text if is_near_end else ""
            )
            clip = ImageClip(temp_image_path).set_duration(end - start).set_start(start)
            txt_clips.append(clip)
            os.remove(temp_image_path)  # Clean up the temporary image
        except Exception as e:
            logging.error(f"Error creating text clip: {str(e)}")

    if not txt_clips:
        logging.error("No text clips could be created. Cannot generate video.")
        return

    subtitles_clip = CompositeVideoClip(txt_clips)
    video = CompositeVideoClip([subtitles_clip.set_audio(audio)])
    
    output_path = os.path.join("video", output_filename)  # Use the determined output filename
    logging.info(f"Rendering video: {output_path}")
    video.write_videofile(output_path, fps=24)
    logging.info(f"Video saved as {output_path}")

    # Generate thumbnail after the video is created
    thumbnail_filename = f"{os.path.splitext(output_filename)[0]}-thumbnail.png"  
    thumbnail_path = os.path.join("video", thumbnail_filename)

    try:
        create_text_image(
            thumbnailText, 
            background_path,
            thumbnail_path,
            static_text="",
            bottom_static_text=""
        )
    except Exception as e:
        logging.error(f"Error generating thumbnail: {str(e)}")

    resize_thumbnail(thumbnail_path)
    # Update the database to set videoGenerated to 1 and store video and thumbnail paths
    update_video_generated(audio_path, output_path, thumbnail_path)

    # Optionally delete the audio file after processing
    # os.remove(audio_path)
    # logging.info(f"Deleted audio file: {audio_path}")

def update_video_generated(audio_path, video_path, thumbnail_path):
    """Update the database to mark the video as generated and set the video and thumbnail paths."""
    conn = sqlite3.connect('ContentData/entries.db')  # Connect to your database
    cursor = conn.cursor()
    
    # Update the database with the new values
    cursor.execute("""
        UPDATE entries 
        SET generatedVideoPath = ?, generatedThumbnailPath = ?
        WHERE audioPath = ?
    """, (video_path, thumbnail_path, audio_path))
    
    conn.commit()
    conn.close()
    logging.info(f"Set videoPath to: {video_path} and thumbnailPath to: {thumbnail_path}")

def check_for_new_entries():
    """Check the database for new entries and process them."""
    conn = sqlite3.connect('ContentData/entries.db')  # Connect to your database
    cursor = conn.cursor()
    
    while True:
        cursor.execute("SELECT audioPath FROM entries WHERE generatedVideoPath IS NULL")
        new_entries = cursor.fetchall()
        
        for (audio_path,) in new_entries:
            if os.path.exists(audio_path):  # Ensure the audio file exists
                create_video_from_audio(audio_path)

        time.sleep(10)  # Sleep for a while before checking again

if __name__ == "__main__":
    check_for_new_entries()