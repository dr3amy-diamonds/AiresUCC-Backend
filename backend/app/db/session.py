from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# from app.core.config import settings # Luego importas tu config

# Reemplazar con settings.DATABASE_URL
SQLALCHEMY_DATABASE_URL = 'postgresql://user:password@localhost:5432/db_aires_ucc'

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()