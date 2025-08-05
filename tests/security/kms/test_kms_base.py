# tests/security/kms/test_kms_base.py
from security.kms.kms_base import KMSBase
import pytest


class MockKMS(KMSBase):
    """
    Mock implementation of KMSBase for testing purposes.
    """

    def generate_key(self, alias_name: str) -> str:
        """Generate a new KMS key and return its alias name."""
        return super().generate_key(alias_name)

    def get_public_key(self, key_id: str) -> bytes:
        """Retrieve the public key associated with the KMS key_id."""
        return super().get_public_key(key_id)

    def decrypt_symmetric_key(self, key_id: str, encrypted_key: bytes) -> bytes:
        """Decrypt a symmetric key using the KMS key_id."""
        return super().decrypt_symmetric_key(key_id, encrypted_key)

    def validate_key(self, key_id: str) -> bool:
        """Validate the existence and usability of a KMS key."""
        return super().validate_key(key_id)

    def delete_key(self, key_id: str) -> None:
        """Delete a KMS key by its key_id."""
        return super().delete_key(key_id)


class TestKMSBase:
    """
    Test suite for the KMSBase abstract class.
    This suite tests the abstract methods and ensures they raise NotImplementedError.
    """

    @pytest.fixture
    def mock_kms(self):
        """
        Fixture to create an instance of MockKMS.
        Returns:
            MockKMS: An instance of MockKMS.
        """
        return MockKMS()

    def test_generate_key_not_implemented(self, mock_kms, caplog):
        """
        Test that generate_key raises NotImplementedError.
        """
        with pytest.raises(NotImplementedError) as exc_info:
            mock_kms.generate_key("test-alias")
        assert "generate_key method not implemented." in caplog.text
        assert "generate_key method not implemented." in str(exc_info.value)

    def test_get_public_key_not_implemented(self, mock_kms, caplog):
        """
        Test that get_public_key raises NotImplementedError.
        """
        with pytest.raises(NotImplementedError) as exc_info:
            mock_kms.get_public_key("test-key-id")
        assert "get_public_key method not implemented." in caplog.text
        assert "get_public_key method not implemented." in str(exc_info.value)

    def test_decrypt_symmetric_key_not_implemented(self, mock_kms, caplog):
        """
        Test that decrypt_symmetric_key raises NotImplementedError.
        """
        with pytest.raises(NotImplementedError) as exc_info:
            mock_kms.decrypt_symmetric_key("test-key-id", b"encrypted_key_data")
        assert "decrypt_symmetric_key method not implemented." in caplog.text
        assert "decrypt_symmetric_key method not implemented." in str(exc_info.value)

    def test_validate_key_not_implemented(self, mock_kms, caplog):
        """
        Test that validate_key raises NotImplementedError.
        """
        with pytest.raises(NotImplementedError) as exc_info:
            mock_kms.validate_key("test-key-id")
        assert "validate_key method not implemented." in caplog.text
        assert "validate_key method not implemented." in str(exc_info.value)

    def test_delete_key_not_implemented(self, mock_kms, caplog):
        """
        Test that delete_key raises NotImplementedError.
        """
        with pytest.raises(NotImplementedError) as exc_info:
            mock_kms.delete_key("test-key-id")
        assert "delete_key method not implemented." in caplog.text
        assert "delete_key method not implemented." in str(exc_info.value)
