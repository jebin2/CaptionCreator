import whisper
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import os
import time
import random
import sqlite3
import riddle_parser
import create_riddles
import logger_config
from moviepy.editor import ImageSequenceClip
import retrieveText
import databasecon
import common
import custom_env

logging = logger_config.setup_logging()

BACKGROUND_IMAGES_N = 11  # Total number of background images available
BACKGROUND_LABEL = 'background'
BACKGROUND_PATH = 'background_images'
BACKGROUND_EXT = 'jpg'
FONT_N = 2
FONT_LABEL = 'font'
FONT_PATH = 'Fonts'
FONT_EXT = 'ttf'
SHOW_ANSWER = False
TEMP_FILENAME = 'temp_text_image.png'
IMAGE_SIZE=(1920, 1080)

def get_random_file_name(path, label, n, ext, type=''):
    """Select a random background image from the available ones."""
    try:
        if type == 'chess':
            return custom_env.CHESS_BOARD_WITH_PUZZLE_JPG
        random_number = random.randint(1, n)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path_with_file_name = os.path.join(script_dir, path, f"{label}_{random_number}.{ext}")
        logging.info(f"Selected random path_with_file_name: {path_with_file_name}")
        return path_with_file_name
    except Exception as e:
        logging.error(f"Error selecting background image: {str(e)}", exc_info=True)
        return ""

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

def create_text_image(text, background_path, temp_filename, font_path, font_size=70, padding=50, extra_space=100, stroke_width=2, description="", answer="", img_size=IMAGE_SIZE):
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
        if description:
            static_font_size = int(font_size * 0.8)  # Slightly smaller font for static text
            static_font = ImageFont.truetype(font_path, static_font_size)
            max_static_width = img_size[0] - (2 * padding) - (2 * extra_space)

            # Wrap the static text
            wrapped_static_text = wrap_text(description, static_font, max_static_width)
            
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
        if answer:
            bottom_font_size = int(font_size * 0.8)
            bottom_font = ImageFont.truetype(font_path, bottom_font_size)
            max_bottom_width = img_size[0] - (2 * padding) - (2 * extra_space)

            # Wrap the bottom static text with the prefix
            wrapped_bottom_text = wrap_text("Answer is :: " + answer, bottom_font, max_bottom_width)

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
                logger_config.wait_with_logs(10)
            logging.info(f"Resized thumbnail to {file_size / 1024:.2f} KB with quality {quality}%")
        else:
            logging.info(f"Thumbnail {thumbnail_path} is within size limits")
        return thumbnail_path
    except Exception as e:
        logging.error(f"Error resizing thumbnail: {str(e)}", exc_info=True)
        return thumbnail_path

