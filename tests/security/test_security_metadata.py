import pytest
from security.security_metadata import SecurityMetadata
import shutil
import logging
import json
from cryptography.hazmat.primitives.asymmetric import rsa
import hmac
import hashlib


class TestSecurityMetadata:
    """
    Tests for the SecurityMetadata class.
    """

    @pytest.fixture
    def security_metadata_setup(self, tmp_path, monkeypatch, mocker):
        """
        Setup fixture for SecurityMetadata tests.
        """
        process_path = tmp_path / "test_metadata_processing"
        process_path.mkdir()
        secret_path = tmp_path / ".backy-secrets"
        secret_path.mkdir()
        monkeypatch.setenv("MAIN_BACKUP_PATH", str(process_path))

        # Create a dummy public key for mocking purposes
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

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

        service = SecurityMetadata(config)

        yield service, process_path, secret_path, public_key

        shutil.rmtree(tmp_path, ignore_errors=True)

    def test_create_metadata_success(self, security_metadata_setup):
        """
        Test that create_metadata successfully creates a metadata file.
        """
        service, process_path, _, _ = security_metadata_setup

        metadata_file = service.create_metadata()

        assert metadata_file.exists()
        assert metadata_file.name == "security_metadata.json"
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
        assert "timestamp" in metadata
        assert metadata["main_folder"] == process_path.name
        assert (
            metadata["encrypted_data"]
            == f"{process_path.name}.{service.compression_extension}.enc"
        )
        assert metadata["version"] == "v1"
        assert metadata["HMAC"] == "SHA256"
        assert metadata["Nonce"] == "12 bytes"
        assert metadata["symmetric_key"] == "256 bits"
        assert metadata["private_key_size"] == "2048"
        assert metadata["encryption_type"] == "symmetric + asymmetric + password"
        assert (
            metadata["description"]
            == "This metadata file contains information about the encryption process."
        )

    def test_create_metadata_failure(self, security_metadata_setup, mocker, caplog):
        """
        Test that create_metadata handles exceptions during file writing.
        """
        service, _, _, _ = security_metadata_setup
        mocker.patch("json.dump", side_effect=Exception("Mock JSON error"))

        with caplog.at_level(logging.ERROR):
            with pytest.raises(RuntimeError) as excinfo:
                service.create_metadata()
            assert "Failed to create metadata file" in str(excinfo.value)
            assert "Error creating metadata file: Mock JSON error" in caplog.text

    def test_copy_public_key_success(self, security_metadata_setup):
        """
        Test that copy_public_key successfully copies the public key.
        """
        service, process_path, secret_path, public_key = security_metadata_setup

        # Create a mock public key file in the secret path
        public_key_name = f"public_key_{service.version}.pem"
        public_key_path = secret_path / public_key_name
        public_key_path.write_text("mock public key content")

        copied_key_path = service.copy_public_key()

        assert copied_key_path.exists()
        assert copied_key_path == process_path / public_key_name
        assert copied_key_path.read_text() == "mock public key content"

    def test_copy_public_key_file_not_found(self, security_metadata_setup, caplog):
        """
        Test that copy_public_key raises FileNotFoundError if the public key file does not exist.
        """
        service, _, _, _ = security_metadata_setup
        public_key_name = f"public_key_{service.version}.pem"

        with caplog.at_level(logging.ERROR):
            with pytest.raises(FileNotFoundError) as excinfo:
                service.copy_public_key()
                assert (
                    f"Public key file {public_key_name} does not exist in the secret path."
                    in str(excinfo.value)
                )
                assert (
                    f"Public key file {public_key_name} does not exist in the secret path."
                    in caplog.text
                )

    def test_copy_public_key_failure(self, security_metadata_setup, mocker, caplog):
        """
        Test that copy_public_key handles exceptions during file copying.
        """
        service, _, secret_path, _ = security_metadata_setup

        public_key_name = f"public_key_{service.version}.pem"
        public_key_path = secret_path / public_key_name
        public_key_path.write_text("mock public key content")

        mocker.patch("shutil.copy2", side_effect=Exception("Mock copy error"))

        with caplog.at_level(logging.ERROR):
            with pytest.raises(RuntimeError) as excinfo:
                service.copy_public_key()
            assert "Failed to copy public key" in str(excinfo.value)
            assert "Error copying public key: Mock copy error" in caplog.text

    def test_create_integrity_file_success(
        self, security_metadata_setup, mocker, caplog
    ):
        """
        Test that create_integrity_file successfully creates an integrity file.
        """
        service, process_path, _, _ = security_metadata_setup

        # Create mock files in the processing path
        (process_path / "file1.txt").write_text("content1")
        (process_path / "file2.txt").write_text("content2")

        mocker.patch("security.security_metadata.compute_hmac", return_value="checksum")

        with caplog.at_level("INFO"):
            integrity_file = service.create_integrity_file()
            assert integrity_file.exists()
            assert integrity_file.name == "integrity.hmac"
            with open(integrity_file, "r") as f:
                content = f.read()
            expected_content = "checksum  file1.txt\nchecksum  file2.txt\n"
            assert content == expected_content
            assert "integrity.hmac" not in content
            assert "Integrity file created successfully" in caplog.text

    def test_create_integrity_file_no_files_found(
        self, security_metadata_setup, caplog
    ):
        """
        Test that create_integrity_file raises FileNotFoundError if no files are found in the processing path.
        """
        service, _, _, _ = security_metadata_setup

        with caplog.at_level("ERROR"):
            with pytest.raises(FileNotFoundError) as excinfo:
                service.create_integrity_file()
            assert "No files found in the processing path." in str(excinfo.value)
            assert "No files found in the processing path." in caplog.text

    def test_create_integrity_file_failure(
        self, security_metadata_setup, mocker, caplog
    ):
        """
        Test that create_integrity_file handles exceptions during file writing.
        """
        service, process_path, _, _ = security_metadata_setup
        (process_path / "file1.txt").write_text("content1")

        mocker.patch(
            "security.security_metadata.compute_hmac",
            side_effect=Exception("Mock file write error"),
        )
        with caplog.at_level("ERROR"):
            with pytest.raises(RuntimeError) as excinfo:
                service.create_integrity_file()
            assert "Failed to create integrity file" in str(excinfo.value)
            assert "Error creating integrity file: Mock file write error" in caplog.text

    def test_verify_integrity_success(self, security_metadata_setup):
        """
        Test that verify_integrity returns True for valid checksums.
        """
        service, process_path, _, _ = security_metadata_setup

        # Create real files and a valid integrity file
        (process_path / "file1.txt").write_text("content1")
        (process_path / "file2.txt").write_text("content2")

        integrity_file_path = process_path / "integrity.hmac"

        with open(integrity_file_path, "w", encoding="utf-8") as f:
            for file in process_path.glob("*"):
                if file.name == "integrity.hmac":
                    continue
                h = hmac.new(
                    service.integrity_password.encode(), digestmod=hashlib.sha256
                )
                with open(file, "rb") as f2:
                    while chunk := f2.read(4096):
                        h.update(chunk)
                f.write(f"{h.hexdigest()}  {file.name}\n")

        is_valid = service.verify_integrity()
        assert is_valid is True
        assert integrity_file_path.exists()

    def test_verify_integrity_file_not_found(self, security_metadata_setup, caplog):
        """
        Test that verify_integrity raises FileNotFoundError if the integrity file does not exist.
        """
        service, _, _, _ = security_metadata_setup

        with caplog.at_level(logging.ERROR):
            with pytest.raises(FileNotFoundError) as excinfo:
                service.verify_integrity()
            assert "Integrity file does not exist in the processing path." in str(
                excinfo.value
            )
            assert (
                "Integrity file does not exist in the processing path." in caplog.text
            )

    def test_verify_files_in_integrity_file_not_found(
        self, security_metadata_setup, caplog
    ):
        """
        Test that verify_integrity raises FileNotFoundError if a file listed in the integrity file does not exist.
        """
        service, process_path, _, _ = security_metadata_setup

        # Create real files and a valid integrity file
        (process_path / "file1.txt").write_text("content1")
        (process_path / "file2.txt").write_text("content2")

        integrity_file_path = process_path / "integrity.hmac"

        with open(integrity_file_path, "w", encoding="utf-8") as f:
            for file in process_path.glob("*"):
                if file.name == "integrity.hmac":
                    continue
                h = hmac.new(
                    service.integrity_password.encode(), digestmod=hashlib.sha256
                )
                with open(file, "rb") as f2:
                    while chunk := f2.read(4096):
                        h.update(chunk)
                f.write(f"{h.hexdigest()}  {file.name}\n")

        # Remove one of the files to simulate a missing file
        (process_path / "file2.txt").unlink()

        with caplog.at_level("ERROR"):
            with pytest.raises(FileNotFoundError) as excinfo:
                service.verify_integrity()
            assert "File file2.txt does not exist in the processing path." in str(
                excinfo.value
            )
            assert (
                "File file2.txt does not exist in the processing path." in caplog.text
            )

    def test_verify_integrity_checksum_mismatch(self, security_metadata_setup, caplog):
        """
        Test that verify_integrity returns False for a checksum mismatch.
        """
        service, process_path, _, _ = security_metadata_setup

        # Create real files and a valid integrity file
        (process_path / "file1.txt").write_text("content1")
        (process_path / "file2.txt").write_text("content2")

        integrity_file_path = process_path / "integrity.hmac"

        with open(integrity_file_path, "w", encoding="utf-8") as f:
            for file in process_path.glob("*"):
                if file.name == "integrity.hmac":
                    continue
                h = hmac.new(
                    service.integrity_password.encode(), digestmod=hashlib.sha256
                )
                with open(file, "rb") as f2:
                    while chunk := f2.read(4096):
                        h.update(chunk)
                f.write(f"{h.hexdigest()}  {file.name}\n")

        # Modify one of the files to create a checksum mismatch
        (process_path / "file1.txt").write_text("modified content")

        with caplog.at_level("ERROR"):
            with pytest.raises(ValueError) as excinfo:
                service.verify_integrity()
            assert "Checksum mismatch for file file1.txt" in str(excinfo.value)
            assert "Checksum mismatch for file file1.txt" in caplog.text

    def test_verify_integrity_failure(self, security_metadata_setup, mocker, caplog):
        """
        Test that verify_integrity handles exceptions during verification.
        """
        service, process_path, _, _ = security_metadata_setup

        integrity_file_path = process_path / "integrity.hmac"
        integrity_file_path.write_text("checksum1  file1.txt\n")

        mocker.patch(
            "builtins.open",
            side_effect=Exception("Mock file read error"),
        )

        with caplog.at_level("ERROR"):
            with pytest.raises(RuntimeError) as excinfo:
                service.verify_integrity()
            assert "Failed to verify integrity" in str(excinfo.value)
            assert "Error verifying integrity: Mock file read error" in caplog.text
