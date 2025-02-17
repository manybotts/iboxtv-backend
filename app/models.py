from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class Show(Base):
    __tablename__ = "shows"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    download_link = Column(String, nullable=False)
    is_streamable = Column(Boolean, default=False)
    popularity = Column(Integer, default=0)
