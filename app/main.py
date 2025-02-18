@app.get("/fetch", tags=["Shows"])
async def fetch_shows(db: Session = Depends(get_db)):
    new_shows_data = await telegram_scraper.fetch_latest_shows(limit=10)
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
            except Exception as e:
                db.rollback()
                print(f"Error inserting show {show_data['title']}: {e}")
    return {"message": f"Fetched and inserted {len(inserted_shows)} new shows", "shows": [show.title for show in inserted_shows]}
