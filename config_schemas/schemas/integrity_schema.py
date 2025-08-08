# config_schemas/schemas/integrity_schema.py
from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional
from logger.logger_manager import LoggerManager


class IntegritySchema(BaseModel):
    """
    Schema for integrity settings.
    This schema defines the structure for integrity settings
    used in the backup or restoration process.
    """

    integrity_check: bool = Field(
        default=False, description="If True, integrity check will be performed."
    )
    integrity_type: Optional[Literal["checksum", "hmac"]] = Field(
        default=None, description="Type of integrity check to perform."
    )

    @model_validator(mode="after")
    def validate_integrity_type(self) -> "IntegritySchema":
        """
        Validates the integrity_type if integrity_check is enabled.
        If integrity_check is enabled but integrity_type is None,
        raises a ValueError.
        """
        logger = LoggerManager.setup_logger("schema")

        if self.integrity_check and self.integrity_type is None:
            logger.error(
                "integrity_type must be specified when integrity_check is enabled."
            )
            raise ValueError(
                "integrity_type must be specified when integrity_check is enabled."
            )
        return self
