import os
import time
import json
import sqlite3
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import custom_env
import databasecon
import common

import logger_config

logging = logger_config.setup_logging()

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]
CLIENT_SECRETS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

KNOW_IT_CLIENT_SECRETS_FILE = 'credentials.json' #'knowityt.json'
KNOW_IT_TOKEN_FILE = 'token.json' #'knowityt-token.json'

# Global services to prevent re-authentication
youtube_service = None
know_it_youtube_service = None

def get_youtube_service(type='text'):
    global youtube_service
    if type == 'text' and youtube_service:
        logging.info("Using existing YouTube service.")
        return youtube_service
    
    if type == 'facts' and know_it_youtube_service:
        logging.info("Using existing KnowIt YouTube service.")
        return youtube_service

    specific_token = TOKEN_FILE if type == 'text' else KNOW_IT_TOKEN_FILE
    specific_client = CLIENT_SECRETS_FILE if type == 'text' else KNOW_IT_CLIENT_SECRETS_FILE
    logging.info("Checking for stored credentials...")
    creds = None
    if os.path.exists(specific_token):
        creds = Credentials.from_authorized_user_file(specific_token, SCOPES)
        logging.info("Found existing credentials.")

    # Refresh the token if it's expired
    if creds and creds.expired and creds.refresh_token:
        try:
            logging.info("Refreshing expired credentials...")
            creds.refresh(Request())  # This will use the refresh token to get a new access token
            logging.info("Credentials refreshed successfully.")
        except Exception as e:
            logging.error(f"Error refreshing token: {e}")
            creds = None  # Reset creds to trigger new auth flow

    # If no valid credentials are available, prompt the user to log in again
    if not creds or not creds.valid:
        if not creds or not creds.refresh_token:
            logging.info("No valid credentials or refresh token found. Initiating authentication flow.")
            flow = InstalledAppFlow.from_client_secrets_file(specific_client, SCOPES)
            creds = flow.run_local_server(port=0)
            logging.info("New credentials obtained successfully.")
        
        # Save the credentials to the file for the next run
        with open(specific_token, 'w') as token:
            token.write(creds.to_json())
            logging.info("Credentials saved to 'token.json'.")

    logging.info("Building YouTube service...")
    youtube_service = build('youtube', 'v3', credentials=creds)
    logging.info("YouTube service built successfully.")
    return youtube_service

def upload_video_to_youtube(video_path, thumbnail_path, title, description, type='text', riddle_shorts=False, old_video_id=None):
    """Upload a video to YouTube and set the thumbnail."""
    logging.info(f"Starting upload for video: {video_path}")

    youtube = get_youtube_service(type)

    start_desc = ''
    if 'text' == type:
        start_desc = f"Puzzle: {description}"
    if 'chess' == type:
        start_desc = f"Puzzle: {description}\nhttps://www.chess.com/daily-chess-puzzle/{title[-10:]}"
    if 'facts' == type:
        start_desc += f"Puzzle: {description}"
        if riddle_shorts:
            start_desc += f"Puzzle: {description}\n Solution:https://www.youtube.com/watch?v={old_video_id}"

    # Set the video details
    final_des = f"""{start_desc}

Welcome to Think Solve Now – Your Ultimate Destination for Riddles, Puzzles, and Chess Challenges!

Are you ready to challenge your mind with brain teasers, riddles, and chess puzzles? On this channel, we dive into intriguing riddles, clever puzzles, and fun chess challenges that will push your critical thinking and strategy skills to the limit. Whether you love logic puzzles, word riddles, or solving chess positions, we’ve got something for everyone!

In each video, we’ll present a new puzzle or chess scenario, give you a chance to solve it, and then break down the solution step by step. From classic riddles to tricky chess puzzles, this channel is perfect for curious minds, chess lovers, and puzzle enthusiasts alike.

🔍 Why Subscribe?

- Fresh riddles, puzzles, and chess challenges uploaded regularly.
- Step-by-step explanations to enhance both your problem-solving and chess skills.
- Interactive puzzles designed to engage and challenge your mind.
- Perfect for anyone who enjoys mental challenges, brain workouts, and chess strategy.

🧩 Topics We Cover:

Logic riddles
- Math puzzles
- Lateral thinking puzzles
- Chess puzzles and tactics
- Brain teasers
- Wordplay and conundrums

♟️ Chess Enthusiasts:

- Dive into chess puzzles that sharpen your game strategy.
- Solve complex positions and learn how to outsmart your opponent.

💡 Join our community of puzzle solvers and chess lovers today! Hit that subscribe button and ring the bell for notifications so you never miss a challenge!

#Riddles #Puzzles #ChessPuzzles #BrainTeasers #MindGames #LogicPuzzles #ChessTactics #CriticalThinking #ProblemSolving #LateralThinking #Quiz #PuzzleLovers #BrainGames #ThinkSolveNow
"""
    tags = ['riddle', 'thinking', 'fun', 'challenges']
    
    if 'facts' == type:
        tags.append("shorts")

    request_body = {
        'snippet': {
            'categoryId': '22',  # Category for "People & Blogs"
            'title': title,
            'description': final_des,
            'tags': tags,  # Add any relevant tags
            'playlists': ['Riddle']  # Set the playlists here
        },
        'status': {
            'privacyStatus': 'public',  # Changed to "public"
            'madeForKids': False,  # This video is NOT made for kids
            'selfDeclaredMadeForKids': False,
        }
    }

    # Upload the video
    media_file = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part='snippet,status', body=request_body, media_body=media_file)

    logging.info(f"Uploading video: {video_path}")
    response = None
    try:
        while response is None:
            status, response = request.next_chunk()
            if status:
                logging.info(f'Uploaded {int(status.progress() * 100)}% of the video.')
    except Exception as e:
        logging.error(f"An error occurred during video upload: {e}")
        return False

    video_id = response['id']
    logging.info(f'Video uploaded successfully with ID: {video_id}')

    # Set the thumbnail (optional)
    try:
        logging.info(f"Uploading thumbnail: {thumbnail_path}")
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path)
        ).execute()
        logging.info(f"Thumbnail uploaded successfully for video ID: {video_id}")
    except Exception as e:
        logging.error(f"An error occurred during thumbnail upload: {e}")

    return video_id

