import re
import os
import requests
import asyncio
from telegram import Bot, Update
from telegram.error import TelegramError

# Retrieve environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
# Use TELEGRAM_GROUP if provided; otherwise, fallback to TELEGRAM_CHANNEL.
TARGET = os.getenv("TELEGRAM_GROUP") or os.getenv("TELEGRAM_CHANNEL")

if not BOT_TOKEN or not OMDB_API_KEY or not TARGET:
    raise ValueError("Please set TELEGRAM_BOT_TOKEN, OMDB_API_KEY, and TELEGRAM_GROUP or TELEGRAM_CHANNEL environment variables.")

# Initialize the bot
bot = Bot(token=BOT_TOKEN)

def fetch_omdb_data(title: str) -> dict:
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

def parse_message(message: Update) -> dict:
    if not message.text:
        return None

    # Split the message text into non-empty lines.
    lines = [line.strip() for line in message.text.split("\n") if line.strip()]
    if len(lines) < 3:
        return None

    show_title = lines[0]
    season_episode = lines[1]

    # Extract the download URL from the third line.
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

def fetch_latest_shows(limit: int = 10) -> list:
    """
    Synchronously fetches updates from the bot and returns a list of show dictionaries.
    We filter updates whose message chat username matches TARGET (without the '@').
    """
    try:
        updates = bot.get_updates()
    except TelegramError as e:
        print(f"Error fetching updates: {e}")
        return []
    
    shows = []
    target_username = TARGET.lstrip('@')
    for update in updates:
        if update.message and update.message.chat.username == target_username:
            parsed = parse_message(update.message)
            if parsed:
                shows.append(parsed)
            if len(shows) >= limit:
                break
    return shows

# Provide an async wrapper so that FastAPI endpoints can await fetching shows.
async def async_fetch_latest_shows(limit: int = 10) -> list:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, fetch_latest_shows, limit)
