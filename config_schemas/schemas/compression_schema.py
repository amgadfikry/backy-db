# config_schemas/schemas/compression_schema.py
from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional


class CompressionSchema(BaseModel):
    """
    Schema for compression settings.
    This schema defines the structure for compression settings
    used in the backup or restoration process.
    """

    compression: bool = Field(
        default=False, description="If True, backup will be compressed."
    )
    compression_type: Optional[Literal["zip", "tar"]] = Field(
        default=None, description="Type of compression to use."
    )

    @model_validator(mode="after")
    def validate_compression_type(self) -> "CompressionSchema":
        """
        Validates the compression_type if compression is enabled.
        If compression is enabled but compression_type is None,
        raises a ValueError.
        """
        if self.compression and self.compression_type is None:
            raise ValueError(
                "compression_type must be specified when compression is enabled."
            )
        return self
