# tests/config_schemas/schemas/test_backup_info_schema.py
from config_schemas.schemas.backup_info_schema import BackupInfoSchema
from datetime import datetime
import pytest


class TestBackupInfoSchema:
    """
    Test cases for BackupInfoSchema.
    This class contains tests to validate the BackupInfoSchema
    and ensure it behaves as expected.
    """

    def test_backup_info_schema_with_valid_data(self):
        """
        Test BackupInfoSchema with valid data.
        """
        schema = BackupInfoSchema(
            backup_type="backy",
            backup_description="Daily backup of the database.",
            expiry_date="2023-12-31",
        )
        assert schema.backup_type == "backy"
        assert schema.backup_description == "Daily backup of the database."
        assert schema.expiry_date == datetime(2023, 12, 31, 0, 0)

    def test_backup_info_schema_with_default_values(self):
        """
        Test BackupInfoSchema with default values.
        """
        schema = BackupInfoSchema()
        assert schema.backup_type == "sql"
        assert schema.backup_description == ""
        assert schema.expiry_date is None

    def test_backup_info_schema_with_invalid_backup_type(self):
        """
        Test BackupInfoSchema with an invalid backup type.
        """
        with pytest.raises(ValueError) as exc_info:
            BackupInfoSchema(backup_type="invalid_type")
        assert "validation error" in str(exc_info.value)

    def test_backup_info_schema_with_expiry_date_format(self):
        """
        Test BackupInfoSchema with an invalid expiry date format.
        """
        with pytest.raises(ValueError) as exc_info:
            BackupInfoSchema(expiry_date="invalid_date")
        assert "validation error" in str(exc_info.value)
