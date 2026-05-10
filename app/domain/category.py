from pydantic import BaseModel, Field


class Category(BaseModel):
    """Category model for eventts."""

    id: str = Field(serialization_alias="_id") # uuid v7

    name: str
