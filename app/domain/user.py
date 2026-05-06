from pydantic import BaseModel, Field


class User(BaseModel):
    """User (student) model."""

    id: str = Field(serialization_alias="_id") # uuid v7

    telegram_id: int

    is_verified: bool = False
