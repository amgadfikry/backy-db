# tests/security/services/test_decryption_service.py
import pytest
from security.services.decryption_service import DecryptionService
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class TestDecryptionService:
    """
    Test suite for the DecryptionService class.
    This suite tests the decryption functionality of the service.
    """

    @pytest.fixture
    def decryption_service(self):
        """
        Fixture to create an instance of DecryptionService.
        Returns:
            DecryptionService: An instance of DecryptionService.
        """
        return DecryptionService()

    def test_decrypt_bytes_success(self, decryption_service):
        """
        Test that the decrypt_bytes method correctly decrypts data.
        """
        symmetric_key = AESGCM.generate_key(bit_length=256)
        nonce = b"\x00" * 12  # Example nonce
        data = b"some_data"
        aesgcm = AESGCM(symmetric_key)
        encrypted_data = aesgcm.encrypt(nonce, data, None)

        decrypted_data = decryption_service.decrypt_bytes(
            nonce + encrypted_data, symmetric_key
        )
        assert decrypted_data == data

    def test_decrypt_bytes_no_blob(self, decryption_service, caplog):
        """
        Test that decrypt_bytes raises ValueError when no encrypted blob is provided.
        """
        symmetric_key = AESGCM.generate_key(bit_length=256)
        with pytest.raises(ValueError) as exc_info:
            decryption_service.decrypt_bytes(b"", symmetric_key)
        assert "No encrypted blob provided for decryption" in caplog.text
        assert "No encrypted blob provided for decryption" in str(exc_info.value)

    def test_decrypt_bytes_no_key(self, decryption_service, caplog):
        """
        Test that decrypt_bytes raises ValueError when no symmetric key is provided.
        """
        encrypted_blob = b"\x00" * 12 + b"some_encrypted_data"
        symmetric_key = None
        with pytest.raises(ValueError) as exc_info:
            decryption_service.decrypt_bytes(encrypted_blob, symmetric_key)
        assert "No symmetric key provided for decryption" in caplog.text
        assert "No symmetric key provided for decryption" in str(exc_info.value)

    def test_decrypt_bytes_error(self, decryption_service, mocker, caplog):
        """
        Test that decrypt_bytes raises RuntimeError when there is an error during decryption.
        """
        symmetric_key = AESGCM.generate_key(bit_length=256)
        encrypted_blob = b"\x00" * 12 + b"some_encrypted_data"
        # Mock the AESGCM decrypt method to raise an exception
        mocker.patch.object(
            AESGCM, "decrypt", side_effect=Exception("Decryption error")
        )
        with pytest.raises(RuntimeError) as exc_info:
            decryption_service.decrypt_bytes(encrypted_blob, symmetric_key)
        assert "Error decrypting data: Decryption error" in caplog.text
        assert "Error decrypting data: Decryption error" in str(exc_info.value)
