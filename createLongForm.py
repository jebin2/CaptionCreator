import logger_config
import databasecon
import retrieveText
import convertToVideo
import custom_env
import common
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_audioclips
import retrieveAudio
import trimaudio
from typing import List, Tuple, Optional
import numpy as np
import combineAudio
import random
import json

START_WITH = ['Hello everyone', 'Hello', 'everyone']
END_WITH = ['Thank you for listening', 'Thanks for listening', 'for listening']

def get_valid_entries(limit: int = 100) -> List[Tuple[str]]:
    return databasecon.execute(f"""SELECT id, description, answer, generatedVideoPath FROM entries WHERE type ='text'
        AND (addedToLongForm is NULL OR addedToLongForm = '')
        AND generatedVideoPath is not NULL
        AND generatedVideoPath != ''
        order by id desc limit {limit}"""
    )

def process_audio_file(file_path: str) -> Optional[str]:
    try:
        audio = AudioFileClip(file_path)
        if audio.duration < 1:  # Minimum 1 second
            logger_config.error(f"Less than 1 second")
            return None
        return file_path
    except Exception as e:
        logger_config.error(f"Error processing audio file {file_path}: {str(e)}")
        return None

def process_video_entry(video_path: str, skipEnd: bool = False) -> Optional[str]:
    try:
        if not common.file_exists(video_path):
            logger_config.error(f'Video path does not exist: {video_path}')
            return None

        path = retrieveAudio.get(video_path)
        transcript, segments = retrieveText.parse(path)
        
        hasStartText = False
        for text in START_WITH:
            if transcript.strip().lower().startswith(text.lower()):
                hasStartText = True
                break
        
        if not hasStartText:
            logger_config.error(f"Not valid transcript")
            return None
        
        if segments:
            trimmed_path = trimaudio.get(path, fromText=START_WITH, endText=None if skipEnd else END_WITH, segments=segments)
            return process_audio_file(trimmed_path)
        else:
            return process_audio_file(path)
            
    except Exception as e:
        logger_config.error(f"Error processing video {video_path}: {str(e)}")
        return None

def save_to_database(audio_path: str, puzzle_start_w_title='') -> Tuple[int, str]:
    databasecon.execute(
        """DELETE FROM entries
        WHERE (generatedVideoPath IS NULL OR generatedVideoPath = '')
        AND type = 'long_form_text'"""
    )

    title = ['10 Mind-Bending Riddles: Can You Solve Them All?', 'Ultimate Riddle Challenge: 10 Puzzles to Test Your Wits!', '10 Fun Riddles: How Many Can You Solve?', 'Brain Teasers: 10 Riddles That Will Stump You!', '10 Challenging Riddles: Put Your Brain to the Test!', '10 Tricky Riddles: Are You Smart Enough to Solve Them?', 'Riddle Me This: 10 Puzzles for the Cleverest Minds!', '10 Brain Teasers: How Many Can You Crack?', '10 Riddles to Test Your Logic and Wit!', 'Challenge Accepted: Can You Solve These 10 Riddles?', '10 Fun and Challenging Riddles to Get Your Brain Working!', 'Are You a Riddle Master? Solve These 10 Puzzles!', 'Riddle Rumble: 10 Puzzles to Engage Your Mind!', 'Puzzling Perfection: 10 Riddles to Delight Your Mind!', 'The Riddle Room: 10 Puzzles to Unlock!', 'Mind Benders: 10 Riddles to Challenge Your Brain!']
    description = ['10 Riddles to Solve!', 'Can You Crack Them?', 'Test Your Brainpower!', 'Ultimate Riddle Challenge!', 'Mind-Bending Puzzles Inside!', 'Riddle Me This!', 'Are You Up for the Challenge?', 'Stump Your Friends!', 'Can You Guess the Answers?', 'Join the Riddle Fun!']
    random_title = random.randint(0, len(title)-1)
    random_desc = random.randint(0, len(description)-1)
    databasecon.execute(
        """INSERT into entries (audioPath, title, description, thumbnailText, answer, type, addedToLongForm) 
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (audio_path, title[random_title], 'desc', description[random_desc], 'answer', 'long_form_text', puzzle_start_w_title), type='get'
    )

    return databasecon.execute(
        f"SELECT id, audioPath FROM entries WHERE audioPath ='{audio_path}' "
        "AND type = 'long_form_text'",
        type='get'
    )

def start() -> bool:
    try:
        entries = get_valid_entries()
        if len(entries) < 10:
            logger_config.warning("No required amount of video found")
            return False

        # Initialize audio components
        audio_clips = ['background_music/hello.wav']
        next_puzzle = "background_music/next_puzzle.wav"
        processed_count = 1
        itr_count = 0
        max_audio_count = 10

        puzzle_start_w_title = []

        # Process videos and collect audio
        for entry in entries:
            itr_count += 1
            if processed_count > max_audio_count:  # Process 3 videos (1 initial + 2 additional)
                break

            id, description, answer, video_path = entry
            logger_config.warning(f"Trying for video:: {processed_count} :: {video_path} :: totl itr :: {itr_count}")

            # Process video entry
            audio_path = process_video_entry(video_path, skipEnd=(processed_count==max_audio_count))

            if audio_path is None:
                logger_config.error(f"audio_path none continue...")
                continue

            # Handle first clip differently
            if audio_path:
                audio_clips.append(audio_path)
                audio = AudioFileClip(audio_path)
                start = 0 if len(puzzle_start_w_title) == 0 else puzzle_start_w_title[-1]['end'] + 4
                puzzle_start_w_title.append({
                    "id": id,
                    "start": start,
                    "end": audio.duration,
                    "description": description,
                    'answer': answer
                })
                logger_config.warning(puzzle_start_w_title)
                if processed_count < max_audio_count:
                    audio_clips.append(next_puzzle)

                processed_count += 1
                continue
        
        # Combine audio clips
        final_path = f'audio/{common.generate_random_string()}.wav'
        try:
            # Use CompositeAudioClip for direct concatenation
            final_path = combineAudio.start(audio_clips, final_path)
            for file in audio_clips:
                if 'hello' not in file and 'next_puzzle' not in file:
                    common.remove_file(file)
            logger_config.success(f'final combining audioPath:: {final_path}')
        except Exception as e:
            logger_config.error(f"Error combining audio: {str(e)}")
            return False

        if processed_count < max_audio_count:
            logger_config.warning("No required amount of video found after processing")
            return False

        try:
            entry_id, audio_path = save_to_database(final_path, json.dumps(puzzle_start_w_title))
            is_success = convertToVideo.process(entry_id, audio_path=audio_path, puzzle_start_w_title=puzzle_start_w_title)
            common.update_database_status(entry_id, is_success)
            return is_success
        except Exception as e:
            logger_config.error(f"Error in database operations: {str(e)}")
            return False

    except Exception as e:
        logger_config.error(f"Error in createLongForm::start : {str(e)}")
        return False

if __name__ == "__main__":
    start()