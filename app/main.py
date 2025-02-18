import logging
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import SessionLocal, engine
from app.telegram_scraper import fetch_latest_shows

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="iBOX TV API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def populate_db():
    logger.info("Startup event: Checking database for existing shows...")
    db = SessionLocal()
    try:
        count = db.query(models.Show).count()
        logger.info(f"Current show count: {count}")
        if count == 0:
            new_shows_data = await fetch_latest_shows()
            inserted_shows = 0
            for show_data in new_shows_data:
                # Use ilike for case-insensitive comparison
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
                        inserted_shows += 1
                        logger.info("Inserted show: %s", new_show.title)
                    except Exception as e:
                        db.rollback()
                        logger.error("Error inserting show %s: %s", show_data["title"], e)
            logger.info("Startup event: Inserted %d new shows", inserted_shows)
        else:
            logger.info("Startup event: Database already populated")
    except Exception as e:
        logger.error("Error during startup population: %s", e)
    finally:
        db.close()

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the iBOX TV API"}

@app.get("/fetch", tags=["Shows"])
async def fetch_shows(db: Session = Depends(get_db)):
    new_shows_data = await fetch_latest_shows()
    inserted_shows = []
    for show_data in new_shows_data:
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
                inserted_shows.append(new_show)
                logger.info("Inserted show via /fetch: %s", new_show.title)
            except Exception as e:
                db.rollback()
                logger.error("Error inserting show %s: %s", show_data["title"], e)
    return {
        "message": f"Fetched and inserted {len(inserted_shows)} new shows",
        "shows": [show.title for show in inserted_shows]
    }

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
    return {"streamable": show.is_streamable}