def process_entries_in_db(type):
    logging.info("--------------------------------------")
    logging.info("Checking whether video upload in 12hrs")
    logging.info("--------------------------------------")
    hours = 24 if type == 'chess' else 1
    entries = databasecon.execute(f""" 
        SELECT id, title, description, generatedVideoPath, generatedThumbnailPath, type
        FROM entries 
        WHERE uploadedToYoutube > {int(time.time() * 1000) - (hours *60 * 60 * 1000)} 
        AND uploadedToYoutube < {int(time.time() * 1000)}
        AND type = '{type}'
    """, type='get')

    if entries:
        logging.info(f"Will upload after 1 hrs :: {entries}")
        return

    # Query for entries where generatedVideoPath and generatedThumbnailPath are not null
    logging.info("Fetching entries with videos and thumbnails ready for upload...")
    is_data_avail = False
    entries = None
    date_count = 0
    riddle_shorts = False
    while not is_data_avail:
        date_contains = common.get_date(date_count)
        filter = f"AND title LIKE '%{date_contains}%'" if type == 'chess' else ''
        entries = databasecon.execute(f""" 
            SELECT id, title, description, generatedVideoPath, generatedThumbnailPath, type
            FROM entries 
            WHERE (generatedVideoPath IS NOT NULL AND generatedVideoPath != '') 
            AND (generatedThumbnailPath IS NOT NULL AND generatedThumbnailPath != '')
            AND (uploadedToYoutube = 0 OR uploadedToYoutube IS NULL)
            AND type = '{type}'
            {filter}
            limit 1
        """)
        date_count += 1
        is_data_avail = len(entries) > 0 or date_count > 50

        if len(entries) > 0 and type == 'text':
            title = entries[0][1]
            logging.info(f"Checking facts for title {title} entries to process.")
            entries = databasecon.execute(f""" 
                SELECT id, title, description, generatedVideoPath, generatedThumbnailPath, type
                FROM entries 
                WHERE title = ?
            """, (title,))
            riddle_shorts = len(entries) > 1

        if len(entries) > 0 and type == 'facts':
            title = entries[0][1]
            logging.info(f"Checking facts for title {title} entries to process.")
            entries = databasecon.execute(f""" 
                SELECT id, title, description, generatedVideoPath, generatedThumbnailPath, type
                FROM entries 
                WHERE title = ? AND type = 'text'
            """, (title, type))

            if len(entries) > 0:
                entries = databasecon.execute(f""" 
                    SELECT id, title, description, generatedVideoPath, generatedThumbnailPath, type
                    FROM entries 
                    WHERE title != ? AND type = ?
                """, (title, type))

    logging.info(f"Found {len(entries)} entries to process.")
    
    # Upload videos to YouTube
    video_id = None
    for entry in entries:
        entry_id, title, description, video_path, thumbnail_path, type = entry
        logging.info(f"Processing entry {entry_id}: {title}")

        # Upload the video to YouTube
        video_id = upload_video_to_youtube(video_path, thumbnail_path, title, description, type, riddle_shorts, video_id)
        
        if not video_id:
            logging.error(f"Error uploading video for entry {entry_id}. Stopping further uploads.")
            break  # Stop further uploads if there's an error

        # Mark the entry as uploaded to YouTube
        logging.info(f"Marking entry {entry_id} as uploaded to YouTube with video ID {video_id}.")
        current_timestamp_ms = int(time.time() * 1000)
        databasecon.execute("UPDATE entries SET uploadedToYoutube = ?, youtubeVideoId = ? WHERE id = ?", (current_timestamp_ms, video_id, entry_id,))
        logging.info(f"Entry {entry_id} successfully updated in the database.")

        logging.info(f"========================================================")
        logging.info(f"=                                                      =")
        logging.info(f"=Entry {entry_id} successfully posted to YT            =")
        logging.info(f"=                                                      =")
        logging.info(f"========================================================")


        logging.info("Sleeping for 1 minute before next upload...")

def start(interval=10):
    try:
        logging.info(f"Starting database monitor with an interval of {interval} seconds.")
        while True:
            logging.info("Checking the database for new entries.")
            process_entries_in_db('text')
            process_entries_in_db('chess')
            process_entries_in_db('facts')
            logging.info(f"Sleeping for {interval} seconds before next check.")
            logger_config.wait_with_logs(interval)
            if interval == 0:
                break 
    except Exception as e:
        logging.error(f"Error in publish to yt:: {str(e)}", exc_info=True)
        return False

    return True

if __name__ == "__main__":
    # Monitor the database and check every 2.5 minutes
    logging.info("YouTube video uploader started. Monitoring the database.")
    start(interval=10)