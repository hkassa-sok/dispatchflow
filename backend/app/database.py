import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

URL = os.getenv("DATABASE_URL", "sqlite:///./dispatchflow.db")
engine = create_engine(URL, connect_args={"check_same_thread": False, "timeout": 20} if URL.startswith("sqlite") else {}, pool_pre_ping=True)
if URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def enable_fks(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
Session = sessionmaker(engine, expire_on_commit=False)
class Base(DeclarativeBase):
    pass

def session():
    with Session() as db:
        yield db
