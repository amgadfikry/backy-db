# tests/security/testencryption_service.py
import pytest
from security.encryption_service import EncryptionService
from pathlib import Path
import shutil
from cryptography.hazmat.primitives.asymmetric import rsa


class TestEncryptionService:
    """
    Tests for the EncryptionService class.
    """

    @pytest.fixture
    def encryption_service_setup(self, tmp_path, monkeypatch, mocker):
        """
        Setup fixture for EncryptionService tests.
        """
        process_path = tmp_path / "test_backup"
        process_path.mkdir()
        monkeypatch.setenv("MAIN_BACKUP_PATH", str(process_path))

        # Create a dummy public key for testing
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        # Mock SecurityEngine's initialization to prevent actual key generation/loading
        mocker.patch(
            "security.security_engine.SecurityEngine._check_keys_exist",
            return_value=True,
        )
        mocker.patch(
            "security.security_engine.SecurityEngine._load_public_key",
            return_value=(public_key, "v1"),
        )
        config = {
            "private_key_password": "test_password",
            "private_key_size": "2048",
            "integrity_password": "test_integrity_password",
            "integrity_check": True,
            "file_extension": "zip",
        }
        service = EncryptionService(config)

        yield service, process_path, public_key

        shutil.rmtree(process_path, ignore_errors=True)

    def test_encrypt_using_symmetric_key_success(self, encryption_service_setup):
        """
        Test that encrypt_using_symmetric_key successfully encrypts a file.
        """
        service, processing_path, _ = encryption_service_setup
        # Create a mock compressed file
        mock_zip_file = processing_path / f"backup.{service.compression_extension}"
        mock_zip_file.write_bytes(b"mock_backup_data")
        # Call the method to encrypt the file
        symmetric_key = service.encrypt_using_symmetric_key()
        # Assertions
        assert isinstance(symmetric_key, bytes)
        assert len(symmetric_key) == 32
        encrypted_file_path = (
            processing_path / f"backup.{service.compression_extension}.enc"
        )
        assert encrypted_file_path.exists()
        assert not mock_zip_file.exists()

    def test_encrypt_using_symmetric_key_no_file_found(
        self, encryption_service_setup, caplog
    ):
        """
        Test that encrypt_using_symmetric_key raises FileNotFoundError if no compressed file is found.
        """
        service, _, _ = encryption_service_setup
        with caplog.at_level("ERROR"):
            with pytest.raises(FileNotFoundError) as excinfo:
                service.encrypt_using_symmetric_key()
            assert "No zip file found in the processing path." in str(excinfo.value)
            assert "No zip file found in the processing path." in caplog.text

    def test_encrypt_using_symmetric_key_failure(
        self, encryption_service_setup, mocker, caplog
    ):
        """
        Test that encrypt_using_symmetric_key handles exceptions during encryption.
        """
        service, processing_path, _ = encryption_service_setup

        # Create a mock compressed file
        mock_zip_file = processing_path / f"backup.{service.compression_extension}"
        mock_zip_file.write_bytes(b"mock_backup_data")

        # Mock AESGCM to raise an exception during encryption
        mocker.patch(
            "security.encryption_service.AESGCM.encrypt",
            side_effect=Exception("Mock encryption error"),
        )
        with caplog.at_level("ERROR"):
            with pytest.raises(RuntimeError) as excinfo:
                service.encrypt_using_symmetric_key()
            assert "Failed to encrypt data with symmetric key" in str(excinfo.value)
            assert (
                "Error during encryption data with symmetric key: Mock encryption error"
                in caplog.text
            )

    def test_encrypt_symmetric_key_with_public_key_success(
        self, encryption_service_setup
    ):
        """
        Test that encrypt_symmetric_key_with_public_key successfully encrypts the symmetric key.
        """
        service, processing_path, _ = encryption_service_setup
        symmetric_key = b"test_symmetric_key"

        # Call the method to encrypt the symmetric key
        encrypted_key_path = service.encrypt_symmetric_key_with_public_key(
            symmetric_key
        )
        # Assertions
        assert isinstance(encrypted_key_path, Path)
        assert encrypted_key_path.exists()
        assert encrypted_key_path.name == f"encryption_key_{service.version}.enc"
        files_in_processing_path = list(processing_path.glob("encryption_key_*.enc"))
        assert len(files_in_processing_path) == 1

    def test_encrypt_symmetric_key_with_public_key_no_public_key(
        self, encryption_service_setup, caplog
    ):
        """
        Test that encrypt_symmetric_key_with_public_key raises ValueError if public key is not loaded.
        """
        service, _, _ = encryption_service_setup
        service.public_key = None
        symmetric_key = b"test_symmetric_key"
        with caplog.at_level("ERROR"):
            with pytest.raises(ValueError) as excinfo:
                service.encrypt_symmetric_key_with_public_key(symmetric_key)
            assert "Public key is not loaded." in str(excinfo.value)
            assert "Public key is not loaded." in caplog.text

    def test_encrypt_symmetric_key_with_public_key_failure(
        self, encryption_service_setup, mocker, caplog
    ):
        """
        Test that encrypt_symmetric_key_with_public_key handles exceptions during encryption.
        """
        service, _, public_key = encryption_service_setup
        symmetric_key = b"test_symmetric_key"

        mocker.patch(
            "security.encryption_service.open", side_effect=Exception("Mock open error")
        )

        with caplog.at_level("ERROR"):
            with pytest.raises(RuntimeError) as excinfo:
                service.encrypt_symmetric_key_with_public_key(symmetric_key)
            assert "Failed to encrypt symmetric key with public key" in str(
                excinfo.value
            )
            assert (
                "Error encrypting symmetric key with public key: Mock open error"
                in caplog.text
            )
