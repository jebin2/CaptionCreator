import os
import time
import logging
import json
import sqlite3
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Define constants
DATABASE_PATH = 'ContentData/entries.db'
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]
CLIENT_SECRETS_FILE = 'credentials.json'

# Global services to prevent re-authentication
youtube_service = None

def get_youtube_service():
    """Authenticate and return a YouTube service object."""
    global youtube_service
    if youtube_service:
        return youtube_service

    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            logging.info("Credentials refreshed.")
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            logging.info("New credentials obtained.")
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    youtube_service = build('youtube', 'v3', credentials=creds)
    return youtube_service

def upload_video_to_youtube(video_path, thumbnail_path, title, description):
    """Upload a video to YouTube and set the thumbnail."""
    youtube = get_youtube_service()

    # Set the video details
    request_body = {
        'snippet': {
            'categoryId': '22',  # Category for "People & Blogs"
            'title': title,
            'description': description + "\n\n#riddle #thinking #fun #challenges",
            'tags': ['riddle', 'thinking', 'fun', 'challenges'],  # Add any relevant tags
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

    response = None
    try:
        while response is None:
            status, response = request.next_chunk()
            if status:
                logging.info(f'Uploaded {int(status.progress() * 100)}%.')
    except Exception as e:
        logging.error(f"An error occurred during upload: {e}")
        return False

    video_id = response['id']
    logging.info(f'Video uploaded successfully with ID: {video_id}')

    # Set the thumbnail
    try:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path)
        ).execute()
        logging.info(f"Thumbnail uploaded successfully for video ID: {video_id}")
    except Exception as e:
        logging.error(f"An error occurred during thumbnail upload: {e}")

    return video_id

def process_entries_in_db():
    """Check the database for videos to upload to YouTube."""
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()

    # Query for entries where generatedVideoPath and generatedThumbnailPath are not null
    cursor.execute(""" 
        SELECT id, title, description, generatedVideoPath, generatedThumbnailPath 
        FROM entries 
        WHERE generatedVideoPath IS NOT NULL 
        AND generatedThumbnailPath IS NOT NULL
        AND uploadedToYoutube = 0
    """)
    entries = cursor.fetchall()

    # Upload videos to YouTube
    for entry in entries:
        entry_id, title, description, video_path, thumbnail_path = entry
        
        # Upload the video to YouTube
        video_id = upload_video_to_youtube(video_path, thumbnail_path, title, description)
        
        if not video_id:
            logging.error("Stopping further uploads due to an error.")
            break  # Stop further uploads if there's an error

        # Mark the entry as uploaded to YouTube
        current_timestamp_ms = int(time.time() * 1000)
        cursor.execute("UPDATE entries SET uploadedToYoutube = ?, youtubeVideoId = ? WHERE id = ?", (current_timestamp_ms, video_id, entry_id,))
        db.commit()
        logging.info(f"Entry {entry_id} marked as uploaded to YouTube.")
        time.sleep(60)  # 1 minute

    db.close()

def monitor_database(interval=10):
    """Periodically check the database for new videos to upload."""
    while True:
        logging.info("Checking DB for new enteries")
        process_entries_in_db()
        time.sleep(interval)

if __name__ == "__main__":
    # Monitor the database and check every 2.5 minutes
    monitor_database(interval=150)