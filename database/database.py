from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from settings.settings import Settings

settings = Settings()

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {},
)


def get_session() -> Session:
    return Session(engine)