from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base

class Show(Base):
    __tablename__ = "shows"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False, unique=True)  # Unique constraint to prevent duplicates
    download_link = Column(String, nullable=False)
    is_streamable = Column(Boolean, default=False)
    popularity = Column(Integer, default=0)
