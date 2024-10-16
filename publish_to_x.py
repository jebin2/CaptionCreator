import os
import time
import logging
import json
import sqlite3
from requests_oauthlib import OAuth1Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Define constants
DATABASE_PATH = 'ContentData/entries.db'

# Load Twitter API credentials from xcredentials.json
with open('xcredentials.json', 'r') as file:
    credentials = json.load(file)

consumer_key = credentials['api_key']
consumer_secret = credentials['api_secret_key']

# File to store access tokens
tokens_file = 'xtokens.json'

def save_tokens(access_token, access_token_secret):
    """Save access tokens to a file."""
    logging.info("Saving access tokens to file.")
    with open(tokens_file, 'w') as f:
        json.dump({
            'access_token': access_token,
            'access_token_secret': access_token_secret
        }, f)
    logging.info("Access tokens saved.")

def load_tokens():
    """Load access tokens from a file, if it exists."""
    logging.info("Loading access tokens from file.")
    if os.path.exists(tokens_file):
        with open(tokens_file, 'r') as f:
            tokens = json.load(f)
            logging.info("Access tokens loaded successfully.")
            return tokens['access_token'], tokens['access_token_secret']
    logging.info("No access tokens found.")
    return None, None

def authenticate():
    """Authenticate and get access tokens, or load existing ones."""
    logging.info("Authenticating with Twitter API.")
    access_token, access_token_secret = load_tokens()

    if access_token and access_token_secret:
        logging.info("Using existing access tokens.")
        return access_token, access_token_secret

    # Get request token
    logging.info("Fetching request token from Twitter API.")
    request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

    try:
        fetch_response = oauth.fetch_request_token(request_token_url)
    except ValueError:
        logging.error("Error fetching request token. Check your consumer_key or consumer_secret.")
        exit()

    resource_owner_key = fetch_response.get("oauth_token")
    resource_owner_secret = fetch_response.get("oauth_token_secret")
    logging.info("OAuth token received: %s", resource_owner_key)

    # Get authorization
    base_authorization_url = "https://api.twitter.com/oauth/authorize"
    authorization_url = oauth.authorization_url(base_authorization_url)
    logging.info("Please go here and authorize: %s", authorization_url)
    verifier = input("Paste the PIN here: ")

    # Get the access token
    logging.info("Exchanging verifier for access tokens.")
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
    logging.info("Access tokens received successfully.")

    # Save the tokens
    save_tokens(access_token, access_token_secret)

    return access_token, access_token_secret

def post_to_x(title, thumbnail_path, description):
    """Post to Twitter with the video title, an image, and reply with the description."""
    
    logging.info("Starting post to Twitter for title: %s", title)
    access_token, access_token_secret = authenticate()

    # Make the request with the access tokens
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )

    if os.path.exists(thumbnail_path) and os.path.isfile(thumbnail_path):
        logging.info("Uploading media from: %s", thumbnail_path)
        with open(thumbnail_path, 'rb') as image_file:
            media_upload_url = "https://upload.twitter.com/1.1/media/upload.json"
            response = oauth.post(media_upload_url, files={"media": image_file})

        if response.status_code != 200:
            logging.error("Media upload failed: %s %s", response.status_code, response.text)
            raise Exception("Media upload failed: {} {}".format(response.status_code, response.text))

        media_id = response.json()['media_id_string']
        logging.info("Media uploaded successfully, media ID: %s", media_id)

        tweet_payload = {
            "text": title,
            "media": {"media_ids": [media_id]}  # Include the media ID
        }
    else:
        logging.warning("Thumbnail not found, posting tweet without media.")
        tweet_payload = {
            "text": title
        }

    logging.info("Posting tweet with title: %s", title)
    tweet_url_v2 = "https://api.twitter.com/2/tweets"
    response = oauth.post(tweet_url_v2, json=tweet_payload)

    if response.status_code != 201:
        logging.error("Tweet post failed: %s %s", response.status_code, response.text)
        raise Exception("Request returned an error when posting tweet: {} {}".format(response.status_code, response.text))

    logging.info("Tweet posted successfully!")
    tweet_data = response.json()
    tweet_id = tweet_data['data']['id']  # Get the tweet ID for the reply

    # Step 3: Reply with the description
    reply_payload = {
        "text": description,
        "reply": {
            "in_reply_to_tweet_id": tweet_id  # Specify the tweet ID you're replying to
        }
    }

    logging.info("Replying to tweet ID: %s with description.", tweet_id)
    response = oauth.post(tweet_url_v2, json=reply_payload)

    if response.status_code != 201:
        logging.error("Reply to tweet failed: %s %s", response.status_code, response.text)
        raise Exception("Request returned an error when replying to tweet: {} {}".format(response.status_code, response.text))

    logging.info("Description replied successfully.")
    
    return tweet_id

def process_entries_in_db():
    """Check the database for videos to upload to Twitter."""
    logging.info("Connecting to database: %s", DATABASE_PATH)
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()

    # Query for entries where generatedThumbnailPath are not null
    logging.info("Fetching entries ready for Twitter posting.")
    cursor.execute(""" 
        SELECT id, title, description, generatedThumbnailPath, youtubeVideoId 
        FROM entries 
        WHERE generatedThumbnailPath IS NOT NULL 
        AND (uploadedToX = 0 OR uploadedToX IS NULL)
        AND uploadedToYoutube > 0
        AND uploadedToYoutube < ? 
    """, (int(time.time() * 1000) - 300000,))  # 5 minutes in milliseconds

    entries = cursor.fetchall()
    logging.info("Found %d entries to process.", len(entries))

    # Post to X (after all uploads are complete)
    for entry in entries:
        entry_id, title, description, thumbnail_path, youtubeVideoId = entry
        logging.info("Processing entry ID: %d for posting to Twitter.", entry_id)

        # Post to X
        youtube_link = f" https://www.youtube.com/watch?v={youtubeVideoId}" if youtubeVideoId else ""
        tweet_id = post_to_x(title, thumbnail_path, str(description + youtube_link))

        # Mark the entry as posted to X
        logging.info("Marking entry ID: %d as posted to Twitter with tweet ID: %s", entry_id, tweet_id)
        current_timestamp_ms = int(time.time() * 1000)
        cursor.execute("UPDATE entries SET uploadedToX = ?, tweetId = ? WHERE id = ?", (current_timestamp_ms, tweet_id, entry_id,))
        db.commit()

        logging.info("Sleeping for 1 minute before processing the next entry.")
        wait_with_logs(60)  # 1 minute

    logging.info("Closing the database connection.")
    db.close()

def monitor_database(interval=10):
    """Periodically check the database for new videos to upload."""
    logging.info("Starting database monitor with an interval of %d seconds.", interval)
    while True:
        logging.info("Checking database for new entries.")
        process_entries_in_db()
        logging.info("Sleeping for %d seconds before next check.", interval)
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
    logging.info("Twitter video uploader started. Monitoring the database.")
    # Monitor the database and check every 2.5 minutes
    monitor_database(interval=150)