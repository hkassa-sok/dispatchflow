import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, session
from app.models import Customer, Merchant, Driver
from app.main import app

@pytest.fixture
def client(tmp_path):
    url = os.getenv("TEST_DATABASE_URL", "sqlite:///" + str(tmp_path / "test.db"))
    if os.getenv("TEST_DATABASE_URL") and not url.split("?")[0].endswith("_test"):
        raise pytest.UsageError("TEST_DATABASE_URL must name a dedicated database ending in _test")
    engine = create_engine(url, connect_args={"check_same_thread":False,"timeout":20} if url.startswith("sqlite") else {})
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as db:
        db.add_all([Customer(id=1,name="Alex"), Merchant(id=1,name="Kitchen",lat=40.72,lng=-74)])
        db.flush()
        db.add_all([Driver(id=1,name="Maya",lat=40.72,lng=-74),Driver(id=2,name="Sam",lat=40.73,lng=-74)])
        db.commit()
    def override():
        with factory() as db:
            yield db
    app.dependency_overrides[session] = override
    # No lifespan: tests explicitly own schema and data; no Redis needed.
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()
