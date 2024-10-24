import os
import time
import json
import sqlite3
from requests_oauthlib import OAuth1Session
import custom_env
import logger_config
import common
import databasecon

# Load Twitter API credentials from xcredentials.json
with open('xcredentials.json', 'r') as file:
    credentials = json.load(file)

consumer_key = credentials['api_key']
consumer_secret = credentials['api_secret_key']

# File to store access tokens
tokens_file = 'xtokens.json'

def save_tokens(access_token, access_token_secret):
    """Save access tokens to a file."""
    logger_config.info("Saving access tokens to file.")
    with open(tokens_file, 'w') as f:
        json.dump({
            'access_token': access_token,
            'access_token_secret': access_token_secret
        }, f)
    logger_config.info("Access tokens saved.")

def load_tokens():
    """Load access tokens from a file, if it exists."""
    logger_config.info("Loading access tokens from file.")
    if os.path.exists(tokens_file):
        with open(tokens_file, 'r') as f:
            tokens = json.load(f)
            logger_config.info("Access tokens loaded successfully.")
            return tokens['access_token'], tokens['access_token_secret']
    logger_config.info("No access tokens found.")
    return None, None

def authenticate():
    """Authenticate and get access tokens, or load existing ones."""
    logger_config.info("Authenticating with Twitter API.")
    access_token, access_token_secret = load_tokens()

    if access_token and access_token_secret:
        logger_config.info("Using existing access tokens.")
        return access_token, access_token_secret

    # Get request token
    logger_config.info("Fetching request token from Twitter API.")
    request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

    try:
        fetch_response = oauth.fetch_request_token(request_token_url)
    except ValueError:
        logger_config.error("Error fetching request token. Check your consumer_key or consumer_secret.")
        exit()

    resource_owner_key = fetch_response.get("oauth_token")
    resource_owner_secret = fetch_response.get("oauth_token_secret")
    logger_config.info("OAuth token received: %s", resource_owner_key)

    # Get authorization
    base_authorization_url = "https://api.twitter.com/oauth/authorize"
    authorization_url = oauth.authorization_url(base_authorization_url)
    logger_config.info("Please go here and authorize: %s", authorization_url)
    verifier = input("Paste the PIN here: ")

    # Get the access token
    logger_config.info("Exchanging verifier for access tokens.")
    access_token_url = "https://api.twitter.com/oauth/access_token"
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier,
    )
    oauth_tokens = oauth.fetch_access_token(access_token_url)

    access_token = oauth_tokens["oauth_token"]
    access_token_secret = oauth_tokens["oauth_token_secret"]
    logger_config.info("Access tokens received successfully.")

    # Save the tokens
    save_tokens(access_token, access_token_secret)

    return access_token, access_token_secret

def upload_image(oauth, image_path):
    media_upload_url = "https://upload.twitter.com/1.1/media/upload.json"
    with open(image_path, 'rb') as image_file:
        response = oauth.post(media_upload_url, files={"media": image_file})

    if response.status_code != 200:
        logger_config.error("Image upload failed: %s %s", response.status_code, response.text)
        return None

    media_id = response.json()['media_id_string']
    logger_config.info("Image uploaded successfully, media ID: %s", media_id)
    return media_id


def upload_video(oauth, video_path):
    """Handles video upload to Twitter using chunked media upload."""
    media_upload_url = "https://upload.twitter.com/1.1/media/upload.json"

    # Step 1: INIT the upload
    video_size = os.path.getsize(video_path)
    init_data = {
        "command": "INIT",
        "media_type": "video/mp4",
        "total_bytes": video_size,
        "media_category": "tweet_video"
    }
    response = oauth.post(media_upload_url, data=init_data)
    if response.status_code != 202:
        logger_config.error("Video INIT failed: %s %s", response.status_code, response.text)
        return None

    media_id = response.json()['media_id_string']
    logger_config.info("Video INIT successful, media ID: %s", media_id)

    # Step 2: APPEND the video in chunks
    with open(video_path, 'rb') as video_file:
        segment_id = 0
        while True:
            chunk = video_file.read(4 * 1024 * 1024)  # Read 4MB at a time
            if not chunk:
                break
            append_data = {
                "command": "APPEND",
                "media_id": media_id,
                "segment_index": segment_id
            }
            files = {"media": chunk}
            response = oauth.post(media_upload_url, data=append_data, files=files)
            if response.status_code != 204:
                logger_config.error("Video APPEND failed: %s %s", response.status_code, response.text)
                return None
            segment_id += 1

    # Step 3: FINALIZE the upload
    finalize_data = {
        "command": "FINALIZE",
        "media_id": media_id
    }
    response = oauth.post(media_upload_url, data=finalize_data)
    if response.status_code != 201:
        logger_config.error("Video FINALIZE failed: %s %s", response.status_code, response.text)
        return None

    logger_config.info("Video FINALIZE successful, media ID: %s", media_id)
    return media_id

