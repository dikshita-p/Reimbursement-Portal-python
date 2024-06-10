from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import db_config

engine = create_engine(db_config)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_session():
    return SessionLocal()
