import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

#we try to get the database url from the environment variables first
#if there is no env var we use the default recipes.sqlite
DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///recipes.sqlite"

engine = create_engine(url=DATABASE_URL, echo=True)


#SQLite does not check foreign keys by default.
#We turn them on for every new connection, so that ON DELETE CASCADE / SET NULL / RESTRICT work.
#SQLite's lower() works only with latin letters, so we replace it with python's str.lower()
#to get case-insensitive comparison for cyrillic names too.
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
    dbapi_connection.create_function(
        "lower", 1, lambda value: value.lower() if value is not None else None)


SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

#get_db is a generator to create new ORM session used in the context of new request
#it works as a Dependency injection into the endpoints
def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()