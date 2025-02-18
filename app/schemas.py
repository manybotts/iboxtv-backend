from pydantic import BaseModel

class Show(BaseModel):
    id: int
    title: str
    download_link: str
    is_streamable: bool
    popularity: int

    model_config = {
        "from_attributes": True
    }
