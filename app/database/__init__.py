from typing import Any, Generator

import sqlmodel


class MessageBase(sqlmodel.SQLModel):
    message: str = sqlmodel.Field(index=True)


class MessageDb(MessageBase, table=True):
    id: int | None = sqlmodel.Field(None, primary_key=True)


class MessageInOut(MessageBase):
    message: str


timescale_url = "postgresql://postgres:password@localhost/postgres"
engine = sqlmodel.create_engine(timescale_url)


def init_db_and_tables():
    sqlmodel.SQLModel.metadata.create_all(engine)


def session() -> Generator[sqlmodel.Session, Any, Any]:
    with sqlmodel.Session(engine) as session:
        yield session
