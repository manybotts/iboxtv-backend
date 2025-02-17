import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Use the DATABASE_URL environment variable if set; otherwise, default to a local PostgreSQL connection.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/iboxtv_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
