# config_schemas/schemas/backup_info_schema.py
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


class BackupInfoSchema(BaseModel):
    """
    Schema for backup information configuration.
    This schema defines the structure for backup information settings
    used in the backup or restoration process.
    """

    backup_type: Literal["backy", "sql"] = Field(
        default="sql", description="Type of backup to perform.", example="sql"
    )
    backup_description: str = Field(
        default="",
        description="Description of the backup.",
        example="Daily backup of the database.",
    )
    expiry_date: Optional[datetime] = Field(
        default=None,
        description="Expiry date for the backup.",
        example="2023-12-31T23:59:59",
    )
