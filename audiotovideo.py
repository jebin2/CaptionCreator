import whisper
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import os
import time
import random
import sqlite3
import riddle_parser
import create_riddles
from logger_config import setup_logging

logging = setup_logging()

BACKGROUND_IMAGES_N = 11  # Total number of background images available
BACKGROUND_LABEL = 'background'
BACKGROUND_PATH = 'background_images'
BACKGROUND_EXT = 'jpg'
FONT_N = 2
FONT_LABEL = 'font'
FONT_PATH = 'Fonts'
FONT_EXT = 'ttf'
SHOW_ANSWER = False

def transcribe_audio(audio_path):
    """Transcribe the given audio file using Whisper."""
    try:
        logging.info(f"Starting audio transcription for: {audio_path}")
        model = whisper.load_model("base")
        logging.info("Whisper model loaded successfully")
        result = model.transcribe(audio_path, word_timestamps=True)
        logging.info(f"Transcription completed successfully for: {audio_path}")
        
        return result['text'], result['segments']
    except Exception as e:
        logging.error(f"Failed to transcribe audio {audio_path}: {str(e)}", exc_info=True)
        return "", []

def get_random_file_name(path, label, n, ext):
    """Select a random background image from the available ones."""
    try:
        random_number = random.randint(1, n)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path_with_file_name = os.path.join(script_dir, path, f"{label}_{random_number}.{ext}")
        logging.info(f"Selected random path_with_file_name: {path_with_file_name}")
        return path_with_file_name
    except Exception as e:
        logging.error(f"Error selecting background image: {str(e)}", exc_info=True)
        return ""

def create_text_image(text, background_path, temp_filename, font_path, font_size=70, img_size=(1920, 1080), padding=50, extra_space=100, stroke_width=2, static_text="", bottom_static_text=""):
    """Create an image with bold text, a black border around each letter, and static text at the top and bottom."""
    logging.info(f"Creating text image with background: {background_path}")
    try:
        background = Image.open(background_path).resize(img_size)
        draw = ImageDraw.Draw(background)
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
                wait_with_logs(10)
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

def find_segment_time(sentence, segments, type, checkAfterSegment):
    sentence = sentence.strip().lower()  # Normalize the sentence for better matching
    sentence = sentence.replace(".", "")
    sendNextWordStartTime = False
    combineSegementText = None
    for i, segment in enumerate(segments):
        if checkAfterSegment is None or segment["id"] >= checkAfterSegment["id"]:
            segment_text = segment['text'].strip().lower()
            segment_text = segment_text.replace(".", "")
            if combineSegementText is None:
                combineSegementText = segment_text
            else:
                combineSegementText += f" {segment_text}"
            if sendNextWordStartTime:
                return segment
            if sentence in combineSegementText:
                if type == "start":
                    return segment
                else:
                    if i == len(segments) - 1:
                        return segment
                    sendNextWordStartTime = True

    return None


