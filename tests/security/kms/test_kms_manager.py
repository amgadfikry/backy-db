# tests/security/kms/test_kms_manager.py
import pytest
from security.kms.kms_manager import KMSManager


class TestKMSManager:
    """
    Test suite for the KMSManager class.
    This suite tests the key management operations of the service.
    """

    @pytest.fixture
    def kms_manager(self, mocker):
        """
        Fixture to create an instance of KMSManager.
        and mocking the AWSKMS client.
        Returns:
            KMSManager: An instance of KMSManager.
        """
        aws_mocker = mocker.Mock()
        aws_mocker.generate_key.return_value = "test-key"
        aws_mocker.get_public_key.return_value = b"public_key_data"
        aws_mocker.decrypt_symmetric_key.return_value = b"decrypted_key"
        aws_mocker.validate_key.return_value = True
        mocker.patch.dict(
            "security.kms.kms_manager.KMSManager.KMS_CLIENT",
            {"aws": lambda: aws_mocker},
        )
        return KMSManager(kms_provider="aws")

    def test_unsupported_kms_provider(self):
        """
        Test that KMSManager raises ValueError for unsupported KMS providers.
        """
        with pytest.raises(ValueError) as exc_info:
            KMSManager(kms_provider="unsupported")
        assert "Unsupported KMS provider: unsupported" in str(exc_info.value)

    def test_generate_key(self, kms_manager):
        """
        Test the generate_key method of KMSManager.
        """
        key_alias = kms_manager.generate_key("test-key-alias")
        assert key_alias == "test-key"
        kms_manager.kms_client.generate_key.assert_called_once_with("test-key-alias")

    def test_get_public_key(self, kms_manager):
        """
        Test the get_public_key method of KMSManager.
        """
        public_key = kms_manager.get_public_key("test-key-id")
        assert public_key == b"public_key_data"
        kms_manager.kms_client.get_public_key.assert_called_once_with("test-key-id")

    def test_decrypt_symmetric_key(self, kms_manager):
        """
        Test the decrypt_symmetric_key method of KMSManager.
        """
        decrypted_key = kms_manager.decrypt_symmetric_key(
            "test-key-id", b"encrypted_key_data"
        )
        assert decrypted_key == b"decrypted_key"
        kms_manager.kms_client.decrypt_symmetric_key.assert_called_once_with(
            "test-key-id", b"encrypted_key_data"
        )

    def test_validate_key(self, kms_manager):
        """
        Test the validate_key method of KMSManager.
        """
        is_valid = kms_manager.validate_key("test-key-id")
        assert is_valid is True
        kms_manager.kms_client.validate_key.assert_called_once_with("test-key-id")

    def test_delete_key(self, kms_manager):
        """
        Test the delete_key method of KMSManager.
        """
        kms_manager.delete_key("test-key-id")
        kms_manager.kms_client.delete_key.assert_called_once_with("test-key-id")
