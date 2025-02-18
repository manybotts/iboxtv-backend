import re
import os
import asyncio
import requests
from telethon import TelegramClient

# Retrieve your Telegram API credentials, channel info, and (optionally) a session string from environment variables
API_ID = int(os.getenv("TELEGRAM_API_ID", 0))
API_HASH = os.getenv("TELEGRAM_API_HASH")
CHANNEL = os.getenv("TELEGRAM_CHANNEL")  # e.g., "@iBOXTVChannel"
OMDB_API_KEY = os.getenv("OMDB_API_KEY")   # Your OMDb API key
SESSION_STRING = os.getenv("TELEGRAM_SESSION_STRING", "")

if not API_ID or not API_HASH or not CHANNEL or not OMDB_API_KEY:
    raise ValueError("Please set TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_CHANNEL, and OMDB_API_KEY environment variables.")

# Attempt to create a client using the session string if available and supported; otherwise, create a new session.
try:
    if SESSION_STRING and hasattr(TelegramClient, "from_session_string"):
        client = TelegramClient.from_session_string(SESSION_STRING, API_ID, API_HASH)
    else:
        client = TelegramClient('iboxtv_session', API_ID, API_HASH)
except Exception as e:
    print("Error initializing TelegramClient from session string:", e)
    client = TelegramClient('iboxtv_session', API_ID, API_HASH)

async def fetch_messages(limit=10):
    await client.start()
    try:
        # Get the channel entity and fetch the latest messages
        channel_entity = await client.get_entity(CHANNEL)
        messages = await client.get_messages(channel_entity, limit=limit)
        return messages
    finally:
        await client.disconnect()

def fetch_omdb_data(title):
    """
    Calls the OMDb API to get additional show data (poster and description) using the show title.
    """
    try:
        url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={title}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get("Response") == "True":
                return {
                    "poster": data.get("Poster", ""),
                    "description": data.get("Plot", "")
                }
    except Exception as e:
        print("OMDb API error:", e)
    return {"poster": "", "description": ""}

def parse_message(message):
    """
    Parses a Telegram message caption with the following general structure:

      Line 1: Show Name
      Line 2: Season and Episode info (e.g., "Season 23 Episode 1")
      Line 3: Contains text like "CLICK HERE" with an embedded URL for downloads.

    Returns a dictionary with:
      - title: The show name from line 1.
      - season_episode: The season/episode info from line 2.
      - download_link: The URL extracted from the text in line 3.
      - poster: Poster URL fetched from OMDb API using the show title.
      - description: Show description (Plot) from OMDb API.
      - popularity: Defaulted to 0.
    """
    if not message.text:
        return None

    # Split the message text into non-empty lines
    lines = [line.strip() for line in message.text.split("\n") if line.strip()]
    if len(lines) < 3:
        return None

    # Extract data from the lines
    show_title = lines[0]
    season_episode = lines[1]

    # Extract URL from the third line: search for "CLICK HERE" followed by a URL
    url_match = re.search(r'CLICK\s+HERE.*?(https?://\S+)', lines[2], re.IGNORECASE)
    download_link = url_match.group(1) if url_match else ""

    # Fetch additional details from the OMDb API using the show title
    omdb_data = fetch_omdb_data(show_title)

    return {
        "title": show_title,
        "season_episode": season_episode,
        "download_link": download_link,
        "poster": omdb_data.get("poster", ""),
        "description": omdb_data.get("description", ""),
        "popularity": 0  # Adjust if needed
    }

def fetch_latest_shows(limit=10):
    """
    Synchronously fetches the latest messages from the specified Telegram channel,
    parses them, and returns a list of show dictionaries.
    """
    try:
        messages = asyncio.run(fetch_messages(limit=limit))
    except Exception as e:
        print(f"Error fetching messages: {e}")
        return []
    
    shows = []
    for msg in messages:
        parsed = parse_message(msg)
        if parsed:
            shows.append(parsed)
    return shows
