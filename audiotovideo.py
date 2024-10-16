import whisper
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import os
import time
import random
import sqlite3
import logging

BACKGROUND_IMAGES_N = 6  # Total number of background images available
SHOW_ANSWER = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

def transcribe_audio(audio_path):
    """Transcribe the given audio file using Whisper."""
    try:
        logging.info(f"Starting audio transcription for: {audio_path}")
        model = whisper.load_model("base")
        logging.info("Whisper model loaded successfully")
        result = model.transcribe(audio_path)
        logging.info(f"Transcription completed successfully for: {audio_path}")
        return result['text']
    except Exception as e:
        logging.error(f"Failed to transcribe audio {audio_path}: {str(e)}", exc_info=True)
        return ""

def get_random_background_image(n):
    """Select a random background image from the available ones."""
    try:
        random_number = random.randint(1, n)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        background_path = os.path.join(script_dir, "background_images", f"background-{random_number}.jpg")
        logging.info(f"Selected random background image: {background_path}")
        return background_path
    except Exception as e:
        logging.error(f"Error selecting background image: {str(e)}", exc_info=True)
        return ""

def create_text_image(text, background_path, temp_filename, font_size=70, img_size=(1920, 1080), padding=50, extra_space=100, stroke_width=2, static_text="", bottom_static_text=""):
    """Create an image with bold text, a black border around each letter, and static text at the top and bottom."""
    logging.info(f"Creating text image with background: {background_path}")
    try:
        background = Image.open(background_path).resize(img_size)
        draw = ImageDraw.Draw(background)
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font = ImageFont.truetype(font_path, font_size)

        # Function to wrap text into lines based on the width
        def wrap_text(text, font, max_width):
            wrapped_lines = []
            lines = text.splitlines()
            
            for line in lines:
                words = line.split()
                current_line = ""
                for word in words:
                    test_line = f"{current_line} {word}".strip()
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    line_width = bbox[2] - bbox[0]
                    if line_width <= max_width:
                        current_line = test_line
                    else:
                        wrapped_lines.append(current_line)
                        current_line = word
                wrapped_lines.append(current_line)
            return wrapped_lines

        # Draw static text at the top
        if static_text:
            static_font_size = int(font_size * 0.8)  # Slightly smaller font for static text
            static_font = ImageFont.truetype(font_path, static_font_size)
            max_static_width = img_size[0] - (2 * padding) - (2 * extra_space)

            # Wrap the static text
            wrapped_static_text = wrap_text(static_text, static_font, max_static_width)
            
            # Calculate y-position for the static text
            total_static_height = len(wrapped_static_text) * (static_font_size + 10)
            static_y = padding
            
            # Draw the black border (stroke) for the static text at the top
            for i, line in enumerate(wrapped_static_text):
                text_width = draw.textbbox((0, 0), line, font=static_font)[2] - draw.textbbox((0, 0), line, font=static_font)[0]
                static_x = (img_size[0] - text_width) / 2  # Center the text horizontally
                
                for dx in range(-stroke_width, stroke_width + 1):
                    for dy in range(-stroke_width, stroke_width + 1):
                        if dx != 0 or dy != 0:
                            draw.text((static_x + dx, static_y + i * (static_font_size + 10) + dy), line, font=static_font, fill="black")
            
            # Draw the white static text on top of the black stroke
            for i, line in enumerate(wrapped_static_text):
                text_width = draw.textbbox((0, 0), line, font=static_font)[2] - draw.textbbox((0, 0), line, font=static_font)[0]
                static_x = (img_size[0] - text_width) / 2  # Center the text horizontally
                draw.text((static_x, static_y + i * (static_font_size + 10)), line, font=static_font, fill="white")

        # Draw static text at the bottom
        if bottom_static_text:
            bottom_font_size = int(font_size * 0.8)
            bottom_font = ImageFont.truetype(font_path, bottom_font_size)
            max_bottom_width = img_size[0] - (2 * padding) - (2 * extra_space)

            # Wrap the bottom static text with the prefix
            wrapped_bottom_text = wrap_text("Answer is :: " + bottom_static_text, bottom_font, max_bottom_width)

            # Calculate y-position for the bottom static text
            total_bottom_height = len(wrapped_bottom_text) * (bottom_font_size + 10)
            bottom_y = img_size[1] - total_bottom_height - padding

            # Draw the black border for bottom static text
            for i, line in enumerate(wrapped_bottom_text):
                text_width = draw.textbbox((0, 0), line, font=bottom_font)[2] - draw.textbbox((0, 0), line, font=bottom_font)[0]
                bottom_x = (img_size[0] - text_width) / 2  # Center the text horizontally
                
                for dx in range(-stroke_width, stroke_width + 1):
                    for dy in range(-stroke_width, stroke_width + 1):
                        if dx != 0 or dy != 0:
                            draw.text((bottom_x + dx, bottom_y + i * (bottom_font_size + 10) + dy), line, font=bottom_font, fill="black")

            # Draw the white bottom static text on top of the black stroke
            for i, line in enumerate(wrapped_bottom_text):
                text_width = draw.textbbox((0, 0), line, font=bottom_font)[2] - draw.textbbox((0, 0), line, font=bottom_font)[0]
                bottom_x = (img_size[0] - text_width) / 2  # Center the text horizontally
                draw.text((bottom_x, bottom_y + i * (bottom_font_size + 10)), line, font=bottom_font, fill="white")

        # Process the main text
        max_text_width = img_size[0] - (2 * padding) - (2 * extra_space)
        wrapped_text = wrap_text(text, font, max_text_width)

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
        logging.info(f"Text image created and saved to {temp_filename}")
        return temp_filename
    except Exception as e:
        logging.error(f"Error creating text image: {str(e)}", exc_info=True)
        return ""

