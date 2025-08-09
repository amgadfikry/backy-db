# tests/config_schemas/schemas/test_restore_schema.py
from config_schemas.schemas.restore_schema import RestoreSchema
from config_schemas.schemas.database_schema import DatabaseRestoreSchema
from config_schemas.schemas.storage_schema import StorageSchema
import pytest


class TestRestoreSchema:
    """
    Test cases for RestoreSchema.
    This class contains tests to validate the RestoreSchema
    and ensure it behaves as expected.
    """

    def test_restore_schema_with_default_values(self):
        """
        Test RestoreSchema with default values.
        """
        schema = RestoreSchema(
            database=DatabaseRestoreSchema(
                db_type="mysql",
                db_name="test_db",
                user="test_user",
                port=3306,
                host="localhost",
            ),
            backup_path="/path/to/backup",
            storage=StorageSchema(storage_type="local"),
        )
        assert schema.database.db_type == "mysql"
        assert schema.database.db_name == "test_db"
        assert schema.backup_path == "/path/to/backup"
        assert schema.storage.storage_type == "local"

    def test_restore_schema_with_empty_values(self):
        """
        Test RestoreSchema with empty values.
        """
        with pytest.raises(ValueError) as exc_info:
            RestoreSchema()
        assert "validation error" in str(exc_info.value)
        assert "required" in str(exc_info.value)
