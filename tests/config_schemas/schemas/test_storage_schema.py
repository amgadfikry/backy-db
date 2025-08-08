# tests/config_schemas.py/schemas/test_storage_schema.py
from config_schemas.schemas.storage_schema import StorageSchema
import pytest


class TestStorageSchema:
    def test_valid_storage_schema(self):
        # Test with valid storage type
        valid_storage = StorageSchema(storage_type="local")
        assert valid_storage.storage_type == "local"

        valid_storage = StorageSchema(storage_type="aws")
        assert valid_storage.storage_type == "aws"

    def test_invalid_storage_schema(self):
        # Test with invalid storage type
        with pytest.raises(ValueError) as exc_info:
            StorageSchema(storage_type="invalid")
        assert "validation error" in str(exc_info.value)
        assert "storage_type" in str(exc_info.value)
