# tests/security/test_decryption_service.py
import pytest
from security.decryption_service import DecryptionService
import shutil
import logging
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import json
import os


class TestDecryptionService:
    """
    Tests for the DecryptionService class.
    """

    @pytest.fixture
    def decryption_service_setup(self, tmp_path, monkeypatch, mocker):
        """
        Setup fixture for DecryptionService tests.
        """
        process_path = tmp_path / "test_decryption"
        process_path.mkdir()
        secret_path = tmp_path / ".backy-secrets"
        secret_path.mkdir()
        monkeypatch.setenv("MAIN_BACKUP_PATH", str(process_path))

        # Generate a mock private key
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        # Mock SecurityEngine's initialization
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
        # Initialize DecryptionService
        service = DecryptionService(config)

        yield service, process_path, secret_path, private_key

        shutil.rmtree(tmp_path, ignore_errors=True)

    def test_decrypt_private_key_success(self, decryption_service_setup, caplog):
        """
        Test that _decrypt_private_key successfully decrypts the private key.
        """
        service, _, secret_path, private_key = decryption_service_setup

        # Save the private key to a file after encrypting it with the password
        private_key_path = secret_path / "private_key_v1.pem"
        with open(private_key_path, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.BestAvailableEncryption(
                        service.password.encode()
                    ),
                )
            )

        # Assert that the private key is decrypted successfully
        with caplog.at_level("INFO"):
            decrypted_key = service._decrypt_private_key()
            assert isinstance(decrypted_key, rsa.RSAPrivateKey)
            assert decrypted_key.private_numbers() == private_key.private_numbers()
            assert "Private key loaded successfully" in caplog.text

    def test_decrypt_private_key_file_not_found(self, decryption_service_setup, caplog):
        """
        Test that _decrypt_private_key raises FileNotFoundError if private key file does not exist.
        """
        service, _, _, _ = decryption_service_setup

        with caplog.at_level("ERROR"):
            with pytest.raises(FileNotFoundError) as excinfo:
                service._decrypt_private_key()
            assert "Private key file does not exist." in str(excinfo.value)
            assert "Private key file does not exist." in caplog.text

    def test_decrypt_private_key_failure(
        self, decryption_service_setup, mocker, caplog
    ):
        """
        Test that __decrypt_private_key handles exceptions during decryption.
        """
        service, _, secret_path, _ = decryption_service_setup
        private_key_path = secret_path / "private_key_v1.pem"
        private_key_path.touch()

        # Mock the serialization.load_pem_private_key to raise an exception
        mocker.patch(
            "cryptography.hazmat.primitives.serialization.load_pem_private_key",
            side_effect=Exception("Mock decryption error"),
        )

        with caplog.at_level("ERROR"):
            with pytest.raises(RuntimeError) as excinfo:
                service._decrypt_private_key()
            assert "Failed to load private key" in str(excinfo.value)
            assert "Error loading private key: Mock decryption error" in caplog.text

    def test_decrypt_symmetric_key_success(self, decryption_service_setup, mocker):
        """
        Test that decrypt_symmetric_key successfully decrypts the symmetric key.
        """
        service, process_path, _, private_key = decryption_service_setup

        # Create mock metadata and encrypted symmetric key files
        metadata_file = process_path / "metadata.json"
        with open(metadata_file, "w") as f:
            json.dump({"version": "v1"}, f)

        symmetric_key = b"mock_symmetric_key"
        encrypted_symmetric_key = service.public_key.encrypt(
            symmetric_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        encrypted_key_file = process_path / "encryption_key_v1.enc"
        encrypted_key_file.write_bytes(encrypted_symmetric_key)
        # Mock the private key decryption
        mocker.patch.object(service, "_decrypt_private_key", return_value=private_key)

        # Decrypt the symmetric key
        assert (process_path / "encryption_key_v1.enc").exists()
        assert (process_path / "metadata.json").exists()
        decrypted_key = service.decrypt_symmetric_key()
        assert decrypted_key == symmetric_key

    def test_decrypt_symmetric_key_no_metadata_file(
        self, decryption_service_setup, mocker, caplog
    ):
        """
        Test that decrypt_symmetric_key raises FileNotFoundError if metadata file does not exist.
        """
        service, process_path, _, private_key = decryption_service_setup

        # Create encrypted symmetric key files
        symmetric_key = b"mock_symmetric_key"
        encrypted_symmetric_key = service.public_key.encrypt(
            symmetric_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        encrypted_key_file = process_path / "encryption_key_v1.enc"
        encrypted_key_file.write_bytes(encrypted_symmetric_key)
        # Mock the private key decryption
        mocker.patch.object(service, "_decrypt_private_key", return_value=private_key)
        # Ensure metadata file does not exist
        assert not (process_path / "metadata.json").exists()
        with caplog.at_level("WARNING"):
            decrypt_key = service.decrypt_symmetric_key()
            assert "Metadata file does not exist" in caplog.text
            assert decrypt_key == symmetric_key

    def test_decrypt_symmetric_key_no_encrypted_key_file(
        self, decryption_service_setup, caplog
    ):
        """
        Test that decrypt_symmetric_key raises FileNotFoundError if encrypted symmetric key file does not exist.
        """
        service, process_path, _, _ = decryption_service_setup

        with caplog.at_level("ERROR"):
            with pytest.raises(FileNotFoundError) as excinfo:
                service.decrypt_symmetric_key()
            assert "Encrypted symmetric key file does not exist." in str(excinfo.value)
            assert "Encrypted symmetric key file does not exist." in caplog.text

    def test_decrypt_symmetric_key_private_key_not_loaded(
        self, decryption_service_setup, mocker, caplog
    ):
        """
        Test that decrypt_symmetric_key raises ValueError if private key is not loaded.
        """
        service, process_path, _, _ = decryption_service_setup

        (process_path / "encryption_key_v1.enc").touch()
        # Mock the private key decryption to return None
        mocker.patch.object(service, "_decrypt_private_key", return_value=None)

        with caplog.at_level("ERROR"):
            with pytest.raises(ValueError) as excinfo:
                service.decrypt_symmetric_key()
            assert "Private key is not loaded." in str(excinfo.value)
            assert "Private key is not loaded." in caplog.text

    def test_decrypt_symmetric_key_failure(
        self, decryption_service_setup, mocker, caplog
    ):
        """
        Test that decrypt_symmetric_key handles exceptions during symmetric key decryption.
        """
        service, process_path, _, private_key = decryption_service_setup
        (process_path / "encryption_key_v1.enc").touch()

        mocker.patch.object(service, "_decrypt_private_key", return_value=private_key)
        mocker.patch(
            "cryptography.hazmat.primitives.asymmetric.padding.OAEP",
            side_effect=Exception("Mock decryption error"),
        )

        with caplog.at_level(logging.ERROR):
            with pytest.raises(RuntimeError) as excinfo:
                service.decrypt_symmetric_key()
            assert "Failed to decrypt symmetric key" in str(excinfo.value)
            assert (
                "Error decrypting symmetric key: Mock decryption error" in caplog.text
            )

    def test_decrypt_data_success(self, decryption_service_setup):
        """
        Test that decrypt_data successfully decrypts the data.
        """
        # Create a symmetric key and encrypt some mock data
        service, process_path, _, _ = decryption_service_setup
        symmetric_key = AESGCM.generate_key(bit_length=256)
        aesgcm = AESGCM(symmetric_key)
        nonce = os.urandom(12)
        plaintext_data = b"mock_decryption_data"
        encrypted_data = aesgcm.encrypt(nonce, plaintext_data, None)

        encrypted_file_path = (
            process_path / f"backup.{service.compression_extension}.enc"
        )
        encrypted_file_path.write_bytes(nonce + encrypted_data)

        decrypted_file_path = service.decrypt_data(symmetric_key)

        assert (
            decrypted_file_path
            == process_path / f"backup.{service.compression_extension}"
        )
        assert decrypted_file_path.exists()
        with open(decrypted_file_path, "rb") as f:
            content = f.read()
        assert content == plaintext_data
        assert not encrypted_file_path.exists()

    def test_decrypt_data_no_encrypted_file_found(
        self, decryption_service_setup, caplog
    ):
        """
        Test that decrypt_data raises FileNotFoundError if no encrypted file is found.
        """
        service, _, _, _ = decryption_service_setup
        symmetric_key = b"dummy_key"

        with caplog.at_level("ERROR"):
            with pytest.raises(FileNotFoundError) as excinfo:
                service.decrypt_data(symmetric_key)
            assert "No encrypted file found in the processing path." in str(
                excinfo.value
            )
            assert "No encrypted file found in the processing path." in caplog.text

    def test_decrypt_data_no_symmetric_key(self, decryption_service_setup, caplog):
        """
        Test that decrypt_data raises ValueError if symmetric key is not provided.
        """
        service, process_path, _, _ = decryption_service_setup

        (process_path / f"backup.{service.compression_extension}.enc").touch()

        with caplog.at_level("ERROR"):
            with pytest.raises(ValueError) as excinfo:
                service.decrypt_data(b"")
            assert "Symmetric key is not provided for decryption." in str(excinfo.value)
            assert "Symmetric key is not provided for decryption." in caplog.text

    def test_decrypt_data_failure(self, decryption_service_setup, mocker, caplog):
        """
        Test that decrypt_data handles exceptions during data decryption.
        """
        # Create a dummy encrypted file
        service, process_path, _, _ = decryption_service_setup
        symmetric_key = AESGCM.generate_key(bit_length=256)
        aesgcm = AESGCM(symmetric_key)
        nonce = os.urandom(12)
        plaintext_data = b"mock_decryption_data"
        encrypted_data = aesgcm.encrypt(nonce, plaintext_data, None)

        encrypted_file_path = (
            process_path / f"backup.{service.compression_extension}.enc"
        )
        encrypted_file_path.write_bytes(nonce + encrypted_data)

        # Mock the AESGCM decrypt method to raise an exception
        mocker.patch.object(
            AESGCM, "decrypt", side_effect=Exception("Mock data decryption error")
        )

        with caplog.at_level("ERROR"):
            with pytest.raises(RuntimeError) as excinfo:
                service.decrypt_data(symmetric_key)
            assert "Failed to decrypt data" in str(excinfo.value)
            assert "Error decrypting data: Mock data decryption error" in caplog.text