def resize_thumbnail(thumbnail_path):
    """Resize and compress the thumbnail image if it's larger than 2 MB."""
    logging.info(f"Checking thumbnail size: {thumbnail_path}")
    max_file_size = 2 * 1024 * 1024  # 2 MB
    try:
        img = Image.open(thumbnail_path)
        file_size = os.path.getsize(thumbnail_path)
        if file_size > max_file_size:
            logging.info(f"Resizing thumbnail {thumbnail_path}")
            img.thumbnail((1280, 720))
            quality = 95
            while file_size > max_file_size:
                img.save(thumbnail_path, format='PNG', quality=quality)
                file_size = os.path.getsize(thumbnail_path)
                quality -= 5
            logging.info(f"Resized thumbnail to {file_size / 1024:.2f} KB with quality {quality}%")
        else:
            logging.info(f"Thumbnail {thumbnail_path} is within size limits")
        return thumbnail_path
    except Exception as e:
        logging.error(f"Error resizing thumbnail: {str(e)}", exc_info=True)
        return thumbnail_path

def show_answer(end, total_duration, sentence, bottom_static_text):
    global SHOW_ANSWER
    is_sentence_contains_bottom_text = bottom_static_text.lower() in sentence.lower()
    SHOW_ANSWER = SHOW_ANSWER or is_sentence_contains_bottom_text
    logging.info(f"Show answer status: {SHOW_ANSWER}")
    return SHOW_ANSWER

def create_video_from_audio(audio_path):
    """Create a video from audio with transcribed text as subtitles."""
    logging.info(f"Starting video creation for audio: {audio_path}")
    global SHOW_ANSWER
    SHOW_ANSWER = False
    
    transcript = transcribe_audio(audio_path)
    if not transcript:
        logging.error("No transcript generated. Cannot create video.")
        return

    filename = os.path.basename(audio_path)
    output_filename = filename.replace(".wav", ".mp4")

    conn = sqlite3.connect('ContentData/entries.db')
    cursor = conn.cursor()
    cursor.execute("SELECT thumbnailText, description, answer FROM entries WHERE audioPath = ?", (audio_path,))
    result = cursor.fetchone()
    thumbnailText, top_static_text, bottom_static_text = result if result else ("", "", "")
    conn.close()

    logging.info(f"Retrieved metadata: thumbnailText='{thumbnailText}', top_static_text='{top_static_text}', bottom_static_text='{bottom_static_text}'")

    background_path = get_random_background_image(BACKGROUND_IMAGES_N)
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration

    logging.info(f"Processing transcript for video creation")
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
            is_near_end = show_answer(end, total_duration, sentence, bottom_static_text)
            temp_image_path = create_text_image(
                sentence, 
                background_path,
                "temp_text_image.png",
                static_text=top_static_text,  
                bottom_static_text=bottom_static_text if is_near_end else ""
            )
            clip = ImageClip(temp_image_path).set_duration(end - start).set_start(start)
            txt_clips.append(clip)
            os.remove(temp_image_path)
            logging.info(f"Created text clip for time range: {start:.2f} - {end:.2f}")
        except Exception as e:
            logging.error(f"Error creating text clip: {str(e)}", exc_info=True)

    if not txt_clips:
        logging.error("No text clips could be created. Cannot generate video.")
        return

    subtitles_clip = CompositeVideoClip(txt_clips)
    video = CompositeVideoClip([subtitles_clip.set_audio(audio)])
    
    output_path = os.path.join("video", output_filename)
    logging.info(f"Rendering video: {output_path}")
    video.write_videofile(output_path, fps=24)
    logging.info(f"Video saved as {output_path}")

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
        logging.info(f"Thumbnail created: {thumbnail_path}")
    except Exception as e:
        logging.error(f"Error generating thumbnail: {str(e)}", exc_info=True)

    resize_thumbnail(thumbnail_path)
    update_video_generated(audio_path, output_path, thumbnail_path)

def update_video_generated(audio_path, video_path, thumbnail_path):
    """Update the database to mark the video as generated and set the video and thumbnail paths."""
    logging.info(f"Updating database for audio: {audio_path}")
    try:
        conn = sqlite3.connect('ContentData/entries.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE entries 
            SET generatedVideoPath = ?, generatedThumbnailPath = ?
            WHERE audioPath = ?
        """, (video_path, thumbnail_path, audio_path))
        conn.commit()
        conn.close()
        logging.info(f"Database updated: videoPath={video_path}, thumbnailPath={thumbnail_path}")
    except Exception as e:
        logging.error(f"Error updating database: {str(e)}", exc_info=True)

def check_for_new_entries():
    """Check the database for new entries and process them."""
    logging.info("Starting to check for new entries")
    conn = sqlite3.connect('ContentData/entries.db')
    cursor = conn.cursor()
    
    while True:
        cursor.execute("SELECT audioPath FROM entries WHERE generatedVideoPath IS NULL")
        new_entries = cursor.fetchall()
        
        for (audio_path,) in new_entries:
            if os.path.exists(audio_path):
                logging.info(f"Processing new entry: {audio_path}")
                create_video_from_audio(audio_path)
            else:
                logging.warning(f"Audio file not found: {audio_path}")

        wait_with_logs(10)  # Sleep for a while before checking again

def wait_with_logs(seconds):
    """Wait for a specified number of seconds, logging the countdown."""
    try:
        logging.info(f"Waiting for {seconds} seconds.")
        for i in range(seconds, 0, -1):
            logging.info(f"Wait time remaining: {i} seconds.")
            time.sleep(1)
        logging.info("Wait period finished.")
    except Exception as e:
        logging.error(f"Error during wait: {str(e)}")

if __name__ == "__main__":
    logging.info("Starting video generation script")
    check_for_new_entries()