import re
import os
import asyncio
import requests
from telethon import TelegramClient
from telethon.sessions import MemorySession

# Retrieve credentials and channel info from environment variables
API_ID = int(os.getenv("TELEGRAM_API_ID", 0))
API_HASH = os.getenv("TELEGRAM_API_HASH")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL = os.getenv("TELEGRAM_CHANNEL")  # e.g., "@iBOXTVChannel"
OMDB_API_KEY = os.getenv("OMDB_API_KEY")  # Your OMDb API key

if not API_ID or not API_HASH or not BOT_TOKEN or not CHANNEL or not OMDB_API_KEY:
    raise ValueError("Please set TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL, and OMDB_API_KEY environment variables.")

# Initialize the Telegram client using MemorySession (avoiding SQLite file locking)
client = TelegramClient(MemorySession(), API_ID, API_HASH)

async def fetch_messages(limit=10):
    await client.start(bot_token=BOT_TOKEN)
    try:
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
    Parses a Telegram message caption with the following structure:

      Line 1: Show Name
      Line 2: Season and Episode info (e.g., "Season 23 Episode 1")
      Line 3: Contains the text "CLICK HERE" with an embedded URL (not in parentheses but within the text)

    Returns a dictionary with:
      - title: The show name from line 1.
      - season_episode: The season/episode info from line 2.
      - download_link: The URL extracted from the third line.
      - poster: Poster URL fetched from OMDb API using the show title.
      - description: Show description (Plot) from OMDb API.
      - popularity: Defaulted to 0.
    """
    if not message.text:
        return None

    # Split message text into non-empty lines
    lines = [line.strip() for line in message.text.split("\n") if line.strip()]
    if len(lines) < 3:
        return None

    show_title = lines[0]
    season_episode = lines[1]

    # Extract URL from the third line by looking for "CLICK HERE" followed by a URL.
    # For example, the third line might be: "CLICK HERE ✔️ https://t.me/somechannel"
    url_match = re.search(r'CLICK\s+HERE.*?(https?://\S+)', lines[2], re.IGNORECASE)
    download_link = url_match.group(1) if url_match else ""

    # Enrich data from OMDb API using the show title
    omdb_data = fetch_omdb_data(show_title)

    return {
        "title": show_title,
        "season_episode": season_episode,
        "download_link": download_link,
        "poster": omdb_data.get("poster", ""),
        "description": omdb_data.get("description", ""),
        "popularity": 0  # Default popularity; adjust if needed
    }

async def fetch_latest_shows(limit=10):
    """
    Asynchronously fetches the latest messages from the Telegram channel,
    parses them, and returns a list of show dictionaries.
    """
    try:
        messages = await fetch_messages(limit=limit)
    except Exception as e:
        print(f"Error fetching messages: {e}")
        return []
    
    shows = []
    for msg in messages:
        parsed = parse_message(msg)
        if parsed:
            shows.append(parsed)
    return shows
