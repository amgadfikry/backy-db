# tests/utils/test_generate_checksum.py
import pytest
from utils.generate_checksum import generate_sha256
import hashlib


class TestGenerateChecksum:
    """
    Test suite for the generate_sha256 function.
    """
    def test_generate_sha256_with_folder(self, tmp_path, caplog):
        """
        Test that the generate_sha256 function raises FileNotFoundError for a folder path.  
        """
        test_folder = tmp_path / "test_folder"
        test_folder.mkdir()
        with caplog.at_level("ERROR"):
            with pytest.raises(FileNotFoundError):
                generate_sha256(test_folder)
            assert f"File {test_folder} does not exist or is not a file." in caplog.text

    def test_generate_sha256_with_nonexistent_file(self, tmp_path, caplog):
        """
        Test that the generate_sha256 function raises FileNotFoundError for a non-existent file.
        """
        non_existent_file = tmp_path / "non_existent_file.txt"
        with caplog.at_level("ERROR"):
            with pytest.raises(FileNotFoundError):
                generate_sha256(non_existent_file)
            assert f"File {non_existent_file} does not exist or is not a file." in caplog.text

    def test_generate_sha256_with_valid_file(self, tmp_path):
        """
        Test that the generate_sha256 function generates the correct checksum for a valid file.
        """
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        checksum = generate_sha256(test_file)
        assert checksum is not None
        assert isinstance(checksum, str)
        assert len(checksum) == 64
        expected_checksum = hashlib.sha256(test_file.read_bytes()).hexdigest()
        assert checksum == expected_checksum

    def test_generate_sha256_with_empty_file(self, tmp_path):
        """
        Test that the generate_sha256 function generates the correct checksum for an empty file.
        """
        empty_file = tmp_path / "empty_file.txt"
        empty_file.touch()
        checksum = generate_sha256(empty_file)
        assert checksum is not None
        assert isinstance(checksum, str)
        assert len(checksum) == 64
        expected_checksum = hashlib.sha256(empty_file.read_bytes()).hexdigest()
        assert checksum == expected_checksum

    def test_generate_sha256_with_error_handling(self, tmp_path, mocker):
        """
        Test that the generate_sha256 function raises RuntimeError on unexpected errors.
        """
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        mocker.patch("utils.generate_checksum.open", side_effect=IOError("Mocked IOError"))
        with pytest.raises(RuntimeError) as e:
            generate_sha256(test_file)
        assert f"Failed to generate checksum for {test_file}" in str(e.value)
