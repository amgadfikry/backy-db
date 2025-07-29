# tests/utils/test_generate_hmac.py
import pytest
from utils.generate_hmac import compute_hmac
import hmac
import hashlib


class TestGenerateHMAC:
    """
    Test suite for the compute_hmac function.
    """

    def test_compute_hmac_with_folder(self, tmp_path, caplog):
        """
        Test that the compute_hmac function raises FileNotFoundError for a folder path.
        """
        test_folder = tmp_path / "test_folder"
        test_folder.mkdir()
        with caplog.at_level("ERROR"):
            with pytest.raises(FileNotFoundError):
                compute_hmac(test_folder, b"secret_key")
            assert f"File {test_folder} does not exist or is not a file." in caplog.text

    def test_compute_hmac_with_nonexistent_file(self, tmp_path, caplog):
        """
        Test that the compute_hmac function raises FileNotFoundError for a non-existent file.
        """
        non_existent_file = tmp_path / "non_existent_file.txt"
        with caplog.at_level("ERROR"):
            with pytest.raises(FileNotFoundError):
                compute_hmac(non_existent_file, b"secret_key")
            assert (
                f"File {non_existent_file} does not exist or is not a file."
                in caplog.text
            )

    def test_compute_hmac_with_no_key(self, tmp_path, caplog):
        """
        Test that the compute_hmac function raises ValueError when no key is provided.
        """
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        with caplog.at_level("ERROR"):
            with pytest.raises(ValueError):
                compute_hmac(test_file, b"")
            assert "HMAC key must be provided." in caplog.text

    def test_compute_hmac_with_valid_file(self, tmp_path):
        """
        Test that the compute_hmac function computes the correct HMAC for a valid file.
        """
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        key = b"secret_key"
        hmac_value = compute_hmac(test_file, key)
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
        hmac_value = compute_hmac(empty_file, key)
        assert hmac_value is not None
        assert isinstance(hmac_value, str)
        expected_hmac = hmac.new(key, digestmod=hashlib.sha256)
        expected_hmac.update(empty_file.read_bytes())
        assert hmac_value == expected_hmac.hexdigest()

    def test_compute_hmac_with_error_handling(self, tmp_path, mocker):
        """
        Test that the compute_hmac function raises RuntimeError on unexpected errors.
        """
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        key = b"secret_key"
        mocker.patch("utils.generate_hmac.open", side_effect=IOError("Mocked IOError"))
        with pytest.raises(RuntimeError) as e:
            compute_hmac(test_file, key)
        assert f"Failed to compute HMAC for {test_file}" in str(e.value)
