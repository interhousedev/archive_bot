from datetime import datetime

from pydantic import BaseModel, Field


class Event(BaseModel):
    """Event model with images."""

    id: str = Field(serialization_alias="_id") # uuid v7

    name: str

    description: str | None = None

    date: datetime

    images_folder: str # folder in s3 storage

    photos_count: int = 0
