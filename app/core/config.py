import secrets
import os
from typing import Literal
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import (
    PostgresDsn,
    computed_field,
)
from pydantic_core import MultiHostUrl

load_dotenv(override=True, dotenv_path=".env")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ENCRYPTION_KEY: str = secrets.token_urlsafe(32)
    
    PROJECT_NAME: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""
    
    BROKER_HOSTNAME: str
    BROKER_PORT: int
    BROKER_USERNAME: str
    BROKER_PASSWORD: str
    VIRTUAL_HOST: str
    USE_SSL: bool = False
    EXCHANGE_TYPE: str
    DURABLE: bool
    CONTENT_TYPE: str
    CONTENT_ENCODING: str
    DELIVERY_MODE: int
    ACCEPT_CONTENT: str
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg2",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )



settings = Settings()  # type: ignore