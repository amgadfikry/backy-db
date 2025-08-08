# config_schemas/schemas/storage_schema.py
from pydantic import BaseModel, Field
from typing import Literal


class StorageSchema(BaseModel):
    """
    Schema for storage settings.
    This schema defines the structure for storage settings
    used in the backup or restoration process.
    """

    storage_type: Literal["local", "aws"] = Field(
        ..., description="Type of storage system."
    )
