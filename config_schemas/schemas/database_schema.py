# config_schemas/schemas/database_schema.py
from pydantic import BaseModel, Field, model_validator
from typing import Literal
from logger.logger_manager import LoggerManager


class MySQLFeaturesSchema(BaseModel):
    """
    Schema for MySQL specific features.
    This schema defines the features that can be enabled or disabled
    for MySQL databases during backup or restoration.
    """

    tables: bool = Field(
        default=True,
        description="If True, backup will include tables.",
    )
    data: bool = Field(
        default=True,
        description="If True, backup will include data.",
    )
    views: bool = Field(
        default=False,
        description="If True, backup will include views.",
    )
    functions: bool = Field(
        default=False,
        description="If True, backup will include functions.",
    )
    procedures: bool = Field(
        default=False,
        description="If True, backup will include procedures.",
    )
    triggers: bool = Field(
        default=False,
        description="If True, backup will include triggers.",
    )
    events: bool = Field(
        default=False,
        description="If True, backup will include events.",
    )

    @model_validator(mode="after")
    def validate_features(self) -> "MySQLFeaturesSchema":
        """
        Validates that at least one feature is enabled.
        If no features are enabled, raises a ValueError.
        """
        logger = LoggerManager.setup_logger("schema")
        if not any(
            [
                self.tables,
                self.data,
                self.views,
                self.functions,
                self.procedures,
                self.triggers,
                self.events,
            ]
        ):
            logger.error("At least one MySQL feature must be enabled.")
            raise ValueError("At least one MySQL feature must be enabled.")
        return self


class DatabaseSchema(BaseModel):
    """
    Configuration for the database connection.
    This schema defines the structure for database connection settings
    used in the backup or restoration process.
    """

    db_type: Literal["mysql"] = Field(
        default="mysql",
        description="Type of the database to connect to.",
        example="mysql",
    )
    host: str = Field(
        ...,
        description="Database host address.",
        example="localhost",
    )
    port: int = Field(..., description="Database port number.", example=3306)
    user: str = Field(..., description="Database user name.", example="root")
    db_name: str = Field(..., description="Database name.", example="my_database")
    multiple_files: bool = Field(
        default=False,
        description="If True, backup will be stored in multiple files.",
    )
    restore_mode: Literal["backy", "sql"] = Field(
        default="sql",
        description="Mode of restoration, either 'backy' or 'sql'.",
    )
    features: MySQLFeaturesSchema = Field(default_factory=MySQLFeaturesSchema)
