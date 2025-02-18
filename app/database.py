import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Retrieve the DATABASE_URL environment variable. 
# This works for Heroku Postgres (which might use 'postgres://') or a local database.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/iboxtv_db")

# If the URL starts with 'postgres://', replace it with 'postgresql://' for SQLAlchemy compatibility.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
