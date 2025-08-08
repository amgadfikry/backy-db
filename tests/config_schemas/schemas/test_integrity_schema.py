# tests/config_schemas.py/schemas/test_integrity_schema.py
from config_schemas.schemas.integrity_schema import IntegritySchema
import pytest


class TestIntegritySchema:
    """
    Test cases for IntegritySchema.
    This class contains tests to validate the IntegritySchema
    and ensure it behaves as expected.
    """

    def test_integrity_schema_with_default_values(self):
        """
        Test IntegritySchema with default values.
        """
        schema = IntegritySchema()
        assert schema.integrity_check is False
        assert schema.integrity_type is None

    def test_integrity_schema_with_custom_values(self):
        """
        Test IntegritySchema with custom values.
        """
        schema = IntegritySchema(integrity_check=True, integrity_type="checksum")
        assert schema.integrity_check is True
        assert schema.integrity_type == "checksum"

    def test_integrity_schema_with_enabled_check_without_type(self):
        """
        Test IntegritySchema with integrity_check enabled but without integrity_type.
        """
        with pytest.raises(ValueError) as exc_info:
            IntegritySchema(integrity_check=True)
        assert (
            "integrity_type must be specified when integrity_check is enabled."
            in str(exc_info.value)
        )

    def test_integrity_schema_with_invalid_type(self):
        """
        Test IntegritySchema with an invalid integrity_type.
        """
        with pytest.raises(ValueError) as exc_info:
            IntegritySchema(integrity_check=True, integrity_type="invalid_type")
        assert "validation error" in str(exc_info.value)
        assert "integrity_type" in str(exc_info.value)
