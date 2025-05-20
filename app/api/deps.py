from collections.abc import Generator
from sqlmodel import Session
from typing import Annotated
from fastapi import Depends

from core.db_client import DatabaseClient


db_client = DatabaseClient()


def get_db() -> Generator[Session, None, None]:
    with Session(db_client.get_engine()) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
