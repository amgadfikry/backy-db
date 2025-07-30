import pytest
from unittest.mock import Mock
from security.security_manager import SecurityManager
from security.encryption_service import EncryptionService
from security.decryption_service import DecryptionService
from security.security_metadata import SecurityMetadata
from logger.logger_manager import LoggerManager
from pathlib import Path


class TestSecurityManager:
    """
    Tests for the SecurityManager class.
    """

    @pytest.fixture
    def security_manager_setup(self, mocker):
        """
        Setup fixture for SecurityManager tests.
        """
        # Mock the LoggerManager to prevent actual log file creation
        mock_logger = mocker.patch.object(
            LoggerManager, "setup_logger", autospec=True
        ).return_value
        mock_logger.info = Mock()
        mock_logger.error = Mock()

        # Mock the EncryptionService, DecryptionService, and SecurityMetadata classes
        mock_encryption_service_init = mocker.patch.object(
            EncryptionService, "__init__", autospec=True
        )
        mock_encryption_service_init.return_value = None
        mock_encryption_service = Mock(spec=EncryptionService)
        mock_encryption_service.encrypt_using_symmetric_key.return_value = (
            b"mock_symmetric_key"
        )
        mock_encryption_service.encrypt_symmetric_key_with_public_key.return_value = (
            None
        )
        mocker.patch(
            "security.security_manager.EncryptionService",
            return_value=mock_encryption_service,
        )

        mock_decryption_service_init = mocker.patch.object(
            DecryptionService, "__init__", autospec=True
        )
        mock_decryption_service_init.return_value = None
        mock_decryption_service = Mock(spec=DecryptionService)
        mock_decryption_service.decrypt_symmetric_key.return_value = (
            b"mock_symmetric_key"
        )
        mock_decryption_service.decrypt_data.return_value = Mock(spec=Path)
        mocker.patch(
            "security.security_manager.DecryptionService",
            return_value=mock_decryption_service,
        )

        mock_security_metadata_init = mocker.patch.object(
            SecurityMetadata, "__init__", autospec=True
        )
        mock_security_metadata_init.return_value = None
        mock_metadata_service = Mock(spec=SecurityMetadata)
        mock_metadata_service.create_metadata.return_value = Mock(spec=Path)
        mock_metadata_service.copy_public_key.return_value = Mock(spec=Path)
        mock_metadata_service.create_integrity_file.return_value = Mock(spec=Path)
        mock_metadata_service.verify_integrity.return_value = True
        mocker.patch(
            "security.security_manager.SecurityMetadata",
            return_value=mock_metadata_service,
        )

        # Default configuration for tests
        security_config = {
            "private_key_password": "test_password",
            "private_key_size": "2048",
            "integrity_password": "test_integrity_password",
            "integrity_check": True,
            "file_extension": "zip",
        }

        # Create an instance of SecurityManager
        manager = SecurityManager(security_config)

        yield manager, mock_encryption_service, mock_decryption_service, mock_metadata_service, mock_logger

    def test_init_success(self, security_manager_setup):
        """
        Test that SecurityManager initializes successfully.
        """
        manager, _, _, _, mock_logger = security_manager_setup
        assert isinstance(manager, SecurityManager)
        assert manager.logger == mock_logger
        assert manager.config["integrity_check"] is True
        assert isinstance(manager.metadata_service, Mock)

    def test_encryption_success_with_integrity_check(self, security_manager_setup):
        """
        Test that the encryption method completes successfully with integrity check enabled.
        """
        manager, mock_encryption_service, _, mock_metadata_service, mock_logger = (
            security_manager_setup
        )

        manager.encryption()

        mock_encryption_service.encrypt_using_symmetric_key.assert_called_once()
        mock_encryption_service.encrypt_symmetric_key_with_public_key.assert_called_once_with(
            b"mock_symmetric_key"
        )
        mock_metadata_service.create_metadata.assert_called_once()
        mock_metadata_service.copy_public_key.assert_called_once()
        mock_metadata_service.create_integrity_file.assert_called_once()
        mock_logger.info.assert_called_once_with("Encryption completed successfully")

    def test_encryption_success_without_integrity_check(self, security_manager_setup):
        """
        Test that the encryption method completes successfully without integrity check.
        """
        manager, mock_encryption_service, _, mock_metadata_service, mock_logger = (
            security_manager_setup
        )
        manager.config["integrity_check"] = False

        manager.encryption()

        mock_encryption_service.encrypt_using_symmetric_key.assert_called_once()
        mock_encryption_service.encrypt_symmetric_key_with_public_key.assert_called_once_with(
            b"mock_symmetric_key"
        )
        mock_metadata_service.create_metadata.assert_called_once()
        mock_metadata_service.copy_public_key.assert_called_once()
        mock_metadata_service.create_integrity_file.assert_not_called()
        mock_logger.info.assert_called_once_with("Encryption completed successfully")

    def test_encryption_failure(self, security_manager_setup):
        """
        Test that the encryption method handles exceptions gracefully.
        """
        manager, mock_encryption_service, _, _, mock_logger = security_manager_setup
        mock_encryption_service.encrypt_using_symmetric_key.side_effect = Exception(
            "Encryption key error"
        )

        with pytest.raises(Exception) as excinfo:
            manager.encryption()
        assert "Encryption key error" in str(excinfo.value)
        mock_logger.error.assert_called_once_with(
            "Encryption failed: Encryption key error"
        )

    def test_decryption_success_with_integrity_check(self, security_manager_setup):
        """
        Test that the decryption method completes successfully with integrity check enabled.
        """
        manager, _, mock_decryption_service, mock_metadata_service, mock_logger = (
            security_manager_setup
        )
        manager.integrity_check = True
        mock_decrypted_path = Mock(spec=Path, name="mock_decrypted_path")
        mock_decryption_service.decrypt_data.return_value = mock_decrypted_path

        manager.decryption()

        mock_metadata_service.verify_integrity.assert_called_once()
        mock_decryption_service.decrypt_symmetric_key.assert_called_once()
        mock_decryption_service.decrypt_data.assert_called_once_with(
            b"mock_symmetric_key"
        )
        mock_logger.info.assert_called_once_with(
            f"Decryption completed, decrypted file available at: {mock_decrypted_path}"
        )

    def test_decryption_success_without_integrity_check(self, security_manager_setup):
        """
        Test that the decryption method completes successfully without integrity check.
        """
        manager, _, mock_decryption_service, mock_metadata_service, mock_logger = (
            security_manager_setup
        )
        manager.config["integrity_check"] = False
        mock_decrypted_path = Mock(spec=Path, name="mock_decrypted_path")
        mock_decryption_service.decrypt_data.return_value = mock_decrypted_path

        manager.decryption()

        mock_metadata_service.verify_integrity.assert_not_called()
        mock_decryption_service.decrypt_symmetric_key.assert_called_once()
        mock_decryption_service.decrypt_data.assert_called_once_with(
            b"mock_symmetric_key"
        )
        mock_logger.info.assert_called_once_with(
            f"Decryption completed, decrypted file available at: {mock_decrypted_path}"
        )

    def test_decryption_integrity_check_failure(self, security_manager_setup):
        """
        Test that decryption method handles integrity check failure.
        """
        manager, _, _, mock_metadata_service, mock_logger = security_manager_setup
        manager.integrity_check = True
        mock_metadata_service.verify_integrity.side_effect = ValueError(
            "Integrity check failed"
        )

        with pytest.raises(ValueError) as excinfo:
            manager.decryption()
        assert "Integrity check failed" in str(excinfo.value)
        mock_logger.error.assert_called_once_with(
            "Decryption failed: Integrity check failed"
        )

    def test_decryption_failure(self, security_manager_setup):
        """
        Test that the decryption method handles general exceptions gracefully.
        """
        manager, _, mock_decryption_service, _, mock_logger = security_manager_setup
        mock_decryption_service.decrypt_symmetric_key.side_effect = Exception(
            "Decryption key error"
        )

        with pytest.raises(Exception) as excinfo:
            manager.decryption()
        assert "Decryption key error" in str(excinfo.value)
        mock_logger.error.assert_called_once_with(
            "Decryption failed: Decryption key error"
        )
