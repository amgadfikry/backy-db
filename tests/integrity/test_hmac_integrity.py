# tests/integrity/test_hmac_integrity.py
import pytest
from integrity.hmac_integrity import HMACIntegrity
import hashlib
import secrets
import hmac


class TestHMACIntegrity:
    """
    Test class for HMACIntegrity functionality
    """

    @pytest.fixture(autouse=True)
    def setup(self, mocker, tmp_path, monkeypatch):
        """
        Setup method to initialize base class and HMACIntegrity before each test
        """
        monkeypatch.setenv("INTEGRITY_PASSWORD", "testpassword")
        first_file = tmp_path / "test_file.txt"
        first_file.write_text("This is a test file.")
        second_file = tmp_path / "test_file2.txt"
        second_file.write_text("This is another test file.")
        self.checksum_integrity = HMACIntegrity()
        mocker.patch.object(self.checksum_integrity, "processing_path", tmp_path)
        mocker.patch.object(
            self.checksum_integrity,
            "get_files_from_processing_path",
            return_value=[first_file, second_file],
        )
        mocker.patch.object(self.checksum_integrity, "check_path", return_value=None)

    def test_initialize(self, tmp_path):
        """
        Test the initialization of HMACIntegrity
        """
        assert self.checksum_integrity.processing_path == tmp_path
        assert self.checksum_integrity.integrity_password == "testpassword"

    def test_create_integrity_success(self, mocker):
        """
        Test the create_integrity method for successful hmac file creation
        """
        mocker.patch.object(
            self.checksum_integrity, "compute_hmac", return_value="dummychecksum"
        )
        mocker.patch.object(
            self.checksum_integrity, "derive_key", return_value=b"dummykey"
        )
        checksum_file = self.checksum_integrity.create_integrity()
        assert checksum_file.exists()
        with open(checksum_file, "r") as f:
            content = f.read()
        assert "salt: " in content
        assert "dummychecksum  test_file.txt" in content
        assert "dummychecksum  test_file2.txt" in content

    def test_create_integrity_failure(self, mocker):
        """
        Test the create_integrity method for failure when no files are present
        """
        mocker.patch.object(
            self.checksum_integrity, "derive_key", return_value=b"dummykey"
        )
        mocker.patch("builtins.open", side_effect=IOError("Failed to open file"))
        with pytest.raises(RuntimeError) as exc_info:
            self.checksum_integrity.create_integrity()
        assert "Failed to create integrity file" in str(exc_info.value)

    def test_verify_integrity_success(self, mocker, tmp_path):
        """
        Test the verify_integrity method for successful integrity verification
        """
        integrity_file = tmp_path / "integrity.hmac"
        integrity_file.write_text(
            f"salt: {secrets.token_bytes(16).hex()}\n"
            f"dummychecksum  test_file.txt\n"
            f"dummychecksum  test_file2.txt\n"
        )
        mocker.patch.object(
            self.checksum_integrity, "derive_key", return_value=b"dummykey"
        )
        mocker.patch.object(
            self.checksum_integrity, "compute_hmac", return_value="dummychecksum"
        )
        result = self.checksum_integrity.verify_integrity(integrity_file)
        assert result is True

    def test_verify_integrity_failure(self, mocker, tmp_path):
        """
        Test the verify_integrity method for failure when checksums do not match
        """
        integrity_file = tmp_path / "integrity.hmac"
        mocker.patch("builtins.open", side_effect=IOError("Failed to open file"))
        with pytest.raises(RuntimeError) as exc_info:
            self.checksum_integrity.verify_integrity(integrity_file)
        assert "Failed to verify integrity" in str(exc_info.value)

    def test_derived_key_success(self):
        """
        Test the key derivation method
        """
        password = "testpassword"
        salt = secrets.token_bytes(16)
        derived_key = self.checksum_integrity.derive_key(password, salt)
        assert isinstance(derived_key, bytes)
        assert len(derived_key) == 32
        assert derived_key != password.encode("utf-8")

    def test_derived_key_failure(self):
        """
        Test the key derivation method with invalid parameters
        """
        with pytest.raises(RuntimeError) as exc_info:
            self.checksum_integrity.derive_key("", None)
        assert "Failed to derive key" in str(exc_info.value)

    def test_compute_hmac_with_no_key(self, caplog):
        """
        Test that the compute_hmac function raises ValueError when no key is provided.
        """
        files = self.checksum_integrity.get_files_from_processing_path()
        test_file = files[0]
        with pytest.raises(ValueError):
            self.checksum_integrity.compute_hmac(test_file, b"")
        assert "HMAC key must be provided." in caplog.text

    def test_compute_hmac_with_valid_file(self):
        """
        Test that the compute_hmac function computes the correct HMAC for a valid file.
        """
        files = self.checksum_integrity.get_files_from_processing_path()
        test_file = files[0]
        key = b"secret_key"
        hmac_value = self.checksum_integrity.compute_hmac(test_file, key)
        assert hmac_value is not None
        assert isinstance(hmac_value, str)
        expected_hmac = hmac.new(key, digestmod=hashlib.sha256)
        expected_hmac.update(test_file.read_bytes())
        assert hmac_value == expected_hmac.hexdigest()

    def test_compute_hmac_with_empty_file(self, tmp_path):
        """
        Test that the compute_hmac function computes the correct HMAC for an empty file.
        """
        empty_file = tmp_path / "empty_file.txt"
        empty_file.touch()
        key = b"secret_key"
        hmac_value = self.checksum_integrity.compute_hmac(empty_file, key)
        assert hmac_value is not None
        assert isinstance(hmac_value, str)
        expected_hmac = hmac.new(key, digestmod=hashlib.sha256)
        expected_hmac.update(empty_file.read_bytes())
        assert hmac_value == expected_hmac.hexdigest()

    def test_compute_hmac_with_error_handling(self, tmp_path, mocker):
        """
        Test that the compute_hmac function raises RuntimeError on unexpected errors.
        """
        files = self.checksum_integrity.get_files_from_processing_path()
        test_file = files[0]
        key = b"secret_key"
        mocker.patch("builtins.open", side_effect=IOError("Mocked IOError"))
        with pytest.raises(RuntimeError) as e:
            self.checksum_integrity.compute_hmac(test_file, key)
        assert f"Failed to compute HMAC for {test_file}" in str(e.value)
