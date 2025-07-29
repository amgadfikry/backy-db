# typing/backup_typing.py
from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional
from logger.logger_manager import LoggerManager

logger = LoggerManager.setup_logger("schema")


class DatabaseConfig(BaseModel):
    """
    Configuration for the database connection.
    """
    host: str
    port: int
    user: str
    password: str
    db_name: str
    db_type: Literal['mysql', 'postgresql', 'sqlite']
    one_file: bool = Field(
        default=True, description="If True, backup will be stored in a single file."
    )
    tables: bool = Field(
        default=True, description="If True, backup will include tables."
    )
    data: bool = Field(
        default=True, description="If True, backup will include data."
    )
    triggers: bool = Field(
        default=False, description="If True, backup will include triggers."
    )
    views: bool = Field(
        default=False, description="If True, backup will include views."
    )
    functions: bool = Field(
        default=False, description="If True, backup will include functions."
    )
    procedures: bool = Field(
        default=False, description="If True, backup will include procedures."
    )
    events: bool = Field(
        default=False, description="If True, backup will include events."
    )


class StorageConfig(BaseModel):
    """
    Configuration for the storage system.
    """
    storage_type: Literal['local', 's3'] = Field(
        default='local', description="Type of storage system.")
    path: str


class CompressionConfig(BaseModel):
    """
    Configuration for compression settings.
    """
    compression: bool = Field(default=False, description="If True, backup will be compressed.")
    compression_type: Optional[Literal['zip', 'tar', 'targz']] = Field(
        default=None, description="Type of compression to use."
    )
    @model_validator(mode='after')
    def validate_compression_after(self) -> 'CompressionConfig':
        if self.compression and not self.compression_type:
            logger.warning("Compression type is not set, defaulting to 'zip'.")
            self.compression_type = 'zip'
        return self


class SecurityConfig(BaseModel):
    """
    Configuration for security settings.
    """
    encryption: bool = Field(
        default=False, description="If True, backup will be encrypted."
    )
    private_key_password: str = Field(
        default=None, description="Password for the private key if encryption is enabled."
    )
    private_key_size: str = Field(
        default=None, description="Size of the private key if encryption is enabled."
    )
    integrity_check: bool = Field(
        default=False, description="If True, integrity check will be performed on the backup."
    )
    integrity_password: str = Field(
        default=None, description="Password for integrity check if enabled."
    )
    file_extension: str = Field(
        default=None, description="File extension for the backup file."
    )

    @model_validator(mode='after') 
    def validate_encryption_after(self) -> 'SecurityConfig':
        if not self.encryption and self.integrity_check:
            logger.warning("Integrity check cannot be performed without encryption. Disabling integrity check.")
            self.integrity_check = False
        if self.encryption and not self.private_key_password:
            logger.error("Private key password must be set if encryption is enabled.")
            raise ValueError("Private key password must be set if encryption is enabled.")
        if self.encryption and not self.private_key_size:
            logger.warning("Private key size is not set, defaulting to '4096'.")
            self.private_key_size = '4096'
        if self.integrity_check and not self.integrity_password:
            logger.error("Integrity password must be set if integrity check is enabled.")
            raise ValueError("Integrity password must be set if integrity check is enabled.")
        return self


class BackupConfig(BaseModel):
    """
    Backup configuration combining all settings.
    """
    database: DatabaseConfig
    storage: StorageConfig
    compression: CompressionConfig = Field(default_factory=CompressionConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    @model_validator(mode='after')
    def validate_backup_config(self) -> 'BackupConfig':
        if not self.compression.compression and self.security.encryption:
            logger.warning("Cannot perform encryption without compression. disabling encryption.")
            self.security.encryption = False
            self.security.private_key_password = None
            self.security.private_key_size = None
            self.security.integrity_check = False
            self.security.integrity_password = None
        if self.compression.compression and self.security.encryption:
            self.security.file_extension = self.compression.compression_type
        return self