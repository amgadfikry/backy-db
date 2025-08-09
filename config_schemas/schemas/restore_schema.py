# config_schemas/schemas/restore_schema.py
from pydantic import BaseModel, Field
from config_schemas.schemas.database_schema import DatabaseRestoreSchema
from config_schemas.schemas.storage_schema import StorageSchema


class RestoreSchema(BaseModel):
    """
    Schema for validating restore configurations.
    This schema defines the structure and types of the restore configuration.
    """

    database: DatabaseRestoreSchema = Field(
        default_factory=DatabaseRestoreSchema,
        description="Database configuration for the restore.",
    )
    backup_path: str = Field(
        ...,
        description="Path to the backup file or directory to restore from.",
    )
    storage: StorageSchema
