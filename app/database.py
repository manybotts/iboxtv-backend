import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Retrieve DATABASE_URL from the environment; if not set, use a local default.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/iboxtv_db")

# Replace "postgres://" with "postgresql://" if necessary.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
