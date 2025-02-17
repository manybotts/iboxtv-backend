import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Retrieve DATABASE_URL from the environment; use a default for local development.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/iboxtv_db")

# Heroku Postgres typically provides a URL starting with 'postgres://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
