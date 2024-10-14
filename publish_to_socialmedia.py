import os
import time
import random
import logging
from moviepy.editor import *
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import sqlite3
import tweepy

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    handlers=[
        logging.StreamHandler()  # Log to console
    ]
)

# Define constants
DATABASE_PATH = 'ContentData/entries.db'
# YouTube API settings
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]
CLIENT_SECRETS_FILE = 'credentials.json'  # Path to your client_secret.json file

# Twitter API settings (fill with your credentials)
TWITTER_API_KEY = 'your_twitter_api_key'
TWITTER_API_SECRET = 'your_twitter_api_secret'
TWITTER_ACCESS_TOKEN = 'your_twitter_access_token'
TWITTER_ACCESS_SECRET = 'your_twitter_access_secret'

def get_youtube_service():
    """Authenticate and return a YouTube service object."""
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
    
    return build('youtube', 'v3', credentials=creds)

def upload_video_to_youtube(video_path, thumbnail_path, title, description):
    """Upload a video to YouTube and set the thumbnail."""
    youtube = get_youtube_service()

    # Set the video details
    request_body = {
        'snippet': {
            'categoryId': '22',  # Category for "People & Blogs"
            'title': title,
            'description': description,
            'tags': ['tag1', 'tag2'],  # Add any relevant tags
            'playlists': ['Riddle']  # Set the playlists here
        },
        'status': {
            'privacyStatus': 'private',  # Can be "public", "unlisted", or "private"
            'madeForKids': False,  # This video is NOT made for kids
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
        return

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

    # Add video to specified playlists
    try:
        for playlist in ['Riddle']:
            playlist_id = get_playlist_id(youtube, playlist)  # Implement this function to get the playlist ID
            if playlist_id:
                youtube.playlistItems().insert(
                    part='snippet',
                    body={
                        'snippet': {
                            'playlistId': playlist_id,
                            'resourceId': {
                                'kind': 'youtube#video',
                                'videoId': video_id
                            }
                        }
                    }
                ).execute()
                logging.info(f"Video added to playlist: {playlist}")
            else:
                logging.warning(f"Playlist '{playlist}' not found.")
    except Exception as e:
        logging.error(f"An error occurred while adding the video to the playlist: {e}")

    return video_id

def get_playlist_id(youtube, playlist_name):
    """Retrieve the playlist ID based on the playlist name."""
    request = youtube.playlists().list(
        part='id,snippet',
        mine=True  # Ensure you have the right scope to access your playlists
    )
    response = request.execute()

    for playlist in response.get('items', []):
        if playlist['snippet']['title'] == playlist_name:
            return playlist['id']
    return None


def post_to_twitter(title, thumbnail_path, description):
    """Post to Twitter with the video title and thumbnail, then reply with the description."""
    auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
    api = tweepy.API(auth)

    # Upload thumbnail image
    media = api.media_upload(thumbnail_path)

    # Post the tweet with title and image
    tweet = api.update_status(status=title, media_ids=[media.media_id_string])
    logging.info("Tweet posted successfully.")

    # Reply with the description
    api.update_status(status=description, in_reply_to_status_id=tweet.id, auto_populate_reply_metadata=True)
    logging.info("Description replied successfully.")

def process_entries_in_db():
    """Check the database for videos to upload to YouTube and post to Twitter."""
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()

    # Query for entries where generatedVideoPath and generatedThumbnailPath are not null and uploadedToYoutube is false
    cursor.execute(""" 
        SELECT id, title, description, generatedVideoPath, generatedThumbnailPath 
        FROM entries 
        WHERE generatedVideoPath IS NOT NULL 
        AND generatedThumbnailPath IS NOT NULL 
        AND uploadedToYoutube = 0
    """)
    entries = cursor.fetchall()

    for entry in entries:
        entry_id, title, description, video_path, thumbnail_path = entry
        
        # Upload the video to YouTube
        video_id = upload_video_to_youtube(video_path, thumbnail_path, title, description)
        
        if video_id:
            # Mark the entry as uploaded to YouTube
            cursor.execute("UPDATE entries SET uploadedToYoutube = 1 WHERE id = ?", (entry_id,))
            db.commit()
            logging.info(f"Entry {entry_id} marked as uploaded to YouTube.")

            # Post to Twitter
            post_to_twitter(title, thumbnail_path, description)

    db.close()

def monitor_database(interval=10):
    """Periodically check the database for new videos to upload."""
    while True:
        process_entries_in_db()
        time.sleep(interval)  # Check every `interval` seconds

if __name__ == "__main__":
    # Process existing entries in the database and continue checking every 10 minutes
    monitor_database()