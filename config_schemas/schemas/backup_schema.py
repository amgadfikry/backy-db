# config_schemas/schemas/backup_schema.py
from pydantic import BaseModel, Field, model_validator
from config_schemas.schemas.backup_info_schema import BackupInfoSchema
from config_schemas.schemas.database_schema import DatabaseSchema
from config_schemas.schemas.compression_schema import CompressionSchema
from config_schemas.schemas.security_schema import SecuritySchema
from config_schemas.schemas.storage_schema import StorageSchema
from config_schemas.schemas.integrity_schema import IntegritySchema


class BackupSchema(BaseModel):
    """
    Schema for backup configuration.
    This schema defines the structure for backup settings
    used in the backup or restoration process.
    """

    backup: BackupInfoSchema = Field(
        default_factory=BackupInfoSchema,
        description="Basic information about the backup.",
    )
    database: DatabaseSchema = Field(
        default_factory=DatabaseSchema,
        description="Database configuration for the backup.",
    )
    compression: CompressionSchema = Field(
        default_factory=CompressionSchema,
        description="Compression settings for the backup.",
    )
    security: SecuritySchema = Field(
        default_factory=SecuritySchema, description="Security settings for the backup."
    )
    integrity: IntegritySchema = Field(
        default_factory=IntegritySchema,
        description="Integrity settings for the backup.",
    )
    storage: StorageSchema

    @model_validator(mode="after")
    def validate_backup_schema(self) -> "BackupSchema":
        """
        Validate the BackupSchema after initialization.
        This method checks the backup type and adjusts the schema accordingly.
        """
        # Add the backup_type according to if there is encryption or compression
        # make the backup.backup_type according to the compression and security
        if self.compression.compression or self.security.encryption:
            self.backup.backup_type = "backy"
            self.database.restore_mode = "backy"
        else:
            self.backup.backup_type = "sql"
            self.database.restore_mode = "sql"

        return self