def create_video_from_audio(audio_path):
    """Create a video from audio with transcribed text as subtitles."""
    logging.info(f"Starting video creation for audio: {audio_path}")
    
    transcript, segments = transcribe_audio(audio_path)
    if not transcript:
        logging.error("No transcript generated. Cannot create video.")
        return
    
    # Retrieve metadata from the database
    conn = sqlite3.connect('ContentData/entries.db')
    cursor = conn.cursor()
    cursor.execute("SELECT thumbnailText, description, answer FROM entries WHERE audioPath = ?", (audio_path,))
    result = cursor.fetchone()
    thumbnailText, top_static_text, bottom_static_text = result if result else ("", "", "")
    conn.close()

    # Process transcript with riddle_parser (which should add --#start#--, --#answer#--, --#end#--)
    transcript = riddle_parser.process_convo_text(transcript, top_static_text, bottom_static_text)
    if transcript is None:
        logging.error("No transcript generated. Cannot create video.")
        return
    
    highlighted_transcript = transcript.replace('--#start#--', '\033[1;32m--#start#--\033[0m') \
                                        .replace('--#end#--', '\033[1;31m--#end#--\033[0m') \
                                        .replace('--#answer#--', '\033[1;34m--#answer#--\033[0m')
    logging.info(f"Parsed transcript: {highlighted_transcript}")

    # Extract file name for output
    filename = os.path.basename(audio_path)
    output_filename = filename.replace(".wav", ".mp4")
    
    logging.info(f"Retrieved metadata: thumbnailText='{thumbnailText}', top_static_text='{top_static_text}', bottom_static_text='{bottom_static_text}'")
    
    # Load background image
    background_path = get_random_file_name(BACKGROUND_PATH, BACKGROUND_LABEL, BACKGROUND_IMAGES_N, BACKGROUND_EXT)
    audio = AudioFileClip(audio_path)
    
    # Split transcript into sentences and calculate total words
    sentences = transcript.split('. ')
    start_segment = None
    end_segment = None
    show_ans_segment = None

    for sentence in sentences:
        if "--#start#--" in sentence:
            sentence = sentence.replace("--#start#--", "")
            start_segment = find_segment_time(sentence, segments, "start", None)
        
        if "--#end#--" in sentence:
            sentence = sentence.replace("--#end#--", "")
            end_segment = find_segment_time(sentence, segments, "end", show_ans_segment)

        if "--#answer#--" in sentence:
            sentence = sentence.replace("--#answer#--", "")
            show_ans_segment = find_segment_time(sentence, segments, "start", start_segment)

    # if start_segment is None or end_segment is None:
    #     logging.error(f"Could not determine valid start and end times for trimming. Check transcript markers. {start_segment} and {end_segment}")
        trimmed_audio = audio  # Keep the original audio if times are invalid
    # else:
    #     trimmed_audio = audio.subclip(start_segment["start"], end_segment["end"])  # Trim the audio if both times are valid
    #     show_ans_segment["start"] = show_ans_segment["start"] - start_segment["start"]

    #     # Create a composite audio clip
    #     final_audio = CompositeAudioClip([trimmed_audio])
    #     final_audio.fps = audio.fps
    #     # Write the result to a file
    #     final_audio.write_audiofile("output_file.mp3")

    #     transcript, segments = transcribe_audio("output_file.mp3")

    txt_clips = []
    font_path = get_random_file_name(FONT_PATH, FONT_LABEL, FONT_N, FONT_EXT)
    for i, segment in enumerate(segments):
        try:
            # If near the answer, show the bottom static text
            temp_image_path = create_text_image(
                segment["text"], 
                background_path,
                "temp_text_image.png",
                font_path,
                static_text=top_static_text,
                bottom_static_text="" if show_ans_segment is None or segment is None or show_ans_segment["start"] > segment["start"] else bottom_static_text
            )
            if i < len(segments) - 1:
                duration = round(segments[i + 1]["end"] - segment["start"], 2)
            else:
                duration = round(segment["end"] - segment["start"], 2)
            clip = ImageClip(temp_image_path).set_duration(duration).set_start(segment["start"])
            txt_clips.append(clip)
            os.remove(temp_image_path)
            logging.info(f"Created text:{segment['text']} clip for time range: {segment['start']} - {segment['end']} duration: {duration}")

        except Exception as e:
            logging.error(f"Error creating text clip: {str(e)}", exc_info=True)
    
    if not txt_clips:
        logging.error("No text clips could be created. Cannot generate video.")
        return

    # Combine subtitle clips and audio into a single video
    subtitles_clip = CompositeVideoClip(txt_clips)
    video = CompositeVideoClip([subtitles_clip.set_audio(trimmed_audio)])  # Use trimmed audio here

    # Output video file
    output_path = os.path.join("video", output_filename)
    logging.info(f"Rendering video: {output_path}")
    video.write_videofile(output_path, fps=24)
    logging.info(f"Video saved as {output_path}")
    
    # Generate and save the thumbnail
    thumbnail_filename = f"{os.path.splitext(output_filename)[0]}-thumbnail.png"
    thumbnail_path = os.path.join("video", thumbnail_filename)
    try:
        create_text_image(
            thumbnailText, 
            background_path,
            thumbnail_path,
            font_path,
            static_text="",
            bottom_static_text=""
        )
        logging.info(f"Thumbnail created: {thumbnail_path}")
    except Exception as e:
        logging.error(f"Error generating thumbnail: {str(e)}", exc_info=True)
    
    # Resize the thumbnail
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
        cursor.execute("SELECT audioPath FROM entries WHERE generatedVideoPath IS NULL OR generatedVideoPath = ''")
        new_entries = cursor.fetchall()
        print(f"new_entries : {new_entries}")
        for (audio_path,) in new_entries:
            if os.path.exists(audio_path):
                logging.info(f"Processing new entry: {audio_path}")
                create_video_from_audio(audio_path)
            else:
                logging.warning(f"Audio file not found: {audio_path}")

        wait_with_logs(10)  # Sleep for a while before checking again
        create_riddles.start()

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