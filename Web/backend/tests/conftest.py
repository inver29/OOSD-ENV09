import re
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from backend.app import domain
from backend.app.bootstrap import initialize
from backend.app.config import Settings
from backend.app.db import make_engine, session_factory
from backend.app.main import create_app
from backend.app.models import Asset, Base, User
from backend.app.seed import seed_demo


@pytest.fixture(scope="session")
def database(tmp_path_factory):
    name = "ENV09_Test_" + uuid4().hex
    config = Settings(
        db_name=name,
        demo_password=uuid4().hex,
        expiry_worker=False,
        storage_dir=tmp_path_factory.mktemp("env09_uploads"),
        frontend_dir=tmp_path_factory.mktemp("env09_no_frontend"),
    )
    engine = initialize(config)
    yield config, engine
    engine.dispose()
    # Only this fixture's newly generated database is eligible for cleanup.
    assert re.fullmatch(r"ENV09_Test_[a-f0-9]{32}", name)
    master = make_engine(config, database="master")
    try:
        with master.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.exec_driver_sql(
                f"ALTER DATABASE [{name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE"
            )
            connection.exec_driver_sql(f"DROP DATABASE [{name}]")
    finally:
        master.dispose()


@pytest.fixture
def env(database, monkeypatch):
    config, engine = database
    clock = [domain.now()]
    monkeypatch.setattr(domain, "now", lambda: clock[0])
    sessions = session_factory(engine)
    with sessions.begin() as db:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(delete(table))
        seed_demo(db, config, include_images=False)
    app = create_app(config, engine)
    clients = []

    def login(username):
        client = TestClient(app)
        response = client.post(
            "/api/auth/login",
            json={"username": username, "password": config.demo_password},
        )
        assert response.status_code == 200, response.text
        client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
        clients.append(client)
        return client

    with sessions() as db:
        assets = {x.name: x.id for x in db.scalars(select(Asset)).unique()}
        users = {x.username: x.id for x in db.scalars(select(User)).unique()}
    yield dict(
        app=app,
        sessions=sessions,
        login=login,
        clock=clock,
        assets=assets,
        users=users,
        config=config,
    )
    for client in clients:
        client.close()
