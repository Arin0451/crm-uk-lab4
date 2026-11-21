import os
from pathlib import Path

from sqlalchemy import URL, Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def database_url() -> URL:
    default_path = Path(__file__).resolve().parent.parent / "crm.db"
    path = Path(os.environ.get("CRM_DB_PATH", default_path)).resolve()
    return URL.create("sqlite", database=str(path))


def create_db_engine(url: URL | None = None) -> Engine:
    engine = create_engine(url if url is not None else database_url())

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys = ON")
        finally:
            cursor.close()

    return engine
