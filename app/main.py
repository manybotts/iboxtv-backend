from fastapi import FastAPI
from app.firebase_db import db  # Importing firebase_db (your Firebase database handler)
from app.telegram_scraper import fetch_latest_shows  # Correct import for fetching Telegram data
from app.models import Show  # Import the Show model for your database
import os

# Initialize the FastAPI app instance
app = FastAPI()  # Ensure 'app' is defined here

@app.on_event("startup")
async def populate_db():
    """
    Populate the Firebase database with the latest TV show data fetched from the Telegram channel/group.
    This function is triggered on application startup.
    """
    try:
        # Fetch the latest shows from the Telegram channel
        new_shows = await fetch_latest_shows(limit=10)

        # Ensure data is processed and added to the Firebase database
        if new_shows:
            for show in new_shows:
                # Assuming you have a Show model and Firebase db setup
                show_data = Show(
                    title=show['title'],
                    season_episode=show['season_episode'],
                    download_link=show['download_link'],
                    poster=show['poster'],
                    description=show['description'],
                    popularity=show['popularity']
                )
                # Add show to Firebase database
                db.collection("shows").add({
                    "title": show_data.title,
                    "season_episode": show_data.season_episode,
                    "download_link": show_data.download_link,
                    "poster": show_data.poster,
                    "description": show_data.description,
                    "popularity": show_data.popularity,
                })

        print(f"Successfully populated {len(new_shows)} shows into the database.")
    except Exception as e:
        print(f"Error in populating DB: {e}")

@app.get("/")
async def root():
    """
    Root endpoint to confirm that the API is working.
    """
    return {"message": "Welcome to the iBOX TV API"}

@app.get("/fetch")
async def fetch_shows():
    """
    Endpoint to manually fetch the latest shows.
    """
    try:
        # Fetch the latest shows from Telegram
        shows = await fetch_latest_shows(limit=10)
        return {"shows": shows}
    except Exception as e:
        return {"error": f"Failed to fetch shows: {str(e)}"}

# Add any other endpoints for additional functionality here