def post_to_x(title, video_path, thumbnail_path, description, type):
    """Post to Twitter with the video title, an image, and reply with the description."""
    
    logger_config.info("Starting post to Twitter for title: %s", title)
    access_token, access_token_secret = authenticate()

    # Make the request with the access tokens
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )

    media_id = None
    if type == 'facts':
        if os.path.exists(video_path) and os.path.isfile(video_path):
            logger_config.info("Uploading media from: %s", video_path)
            media_id = upload_video(oauth, video_path)
    else:
        if os.path.exists(thumbnail_path) and os.path.isfile(thumbnail_path):
            logger_config.info("Uploading image from: %s", thumbnail_path)
            media_id = upload_image(oauth, thumbnail_path)

    if media_id:
        tweet_payload = {
            "text": title,
            "media": {"media_ids": [media_id]}  # Include the media ID
        }
    else:
        tweet_payload = {
            "text": title
        }

    logger_config.info("Posting tweet with title: %s", title)
    tweet_url_v2 = "https://api.twitter.com/2/tweets"
    response = oauth.post(tweet_url_v2, json=tweet_payload)

    if response.status_code != 201:
        logger_config.error("Tweet post failed: %s %s", response.status_code, response.text)
        raise Exception("Request returned an error when posting tweet: {} {}".format(response.status_code, response.text))

    logger_config.info("Tweet posted successfully!")
    tweet_data = response.json()
    tweet_id = tweet_data['data']['id']  # Get the tweet ID for the reply

    # Step 3: Reply with the description
    reply_payload = {
        "text": description,
        "reply": {
            "in_reply_to_tweet_id": tweet_id  # Specify the tweet ID you're replying to
        }
    }

    logger_config.info("Replying to tweet ID: %s with description.", tweet_id)
    response = oauth.post(tweet_url_v2, json=reply_payload)

    if response.status_code != 201:
        logger_config.error("Reply to tweet failed: %s %s", response.status_code, response.text)
        raise Exception("Request returned an error when replying to tweet: {} {}".format(response.status_code, response.text))

    logger_config.info("Description replied successfully.")

    if 'Chess' in title:
        chess_link = f"https://www.chess.com/daily-chess-puzzle/{title[-10:]}"

        # Step 4: Reply with the description
        reply_payload = {
            "text": chess_link,
            "reply": {
                "in_reply_to_tweet_id": tweet_id  # Specify the tweet ID you're replying to
            }
        }

        logger_config.info("Replying to tweet ID: %s with description.", tweet_id)
        response = oauth.post(tweet_url_v2, json=reply_payload)

        if response.status_code != 201:
            logger_config.error("Reply to tweet failed: %s %s", response.status_code, response.text)
            raise Exception("Request returned an error when replying to tweet: {} {}".format(response.status_code, response.text))

        logger_config.info("Chess Link replied successfully.")
    
    return tweet_id

def process_entries_in_db():
    logger_config.info("Fetching entries ready for Twitter posting.")
    entries = databasecon.execute(f""" 
        SELECT id, title, description, generatedVideoPath, generatedThumbnailPath, youtubeVideoId, type 
        FROM entries 
        WHERE generatedThumbnailPath IS NOT NULL 
        AND (uploadedToX = 0 OR uploadedToX IS NULL)
        AND uploadedToYoutube > 0
        AND uploadedToYoutube < '{int(time.time() * 1000) - 300000}' 
    """)  # 5 minutes in milliseconds

    logger_config.info("Found %d entries to process.", len(entries))

    # Post to X (after all uploads are complete)
    for entry in entries:
        entry_id, title, description, video_path, thumbnail_path, youtubeVideoId, type = entry
        logger_config.info("Processing entry ID: %d for posting to Twitter.", entry_id)

        # Post to X
        youtube_link = f" https://www.youtube.com/watch?v={youtubeVideoId}" if youtubeVideoId else ""
        tweet_id = post_to_x(title, video_path, thumbnail_path, str(description + youtube_link), type)

        # Mark the entry as posted to X
        logger_config.info("Marking entry ID: %d as posted to Twitter with tweet ID: %s", entry_id, tweet_id)
        current_timestamp_ms = int(time.time() * 1000)
        databasecon.execute("UPDATE entries SET uploadedToX = ?, tweetId = ? WHERE id = ?", (current_timestamp_ms, tweet_id, entry_id,))

        logger_config.info(f"========================================================")
        logger_config.info(f"=                                                      =")
        logger_config.info(f"=Entry {entry_id} successfully posted to X             =")
        logger_config.info(f"=                                                      =")
        logger_config.info(f"========================================================")

        logger_config.info("Sleeping for 1 minute before processing the next entry.")
        common.remove_file(thumbnail_path)
        # common.remove_file(video_path)

    logger_config.info("Closing the database connection.")

def start(interval=10):
    try:
        logger_config.info("Starting database monitor with an interval of %d seconds.", interval)
        while True:
            logger_config.info("Checking database for new entries.")
            process_entries_in_db()
            logger_config.info("Sleeping for %d seconds before next check.", interval)
            logger_config.info(f"Waiting before new X post", 10)
            if interval == 0:
                break
    except Exception as e:
        logger_config.error(f"Error in publish to X:: {str(e)}")
        return False

    return True

if __name__ == "__main__":
    # Monitor the database and check every 2.5 minutes
    logger_config.info("Twitter started. Monitoring the database.")
    start(interval=10)