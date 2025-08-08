# config_schemas/schemas/security_schema.py
from pydantic import BaseModel, Field, model_validator
from logger.logger_manager import LoggerManager
from typing import Literal, Optional


class SecuritySchema(BaseModel):
    """
    Schema for security settings.
    This schema defines the structure for security settings
    used in the backup or restoration process.
    """

    encryption: bool = Field(
        default=False, description="If True, backup will be encrypted."
    )
    type: Optional[Literal["kms", "keystore"]] = Field(
        default=None, description="Type of encryption to use."
    )
    provider: Optional[Literal["aws", "local", "gcp"]] = Field(
        default=None, description="Cloud provider for encryption."
    )
    key_size: Optional[Literal[4096, 2048]] = Field(
        default=None, description="Size of the encryption key in bits."
    )
    key_version: Optional[str] = Field(
        default=None, description="Version of the encryption key."
    )

    @model_validator(mode="after")
    def validate_type_with_provider(self) -> "SecuritySchema":
        """
        It validates that the type of encryption is compatible with the provider.
        If the type is 'kms', the provider must be 'aws'.
        If the type is 'keystore', the provider must be 'local' or 'gcp'.
        """
        logger = LoggerManager.setup_logger("schema")

        if self.encryption and not all([self.type, self.provider]):
            logger.error(
                "Both type and provider must be specified when encryption is enabled."
            )
            raise ValueError(
                "Both type and provider must be specified when encryption is enabled."
            )

        if self.type == "kms" and self.provider != "aws":
            logger.error("KMS type requires AWS provider.")
            raise ValueError("KMS type requires AWS provider.")
        elif self.type == "keystore" and self.provider not in ["local", "gcp"]:
            logger.error("Keystore type requires local or GCP provider.")
            raise ValueError("Keystore type requires local or GCP provider.")
        return self
