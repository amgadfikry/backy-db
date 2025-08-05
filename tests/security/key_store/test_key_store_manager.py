# tests/security/key_store/test_key_store_manager.py
import pytest
from security.key_store.key_store_manager import KeyStoreManager


class TestKeyStoreManager:
    """
    Test suite for the KeyStoreManager class.
    This suite tests the key management operations of the service.
    """

    @pytest.fixture
    def key_store_manager(self, mocker):
        """
        Fixture to create an instance of KeyStoreManager.
        and mocking the GoogleKeyStore client.
        Returns:
            KeyStoreManager: An instance of KeyStoreManager.
        """
        # Mocking the GoogleKeyStore client
        google_mocker = mocker.Mock()
        google_mocker.save_key.return_value = None
        google_mocker.load_key.return_value = b"key_data"
        google_mocker.delete_key.return_value = None
        google_mocker.validate_key.return_value = True
        mocker.patch.dict(
            "security.key_store.key_store_manager.KeyStoreManager.STORE_MAPPING",
            {"google": lambda: google_mocker},
        )
        return KeyStoreManager(store_type="google")

    def test_unsupported_store_type(self):
        """
        Test that KeyStoreManager raises ValueError for unsupported store types.
        """
        with pytest.raises(ValueError) as exc_info:
            KeyStoreManager(store_type="unsupported")
        assert "Unsupported key store type: unsupported" in str(exc_info.value)

    def test_save_key(self, key_store_manager):
        """
        Test the save_key method of KeyStoreManager.
        """
        key_id = "test-key-id"
        key_data = b"test_key_data"
        key_store_manager.save_key(key_id, key_data)
        key_store_manager.key_store.save_key.assert_called_once_with(key_id, key_data)

    def test_load_key(self, key_store_manager):
        """
        Test the load_key method of KeyStoreManager.
        """
        key_id = "test-key-id"
        key_data = key_store_manager.load_key(key_id)
        assert key_data == b"key_data"
        key_store_manager.key_store.load_key.assert_called_once_with(key_id)

    def test_delete_key(self, key_store_manager):
        """
        Test the delete_key method of KeyStoreManager.
        """
        key_id = "test-key-id"
        key_store_manager.delete_key(key_id)
        key_store_manager.key_store.delete_key.assert_called_once_with(key_id)

    def test_validate_key(self, key_store_manager):
        """
        Test the validate_key method of KeyStoreManager.
        """
        key_id = "test-key-id"
        is_valid = key_store_manager.validate_key(key_id)
        assert is_valid is True
        key_store_manager.key_store.validate_key.assert_called_once_with(key_id)
