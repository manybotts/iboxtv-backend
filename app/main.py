import logging
from fastapi import FastAPI, HTTPException
from app.firebase_db import db
from app import telegram_scraper, schemas

app = FastAPI(title="iBOX TV API (Firebase)")
logger = logging.getLogger(__name__)

# Helper functions for Firestore operations

def get_all_shows():
    shows_ref = db.collection("shows")
    docs = shows_ref.stream()
    shows = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        shows.append(data)
    return shows

def insert_show_if_not_exists(show_data):
    # Check if a show with the same title exists (case-sensitive comparison)
    query = db.collection("shows").where("title", "==", show_data["title"]).get()
    if query:
        return False  # Show already exists
    # Insert the new show
    db.collection("shows").add(show_data)
    return True

def get_trending_shows(limit=10):
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
    logger.info("Startup: Checking if the database has TV show data.")
    if not get_all_shows():
        new_shows = await telegram_scraper.fetch_latest_shows(limit=10)
        for show in new_shows:
            inserted = insert_show_if_not_exists(show)
            if inserted:
                logger.info("Inserted show: %s", show["title"])
        logger.info("Database population complete.")
    else:
        logger.info("Database already contains data; skipping population.")

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the iBOX TV API (Firebase)"}

@app.get("/fetch", tags=["Shows"])
async def fetch_shows():
    new_shows = await telegram_scraper.fetch_latest_shows(limit=10)
    inserted_shows = []
    for show in new_shows:
        if insert_show_if_not_exists(show):
            inserted_shows.append(show["title"])
    return {"message": f"Fetched and inserted {len(inserted_shows)} new shows", "shows": inserted_shows}

@app.get("/shows", response_model=list[schemas.Show], tags=["Shows"])
async def list_shows():
    return get_all_shows()

@app.get("/trending", response_model=list[schemas.Show], tags=["Shows"])
async def trending_shows():
    return get_trending_shows(limit=10)

@app.get("/stream-status/{show_id}", tags=["Shows"])
async def stream_status(show_id: str):
    show = get_show_by_id(show_id)
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    # For now, only the download option is enabled.
    return {"downloadable": bool(show.get("download_link")), "streamable": False}
