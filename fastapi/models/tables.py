from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    created_at: Optional[str] = None


class Prediction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    text: str
    intent: str
    confidence: float
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    )
