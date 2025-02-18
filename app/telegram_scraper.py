import re
import os
import requests
from telegram import Bot, Update
from telegram.error import TelegramError

# Retrieve environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
# Use TELEGRAM_GROUP if provided; otherwise, fall back to TELEGRAM_CHANNEL.
TARGET = os.getenv("TELEGRAM_GROUP") or os.getenv("TELEGRAM_CHANNEL")

if not BOT_TOKEN or not OMDB_API_KEY or not TARGET:
    raise ValueError("Please set TELEGRAM_BOT_TOKEN, OMDB_API_KEY, and TELEGRAM_GROUP or TELEGRAM_CHANNEL environment variables.")

# Initialize the bot
bot = Bot(token=BOT_TOKEN)

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

def parse_message(message: Update) -> dict:
    """
    Expects the Telegram message caption to have at least three non-empty lines:
      - Line 1: Show Name
      - Line 2: Season and Episode info (e.g., "Season 23 Episode 1")
      - Line 3: Contains "CLICK HERE" with an embedded URL for downloads.
    
    Returns a dictionary with:
      - title: (from line 1)
      - season_episode: (from line 2)
      - download_link: URL extracted from line 3 (following "CLICK HERE")
      - poster: Poster URL fetched from OMDb API using the show title
      - description: Show description (Plot) from OMDb API using the show title
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
    Asynchronously fetches updates from the bot and returns a list of show dictionaries.
    Here, we explicitly request updates of type "channel_post" so that the bot receives posts from the channel.
    """
    try:
        # Await the get_updates call, requesting channel_post updates.
        updates = await bot.get_updates(timeout=10, allowed_updates=["channel_post"])
    except TelegramError as e:
        print(f"Error fetching updates: {e}")
        return []
    
    shows = []
    # TARGET might include an '@', so remove it for comparison.
    target_username = TARGET.lstrip('@')
    for update in updates:
        # For channel posts, the update.message is present and update.channel_post may be used;
        # however, many bots receive channel posts in update.message.
        if update.message and update.message.chat.username == target_username:
            parsed = parse_message(update.message)
            if parsed:
                shows.append(parsed)
        if len(shows) >= limit:
            break
    return shows
