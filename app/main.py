from fastapi import FastAPI, HTTPException
from app.firebase_db import db
from app.telegram_scraper import fetch_latest_shows
from app.models import Show
import logging

app = FastAPI(title="iBOX TV API (Firebase)")
logger = logging.getLogger(__name__)

# Firebase helper functions

def get_all_shows():
    shows_ref = db.collection("shows")
    docs = shows_ref.stream()
    shows = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        shows.append(data)
    return shows

def insert_show_if_not_exists(show_data: dict) -> bool:
    # Check if a show with the same title exists (exact match).
    query = db.collection("shows").where("title", "==", show_data["title"]).get()
    if query:
        return False  # Show exists already.
    db.collection("shows").add(show_data)
    return True

def get_trending_shows(limit: int = 10):
    shows_ref = db.collection("shows").order_by("popularity", direction="DESCENDING").limit(limit)
    docs = shows_ref.stream()
    trending = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        trending.append(data)
    return trending

def get_show_by_id(show_id: str):
    doc = db.collection("shows").document(show_id).get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    return None

@app.on_event("startup")
async def populate_db():
    logger.info("Startup: Checking if Firestore has TV show data.")
    if not get_all_shows():
        new_shows = await fetch_latest_shows(limit=10)
        for show in new_shows:
            if insert_show_if_not_exists(show):
                logger.info("Inserted show: %s", show["title"])
        logger.info("Database population complete.")
    else:
        logger.info("Database already contains data; skipping population.")

@app.get("/")
async def root():
    return {"message": "Welcome to the iBOX TV API (Firebase)"}

@app.get("/fetch")
async def fetch_shows():
    try:
        shows = await fetch_latest_shows(limit=10)
        inserted_shows = []
        for show in shows:
            if insert_show_if_not_exists(show):
                inserted_shows.append(show["title"])
        return {"message": f"Fetched and inserted {len(inserted_shows)} new shows", "shows": inserted_shows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/shows")
async def list_shows():
    return get_all_shows()

@app.get("/trending")
async def trending_shows():
    return get_trending_shows(limit=10)

@app.get("/stream-status/{show_id}")
async def stream_status(show_id: str):
    show = get_show_by_id(show_id)
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    return {"downloadable": bool(show.get("download_link")), "streamable": False}
