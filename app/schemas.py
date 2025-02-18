from pydantic import BaseModel

class Show(BaseModel):
    id: str = None
    title: str
    season_episode: str
    download_link: str
    poster: str
    description: str
    popularity: int = 0

    model_config = {
        "from_attributes": True  # For Pydantic v2; use "orm_mode": True for v1.
    }
