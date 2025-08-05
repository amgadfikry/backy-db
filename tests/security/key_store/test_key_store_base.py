# tests/security/key_store/test_key_store_base.py
import pytest
from security.key_store.key_store_base import KeyStoreBase


class MockKeyStore(KeyStoreBase):
    """
    Mock implementation of KeyStoreBase for testing purposes.
    This class provides concrete implementations of the abstract methods.
    """

    def save_key(self, key_id: str, key_data: bytes) -> None:
        """Save a key in the mock key store."""
        return super().save_key(key_id, key_data)

    def load_key(self, key_id: str) -> bytes:
        """Load a key from the mock key store."""
        return super().load_key(key_id)

    def delete_key(self, key_id: str) -> None:
        """Delete a key from the mock key store."""
        return super().delete_key(key_id)

    def validate_key(self, key_id: str) -> bool:
        """Validate a key in the mock key store."""
        return super().validate_key(key_id)


class TestKeyStoreBase:
    """
    Test suite for KeyStoreBase.
    """

    @pytest.fixture
    def mock_key_store(self):
        """
        Fixture to create an instance of MockKeyStore for testing.
        """
        return MockKeyStore()

    def test_save_key_not_implemented(self, mock_key_store):
        """
        Test that save_key raises NotImplementedError.
        """
        with pytest.raises(NotImplementedError) as exc_info:
            mock_key_store.save_key("test_key", b"test_data")
        assert "save_key method not implemented." in str(exc_info.value)

    def test_load_key_not_implemented(self, mock_key_store):
        """
        Test that load_key raises NotImplementedError.
        """
        with pytest.raises(NotImplementedError) as exc_info:
            mock_key_store.load_key("test_key")
        assert "load_key method not implemented." in str(exc_info.value)

    def test_delete_key_not_implemented(self, mock_key_store):
        """
        Test that delete_key raises NotImplementedError.
        """
        with pytest.raises(NotImplementedError) as exc_info:
            mock_key_store.delete_key("test_key")
        assert "delete_key method not implemented." in str(exc_info.value)

    def test_validate_key_not_implemented(self, mock_key_store):
        """
        Test that validate_key raises NotImplementedError.
        """
        with pytest.raises(NotImplementedError) as exc_info:
            mock_key_store.validate_key("test_key")
        assert "validate_key method not implemented." in str(exc_info.value)
