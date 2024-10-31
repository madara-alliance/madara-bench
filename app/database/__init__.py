from typing import Any, Generator

import sqlmodel

from . import models

postgres_url = "postgresql://postgres:password@localhost:5432/postgres"
engine = sqlmodel.create_engine(postgres_url, echo=True)


def init_db_and_tables():
    sqlmodel.SQLModel.metadata.create_all(engine)


def session() -> Generator[sqlmodel.Session, Any, Any]:
    with sqlmodel.Session(engine) as session:
        yield session
