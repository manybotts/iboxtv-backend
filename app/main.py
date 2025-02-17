from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import SessionLocal, engine
from telegram_scraper import fetch_latest_shows

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="iBOX TV API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the iBOX TV API"}

@app.get("/fetch", tags=["Shows"])
async def fetch_shows(db: Session = Depends(get_db)):
    new_shows_data = fetch_latest_shows()
    inserted_shows = []
    for show_data in new_shows_data:
        existing = db.query(models.Show).filter(models.Show.title == show_data["title"]).first()
        if not existing:
            new_show = models.Show(**show_data)
            db.add(new_show)
            db.commit()
            db.refresh(new_show)
            inserted_shows.append(new_show)
    return {"message": f"Inserted {len(inserted_shows)} new shows", "shows": [show.title for show in inserted_shows]}

@app.get("/shows", response_model=list[schemas.Show], tags=["Shows"])
async def list_shows(db: Session = Depends(get_db)):
    shows = db.query(models.Show).all()
    return shows

@app.get("/trending", response_model=list[schemas.Show], tags=["Shows"])
async def trending_shows(db: Session = Depends(get_db)):
    trending = db.query(models.Show).order_by(models.Show.popularity.desc()).limit(10).all()
    return trending

@app.get("/stream-status/{show_id}", response_model=schemas.Show, tags=["Shows"])
async def stream_status(show_id: int, db: Session = Depends(get_db)):
    show = db.query(models.Show).filter(models.Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    return show
