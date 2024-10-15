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
    with open(tokens_file, 'w') as f:
        json.dump({
            'access_token': access_token,
            'access_token_secret': access_token_secret
        }, f)

def load_tokens():
    """Load access tokens from a file, if it exists."""
    if os.path.exists(tokens_file):
        with open(tokens_file, 'r') as f:
            tokens = json.load(f)
            return tokens['access_token'], tokens['access_token_secret']
    return None, None

def authenticate():
    """Authenticate and get access tokens, or load existing ones."""
    access_token, access_token_secret = load_tokens()

    if access_token and access_token_secret:
        return access_token, access_token_secret

    # Get request token
    request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

    try:
        fetch_response = oauth.fetch_request_token(request_token_url)
    except ValueError:
        print("There may have been an issue with the consumer_key or consumer_secret you entered.")
        exit()

    resource_owner_key = fetch_response.get("oauth_token")
    resource_owner_secret = fetch_response.get("oauth_token_secret")
    print("Got OAuth token: %s" % resource_owner_key)

    # Get authorization
    base_authorization_url = "https://api.twitter.com/oauth/authorize"
    authorization_url = oauth.authorization_url(base_authorization_url)
    print("Please go here and authorize: %s" % authorization_url)
    verifier = input("Paste the PIN here: ")

    # Get the access token
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

    # Save the tokens
    save_tokens(access_token, access_token_secret)

    return access_token, access_token_secret

def post_to_x(title, thumbnail_path, description):
    """Post to Twitter with the video title, an image, and reply with the description."""
    
    access_token, access_token_secret = authenticate()

    # Make the request with the access tokens
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )

    # Step 1: Upload the image (thumbnail)
    with open(thumbnail_path, 'rb') as image_file:
        media_upload_url = "https://upload.twitter.com/1.1/media/upload.json"
        response = oauth.post(media_upload_url, files={"media": image_file})

    if response.status_code != 200:
        raise Exception("Media upload failed: {} {}".format(response.status_code, response.text))
    
    media_id = response.json()['media_id_string']
    print("Media uploaded successfully, media ID: {}".format(media_id))

    # Step 2: Post the tweet with the title and the uploaded media
    tweet_payload = {
        "text": title,
        "media": {"media_ids": [media_id]}  # Include the media ID
    }

    tweet_url_v2 = "https://api.twitter.com/2/tweets"
    response = oauth.post(tweet_url_v2, json=tweet_payload)

    if response.status_code != 201:
        raise Exception("Request returned an error when posting tweet: {} {}".format(response.status_code, response.text))

    print("Tweet posted successfully!")
    tweet_data = response.json()
    tweet_id = tweet_data['data']['id']  # Get the tweet ID for the reply

    # Step 3: Reply with the description
    reply_payload = {
        "text": description,
        "reply": {
            "in_reply_to_tweet_id": tweet_id  # Specify the tweet ID you're replying to
        }
    }

    response = oauth.post(tweet_url_v2, json=reply_payload)

    if response.status_code != 201:
        raise Exception("Request returned an error when replying to tweet: {} {}".format(response.status_code, response.text))

    print("Description replied successfully.")
    
    return tweet_id

def process_entries_in_db():
    """Check the database for videos to upload to Twitter."""
    db = sqlite3.connect(DATABASE_PATH)
    cursor = db.cursor()

    # Query for entries where generatedThumbnailPath are not null
    cursor.execute(""" 
        SELECT id, title, description, generatedThumbnailPath, youtubeVideoId 
        FROM entries 
        WHERE generatedThumbnailPath IS NOT NULL 
        AND uploadedToX = 0
        AND uploadedToYoutube > 0
        AND uploadedToYoutube < ? 
    """, (int(time.time() * 1000) - 600000,))  # 10 minutes in millisecond

    entries = cursor.fetchall()

    # Post to X (after all uploads are complete)
    for entry in entries:
        entry_id, title, description, thumbnail_path, youtubeVideoId = entry

        # Post to X
        youtube_link = f" https://www.youtube.com/watch?v={youtubeVideoId}" if youtubeVideoId else ""
        logging.info(f"Entry {youtubeVideoId} YT Link")
        tweet_id = post_to_x(title, thumbnail_path, str(description + youtube_link))


        # Mark the entry as posted to X
        current_timestamp_ms = int(time.time() * 1000)
        cursor.execute("UPDATE entries SET uploadedToX = ?, tweetId = ? WHERE id = ?", (current_timestamp_ms, tweet_id, entry_id,))
        db.commit()
        logging.info(f"Entry {entry_id} marked as posted to X.")

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