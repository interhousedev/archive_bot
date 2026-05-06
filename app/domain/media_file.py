from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.file_type import FileType


class MediaFile(BaseModel):
    """Media file object."""

    id: str = Field(serialization_alias="_id") # uuid v7

    file_name: str
    event_id: str
    author_id: str

    type: FileType

    is_showed: bool = True
