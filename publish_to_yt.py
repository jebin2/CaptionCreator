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

from logger_config import setup_logging

logging = setup_logging()

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

def upload_video_to_youtube(video_path, thumbnail_path, title, description, type='text'):
    """Upload a video to YouTube and set the thumbnail."""
    logging.info(f"Starting upload for video: {video_path}")

    youtube = get_youtube_service(type)

    # Set the video details
    final_des = f"{description}\n\n#riddle #thinking #fun #challenges #challenge"
    tags = ['riddle', 'thinking', 'fun', 'challenges']
    if 'Chess' in title:
        final_des = f"{description}\n\n#chess #chessgame #chesspuzzle #challenges #challenge\n\n\n\nhttps://www.chess.com/daily-chess-puzzle/{title[-10]}"
    
    if 'facts' == type:
        final_des = "#shorts #interesting"
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
    
    logging.info("Checking whether video upload in 12hrs")
    entries = databasecon.execute(f""" 
        SELECT id, title, description, generatedVideoPath, generatedThumbnailPath, type
        FROM entries 
        WHERE uploadedToYoutube > {int(time.time() * 1000) - (12 *60 * 60 * 1000)} 
        AND uploadedToYoutube < {int(time.time() * 1000)}
        AND type = '{type}'
    """, type='get')

    logging.info(f'dfsdfsdf {entries}')
    if entries:
        logging.info("Will upload after 12 hrs")
        return

    # Query for entries where generatedVideoPath and generatedThumbnailPath are not null
    logging.info("Fetching entries with videos and thumbnails ready for upload...")
    entries = databasecon.execute(f""" 
        SELECT id, title, description, generatedVideoPath, generatedThumbnailPath, type
        FROM entries 
        WHERE (generatedVideoPath IS NOT NULL AND generatedVideoPath != '') 
        AND (generatedThumbnailPath IS NOT NULL AND generatedThumbnailPath != '')
        AND (uploadedToYoutube = 0 OR uploadedToYoutube IS NULL)
        AND type = '{type}'
    """)

    logging.info(f"Found {len(entries)} entries to process.")
    
    # Upload videos to YouTube
    for entry in entries:
        entry_id, title, description, video_path, thumbnail_path, type = entry
        logging.info(f"Processing entry {entry_id}: {title}")

        # Upload the video to YouTube
        video_id = upload_video_to_youtube(video_path, thumbnail_path, title, description, type)
        
        if not video_id:
            logging.error(f"Error uploading video for entry {entry_id}. Stopping further uploads.")
            break  # Stop further uploads if there's an error

        # Mark the entry as uploaded to YouTube
        logging.info(f"Marking entry {entry_id} as uploaded to YouTube with video ID {video_id}.")
        current_timestamp_ms = int(time.time() * 1000)
        databasecon.execute("UPDATE entries SET uploadedToYoutube = ?, youtubeVideoId = ? WHERE id = ?", (current_timestamp_ms, video_id, entry_id,))
        logging.info(f"Entry {entry_id} successfully updated in the database.")

        logging.info("Sleeping for 1 minute before next upload...")
        break

def monitor_database(interval=10):
    """Periodically check the database for new videos to upload."""
    logging.info(f"Starting database monitor with an interval of {interval} seconds.")
    while True:
        logging.info("Checking the database for new entries.")
        process_entries_in_db('text')
        process_entries_in_db('chess')
        process_entries_in_db('facts')
        logging.info(f"Sleeping for {interval} seconds before next check.")
        wait_with_logs(interval)

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
    # Monitor the database and check every 2.5 minutes
    logging.info("YouTube video uploader started. Monitoring the database.")
    monitor_database(interval=150)