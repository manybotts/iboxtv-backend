import re
import os
import requests
from telegram import Bot
from telegram.ext import Application, CommandHandler
from telegram.error import TelegramError

# Retrieve your credentials and bot token from environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
CHANNEL = os.getenv("TELEGRAM_CHANNEL")  # The channel or group to fetch from

if not BOT_TOKEN or not OMDB_API_KEY or not CHANNEL:
    raise ValueError("Please set TELEGRAM_BOT_TOKEN, OMDB_API_KEY, and TELEGRAM_CHANNEL environment variables.")

# Initialize the bot with python-telegram-bot
bot = Bot(token=BOT_TOKEN)

def fetch_omdb_data(title):
    """
    Calls the OMDb API to retrieve additional show data (poster and description) using the show title.
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
      Line 3: Contains the text "CLICK HERE" with an embedded URL for downloads.
    
    Returns a dictionary with:
      - title: The show name from line 1.
      - season_episode: The season/episode info from line 2.
      - download_link: The URL extracted from the text in line 3.
      - poster: Poster URL fetched from OMDb API using the show title.
      - description: Show description (Plot) from OMDb API.
      - popularity: Defaulted to 0.
    """
    if not message:
        return None

    # Split the message text into non-empty lines
    lines = [line.strip() for line in message.text.split("\n") if line.strip()]
    if len(lines) < 3:
        return None

    show_title = lines[0]
    season_episode = lines[1]

    # Extract URL from the third line: look for "CLICK HERE" followed by a URL.
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

def fetch_messages_from_channel():
    """
    Fetches the latest messages from the specified channel using the bot.
    """
    try:
        updates = bot.get_updates()
        shows = []
        for update in updates:
            message = update.message
            if message and message.chat.username == CHANNEL:
                parsed_message = parse_message(message)
                if parsed_message:
                    shows.append(parsed_message)
        return shows
    except TelegramError as e:
        print(f"Error fetching messages: {e}")
        return []

def start(update, context):
    """
    Command handler for the '/start' command to test bot functionality.
    """
    update.message.reply_text("Bot is online. Use /fetch to fetch shows!")

def fetch(update, context):
    """
    Command handler for the '/fetch' command to fetch the latest shows.
    """
    shows = fetch_messages_from_channel()
    if shows:
        message = "Fetched the following shows:\n"
        for show in shows:
            message += f"{show['title']} ({show['season_episode']})\n"
        update.message.reply_text(message)
    else:
        update.message.reply_text("No shows found.")

def main():
    """
    Initializes the bot and starts fetching the shows.
    """
    # Initialize the application using the correct method
    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("fetch", fetch))

    # Start polling for new messages
    application.run_polling()

if __name__ == "__main__":
    main()
