# tests/config_schemas.py/schemas/test_compression_schema.py
from config_schemas.schemas.compression_schema import CompressionSchema
import pytest


class TestCompressionSchema:
    """
    Test cases for CompressionSchema.
    This class contains tests to validate the CompressionSchema
    and ensure it behaves as expected.
    """

    def test_compression_schema_with_default_values(self):
        """
        Test CompressionSchema with default values.
        """
        schema = CompressionSchema()
        assert schema.compression is False
        assert schema.compression_type is None

    def test_compression_schema_with_custom_values(self):
        """
        Test CompressionSchema with custom values.
        """
        schema = CompressionSchema(compression=True, compression_type="tar")
        assert schema.compression is True
        assert schema.compression_type == "tar"

    def test_compression_schema_with_invalid_compression_type(self):
        """
        Test CompressionSchema with an invalid compression_type.
        """
        with pytest.raises(ValueError) as exc_info:
            CompressionSchema(compression=True, compression_type="invalid_type")
        assert "validation error" in str(exc_info.value)
        assert "compression_type" in str(exc_info.value)

    def test_compression_schema_with_missing_compression_type(self):
        """
        Test CompressionSchema with missing compression_type when compression is enabled.
        """
        with pytest.raises(ValueError) as exc_info:
            CompressionSchema(compression=True)
        assert "compression_type must be specified when compression is enabled." in str(
            exc_info.value
        )
