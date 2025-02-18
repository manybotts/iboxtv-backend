import re
import os
import asyncio
import requests
from telethon import TelegramClient
from telethon.sessions import MemorySession
from telethon.errors.rpcerrorlist import RPCError

# Retrieve environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_ID = int(os.getenv("TELEGRAM_API_ID", 0))
API_HASH = os.getenv("TELEGRAM_API_HASH")
# Use TELEGRAM_GROUP if provided; otherwise, fallback to TELEGRAM_CHANNEL.
TARGET = os.getenv("TELEGRAM_GROUP") or os.getenv("TELEGRAM_CHANNEL")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

if not BOT_TOKEN or not API_ID or not API_HASH or not TARGET or not OMDB_API_KEY:
    raise ValueError("Please set TELEGRAM_BOT_TOKEN, TELEGRAM_API_ID, TELEGRAM_API_HASH, and TELEGRAM_GROUP (or TELEGRAM_CHANNEL), and OMDB_API_KEY.")

# Initialize the Telegram client using an in-memory session.
client = TelegramClient(MemorySession(), API_ID, API_HASH)

async def fetch_messages(limit: int = 10):
    """
    Starts the client in bot mode, fetches the target entity, and retrieves messages.
    """
    await client.start(bot_token=BOT_TOKEN)
    try:
        target_entity = await client.get_entity(TARGET)
        messages = await client.get_messages(target_entity, limit=limit)
        return messages
    except RPCError as e:
        print(f"Error fetching messages: {e}")
        return []
    finally:
        await client.disconnect()

def fetch_omdb_data(title: str) -> dict:
    """
    Calls the OMDb API to retrieve additional show data (poster and description)
    using the provided show title.
    """
    try:
        url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={title}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get("Response") == "True":
                return {"poster": data.get("Poster", ""), "description": data.get("Plot", "")}
    except Exception as e:
        print("OMDb API error:", e)
    return {"poster": "", "description": ""}

def parse_message(message) -> dict:
    """
    Expects the Telegram message caption to have at least three non-empty lines:
      - Line 1: Show Name
      - Line 2: Season and Episode info (e.g., "Season 23 Episode 1")
      - Line 3: Contains "CLICK HERE" with an embedded URL for downloads.
    
    Returns a dictionary with:
      - title: The show name (from line 1)
      - season_episode: The season/episode info (from line 2)
      - download_link: The URL extracted from line 3 (following "CLICK HERE")
      - poster: Poster URL from OMDb API using the show title
      - description: Plot description from OMDb API using the show title
      - popularity: Defaults to 0
    """
    if not message.text:
        return None

    # Split the text into non-empty lines.
    lines = [line.strip() for line in message.text.split("\n") if line.strip()]
    if len(lines) < 3:
        return None

    show_title = lines[0]
    season_episode = lines[1]

    # Look for "CLICK HERE" followed by a URL in the third line.
    url_match = re.search(r'CLICK\s+HERE.*?(https?://\S+)', lines[2], re.IGNORECASE)
    download_link = url_match.group(1) if url_match else ""
    omdb_data = fetch_omdb_data(show_title)

    return {
        "title": show_title,
        "season_episode": season_episode,
        "download_link": download_link,
        "poster": omdb_data.get("poster", ""),
        "description": omdb_data.get("description", ""),
        "popularity": 0
    }

async def fetch_latest_shows(limit: int = 10) -> list:
    """
    Asynchronously fetches messages from the target Telegram group/channel,
    filters them by chat username, parses them, and returns a list of show dictionaries.
    """
    messages = await fetch_messages(limit=limit)
    shows = []
    target_username = TARGET.lstrip('@').lower()
    for msg in messages:
        if msg.chat and msg.chat.username and msg.chat.username.lower() == target_username:
            parsed = parse_message(msg)
            if parsed:
                shows.append(parsed)
        if len(shows) >= limit:
            break
    return shows
