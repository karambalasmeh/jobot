from typing import Generator
from app.core.database import SessionLocal

def get_db() -> Generator:
    """
    Dependency Injection function to get a database session.
    It ensures the database connection is closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()