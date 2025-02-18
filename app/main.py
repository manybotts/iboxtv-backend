import logging
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from . import models, schemas, telegram_scraper

# Create database tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="iBOX TV API (Firebase)")
logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper function to insert a show if it doesn't exist (case-insensitive check)
def insert_show_if_not_exists(db: Session, show_data):
    existing = db.query(models.Show).filter(models.Show.title.ilike(show_data["title"])).first()
    if not existing:
        new_show = models.Show(
            title=show_data["title"],
            download_link=show_data["download_link"],
            is_streamable=show_data.get("is_streamable", False),
            popularity=show_data.get("popularity", 0)
        )
        db.add(new_show)
        try:
            db.commit()
            db.refresh(new_show)
            return True
        except Exception as e:
            db.rollback()
            logger.error("Error inserting show %s: %s", show_data["title"], e)
    return False

@app.on_event("startup")
async def populate_db():
    logger.info("Startup: Checking if the database has TV show data.")
    db = next(get_db())
    if db.query(models.Show).count() == 0:
        new_shows = await telegram_scraper.fetch_latest_shows(limit=10)
        for show in new_shows:
            insert_show_if_not_exists(db, show)
        logger.info("Database population complete.")
    else:
        logger.info("Database already contains data; skipping population.")

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the iBOX TV API (Firebase)"}

@app.get("/fetch", tags=["Shows"])
async def fetch_shows(db: Session = Depends(get_db)):
    new_shows_data = await telegram_scraper.fetch_latest_shows(limit=10)
    inserted_shows = []
    for show_data in new_shows_data:
        if insert_show_if_not_exists(db, show_data):
            inserted_shows.append(show_data["title"])
    return {"message": f"Fetched and inserted {len(inserted_shows)} new shows", "shows": inserted_shows}

@app.get("/shows", response_model=list[schemas.Show], tags=["Shows"])
async def list_shows(db: Session = Depends(get_db)):
    shows = db.query(models.Show).all()
    return shows

@app.get("/trending", response_model=list[schemas.Show], tags=["Shows"])
async def trending_shows(db: Session = Depends(get_db)):
    trending = db.query(models.Show).order_by(models.Show.popularity.desc()).limit(10).all()
    return trending

@app.get("/stream-status/{show_id}", tags=["Shows"])
async def stream_status(show_id: int, db: Session = Depends(get_db)):
    show = db.query(models.Show).filter(models.Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    return {"downloadable": bool(show.download_link), "streamable": False}
