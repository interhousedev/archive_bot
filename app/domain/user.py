from pydantic import BaseModel, Field


class User(BaseModel):
    """User (student) model."""

    id: str = Field(serialization_alias="_id") # uuid v7

    telegram_id: int

    # By student
    is_verified: bool = False
    # By admins
    is_banned: bool = False
