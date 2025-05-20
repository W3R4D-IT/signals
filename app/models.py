from datetime import datetime, datetime
from typing import Optional, Dict
from sqlalchemy import Column
from sqlmodel import SQLModel, Field, Relationship
from sqlmodel import JSON


class WebHookSecret(SQLModel, table=True):
    __tablename__ = "webhook_secrets"
    id: int = Field(default=None, primary_key=True, index=True)
    bot_id: int = Field(default=None)
    webhook_secret: str = Field(default="")


class Bot(SQLModel, table=True):
    __tablename__ = "bots"
    id: int = Field(default=None, primary_key=True, index=True)
    is_active: bool = Field(default=False)
    is_signal_encrypted: bool = Field(default=False)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)



class Channel(SQLModel, table=True):
    __tablename__ = "channels"
    id: int = Field(default=None, primary_key=True, index=True)
    name: str = Field(max_length=255, nullable=False)
    is_predefined_indicator: bool = Field(default=False)
    indicator_keywords_mapper: Optional[Dict[str, str]] = Field(default=None, sa_column=Column(JSON))
    bot_id: int = Field(nullable=False)

    # # Navigation property
    # bot: Optional["Bot"] = Relationship(back_populates="channels")