def process(id, audio_path=None, startWith = None):
    logging.info(f"Processing audio:: {audio_path}")
    if common.file_exists(audio_path) is False:
        return False
    transcript, segments = retrieveText.parse(audio_path)
    if not transcript:
        logging.error("No transcript generated. Cannot create video.")
        return False
    
    if startWith and not transcript.strip().startswith(startWith):
        logging.error(f"Generated transcript from NotebookLLM is not correct. Try again... {transcript} ::: {startWith}")
        logging.error(f"index:: {transcript.index(startWith)}")
        return False

    result = databasecon.execute("SELECT thumbnailText, description, answer, type FROM entries WHERE id = ?", (id,), type='get')

    thumbnailText, description, answer, type = result if result else ("", "", "", "")

    transcript = riddle_parser.process_convo_text(transcript, description, answer)
    if transcript is None:
        logging.error("No transcript generated. Cannot create video.")
        return False
    
    highlighted_transcript = transcript.replace('--#start#--', '\033[1;32m--#start#--\033[0m') \
                                        .replace('--#end#--', '\033[1;31m--#end#--\033[0m') \
                                        .replace('--#answer#--', '\033[1;34m--#answer#--\033[0m')
    logging.info(f"Parsed transcript: {highlighted_transcript}")

    # Extract file name for output
    output_filename = f"{common.generate_random_string()}.mp4"

    # Load background image
    background_path = get_random_file_name(BACKGROUND_PATH, BACKGROUND_LABEL, BACKGROUND_IMAGES_N, BACKGROUND_EXT, type)
    audio = AudioFileClip(audio_path)

    if audio.duration > 30 and type == 'facts':
        logging.error(f"facts cannot be more than 60 sec: {audio.duration}")
        return False

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

    start_show_answer = show_ans_segment['start'] if show_ans_segment and 'start' in show_ans_segment else audio.duration / 2
    # end_time = segments[-1]['end']

    txt_clips = []
    if type == 'chess':
        background = Image.open(background_path).resize(IMAGE_SIZE)
        # Save the image
        background.save(TEMP_FILENAME)
        logging.info(f"Text image created and saved to {TEMP_FILENAME}")

        clip = ImageClip(TEMP_FILENAME).set_duration(start_show_answer).set_start(0)
        txt_clips.append(clip)
        os.remove(TEMP_FILENAME)

        logging.info(f"Getting Chess move files...")
        files = common.list_files_recursive(custom_env.CHESS_MOVES_PATH)
        filtered_files = [file for file in files if file.endswith('.jpg')]
        logging.info(f"Success.")

        secondCount = 0
        # move_duration = round((end_time-4 - start_show_answer)/len(filtered_files), 2)
        move_duration = 2/custom_env.FPS
        can_break = False
        for i in range(1, 10):  # Adjust the upper limit as needed
            for j in range(custom_env.FPS):
                # Filtering files based on the expected naming convention
                file_in_order = [file for file in filtered_files if file.endswith(f'new_chess_board-update-{i}-{j}.jpg')]
                
                if file_in_order:
                    clip = ImageClip(file_in_order[0]).set_duration(move_duration).set_start(start_show_answer + secondCount)
                    txt_clips.append(clip)
                    logging.info(f"Clip created for file {file_in_order[0]} start at {start_show_answer}")
                    secondCount += move_duration  # Increment for the next clip duration
                else:
                    can_break = True
                    break
            if can_break:
                break
    else:
        font_path = get_random_file_name(FONT_PATH, FONT_LABEL, FONT_N, FONT_EXT)
        for i, segment in enumerate(segments):
            try:
                # If near the answer, show the bottom static text
                temp_image_path = create_text_image(
                    segment["text"], 
                    background_path,
                    TEMP_FILENAME,
                    font_path,
                    description='' if type == 'facts' else description,
                    answer="" if type == 'facts' or show_ans_segment is None or segment is None or show_ans_segment["start"] > segment["start"] else answer,
                    img_size=IMAGE_SIZE[::-1] if type == "facts" else IMAGE_SIZE
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
            return False
    
    logging.info(f"Combining audio {len(txt_clips)}")
    # Combine subtitle clips and audio into a single video
    subtitles_clip = CompositeVideoClip(txt_clips)
    logging.info(f"Combining audio Done")
    video = CompositeVideoClip([subtitles_clip.set_audio(audio)])  # Use trimmed audio here

    # Output video file
    output_path = os.path.join("video", output_filename)
    logging.info(f"Rendering video: {output_path}")
    video.write_videofile(output_path, fps=custom_env.FPS)
    logging.info(f"Video saved as {output_path}")
    
    # Generate and save the thumbnail
    thumbnail_filename = f"{os.path.splitext(output_filename)[0]}-thumbnail.png"
    thumbnail_path = os.path.join("video", thumbnail_filename)
    try:
        if type == 'chess':
            background = Image.open(background_path).resize(IMAGE_SIZE)
            # Save the image
            background.save(thumbnail_path)
        else:
            create_text_image(
                '' if type == 'facts' else thumbnailText, 
                background_path,
                thumbnail_path,
                font_path,
                img_size=IMAGE_SIZE[::-1] if type == "facts" else IMAGE_SIZE
            )

        logging.info(f"Thumbnail created: {thumbnail_path}")
    except Exception as e:
        logging.error(f"Error generating thumbnail: {str(e)}", exc_info=True)
    
    # Resize the thumbnail
    resize_thumbnail(thumbnail_path)
    
    databasecon.execute("""
            UPDATE entries 
            SET generatedVideoPath = ?, generatedThumbnailPath = ?
            WHERE id = ?
        """, (output_path, thumbnail_path, id))
    
    common.remove_file(audio_path)
    return True

# if __name__ == "__main__":
#     process('/home/jebineinstein/git/CaptionCreator/audio/Untitled notebook.wav')