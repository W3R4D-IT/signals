from sqlmodel import Session, create_engine, select
from core.config import settings


class DatabaseClient:
    def __init__(self):
        """Initialize the database engine and session maker."""

        self.engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
        
        with Session(self.engine) as session:
            self.Session = session

    def get_session(self):
        """Provide a new session."""
        return self.Session()

    def get_engine(self):
        """Return the database engine."""
        return self.engine
