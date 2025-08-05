# tests/test_security_manager.py
import pytest
from security.security_manager import SecurityManager


class TestSecurityManager:
    """
    Test suite for the SecurityManager class.
    This suite tests the initialization, key loading, encryption, and decryption functionalities.
    """

    @pytest.fixture
    def security_manager(self, mocker):
        """
        Fixture to create a SecurityManager instance with a mock security configuration.
        Returns:
            SecurityManager: An instance of SecurityManager.
        """
        # Mock SecurityEngine.get_keys
        mock_engine = mocker.patch("security.security_manager.SecurityEngine")
        mock_engine_instance = mock_engine.return_value
        mock_engine_instance.get_keys.return_value = (
            b"symmetric_key",
            b"encrypted_key",
            "key_id",
        )
        # Mock EncryptionService
        mock_encryptor_class = mocker.patch(
            "security.security_manager.EncryptionService"
        )
        mock_encryptor_instance = mock_encryptor_class.return_value
        mock_encryptor_instance.encrypt_bytes.return_value = b"encrypted_data"
        # Mock DecryptionService
        mock_decryptor_class = mocker.patch(
            "security.security_manager.DecryptionService"
        )
        mock_decryptor_instance = mock_decryptor_class.return_value
        mock_decryptor_instance.decrypt_bytes.return_value = b"decrypted_data"
        # Create SecurityManager instance
        security_config = {"some_config": "value"}
        return SecurityManager(security_config)

    def test_initialization_success(self, security_manager):
        """
        Test that the SecurityManager initializes correctly and loads keys.
        """
        assert security_manager is not None
        assert security_manager._SecurityManager__symmetric_key == b"symmetric_key"
        assert security_manager.encrypted_symmetric_key == b"encrypted_key"
        assert security_manager.key_id == "key_id"
        assert security_manager.encryptor is not None
        assert security_manager.decryptor is not None

    def test_load_keys_success(self, security_manager):
        """
        Test that the load_keys method correctly loads keys.
        """
        security_manager.load_keys()
        assert security_manager._SecurityManager__symmetric_key == b"symmetric_key"
        assert security_manager.encrypted_symmetric_key == b"encrypted_key"
        assert security_manager.key_id == "key_id"

    def test_encrypt_bytes_success(self, security_manager):
        """
        Test that the encrypt_bytes method correctly encrypts data.
        """
        data = b"some_data"
        encrypted_data = security_manager.encrypt_bytes(data)
        assert encrypted_data == b"encrypted_data"
        security_manager.encryptor.encrypt_bytes.assert_called_once_with(
            data, security_manager._SecurityManager__symmetric_key
        )

    def test_encrypt_bytes_no_key(self, security_manager, caplog):
        """
        Test that encrypt_bytes raises an error if the symmetric key is not loaded.
        """
        security_manager._SecurityManager__symmetric_key = None
        with pytest.raises(RuntimeError) as exc_info:
            security_manager.encrypt_bytes(b"some_data")
        assert "Symmetric key not loaded. Call load_keys() first." in caplog.text
        assert "Symmetric key not loaded. Call load_keys() first." in str(
            exc_info.value
        )

    def test_decrypt_bytes_success(self, security_manager):
        """
        Test that the decrypt_bytes method correctly decrypts data.
        """
        encrypted_data = b"encrypted_data"
        decrypted_data = security_manager.decrypt_bytes(encrypted_data)
        assert decrypted_data == b"decrypted_data"
        security_manager.decryptor.decrypt_bytes.assert_called_once_with(
            encrypted_data, security_manager._SecurityManager__symmetric_key
        )

    def test_decrypt_bytes_no_key(self, security_manager, caplog):
        """
        Test that decrypt_bytes raises an error if the symmetric key is not loaded.
        """
        security_manager._SecurityManager__symmetric_key = None
        with pytest.raises(RuntimeError) as exc_info:
            security_manager.decrypt_bytes(b"encrypted_data")
        assert "Symmetric key not loaded. Call load_keys() first." in caplog.text
        assert "Symmetric key not loaded. Call load_keys() first." in str(
            exc_info.value
        )

    def test_get_encrypted_key_and_key_id(self, security_manager):
        """
        Test that get_encrypted_key_and_key_id returns the correct encrypted key and key ID.
        """
        encrypted_key, key_id = security_manager.get_encrypted_key_and_key_id()
        assert encrypted_key == b"encrypted_key"
        assert key_id == "key_id"

    def test_end_session(self, security_manager):
        """
        Test that end_session does not raise any errors.
        This method is currently a placeholder and does not perform any actions.
        """
        security_manager.end_session()
        assert security_manager._SecurityManager__symmetric_key is None
        assert security_manager.encrypted_symmetric_key is None
