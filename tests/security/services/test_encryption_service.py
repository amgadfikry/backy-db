# tests/security/services/test_encryption_service.py
import pytest
from security.services.encryption_service import EncryptionService
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class TestEncryptionService:
    """
    Test suite for the EncryptionService class.
    This suite tests the encryption functionality of the service.
    """

    @pytest.fixture
    def encryption_service(self):
        """
        Fixture to create an instance of EncryptionService.
        Returns:
            EncryptionService: An instance of EncryptionService.
        """
        return EncryptionService()

    def test_encrypt_bytes_success(self, encryption_service):
        """
        Test that the encrypt_bytes method correctly encrypts data.
        """
        data = b"some_data"
        symmetric_key = AESGCM.generate_key(bit_length=256)
        encrypted_data = encryption_service.encrypt_bytes(data, symmetric_key)
        assert encrypted_data is not None
        assert isinstance(encrypted_data, bytes)
        assert len(encrypted_data) > 0
        assert encrypted_data != data

    def test_encrypt_bytes_no_data(self, encryption_service, caplog):
        """
        Test that encrypt_bytes raises ValueError when no data is provided.
        """
        data = b""
        symmetric_key = AESGCM.generate_key(bit_length=256)
        with pytest.raises(ValueError) as exc_info:
            encryption_service.encrypt_bytes(data, symmetric_key)
        assert "No data provided for encryption" in caplog.text
        assert "No data provided for encryption" in str(exc_info.value)

    def test_encrypt_bytes_no_key(self, encryption_service, caplog):
        """
        Test that encrypt_bytes raises ValueError when no symmetric key is provided.
        """
        data = b"some_data"
        symmetric_key = None
        with pytest.raises(ValueError) as exc_info:
            encryption_service.encrypt_bytes(data, symmetric_key)
        assert "No symmetric key provided for encryption" in caplog.text
        assert "No symmetric key provided for encryption" in str(exc_info.value)

    def test_encrypt_bytes_error(self, encryption_service, mocker, caplog):
        """
        Test that encrypt_bytes raises RuntimeError when there is an error during encryption.
        """
        data = b"some_data"
        symmetric_key = AESGCM.generate_key(bit_length=256)
        mocker.patch(
            "security.services.encryption_service.AESGCM",
            side_effect=Exception("Encryption error"),
        )
        with pytest.raises(RuntimeError) as exc_info:
            encryption_service.encrypt_bytes(data, symmetric_key)
        assert "Error encrypting data: Encryption error" in caplog.text
        assert "Error encrypting data: Encryption error" in str(exc_info.value)
