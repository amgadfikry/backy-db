# tests/integrity/test_checksum_integrity.py
import pytest
from integrity.checksum_integrity import ChecksumIntegrity
import hashlib


class TestChecksumIntegrity:
    """
    Test class for ChecksumIntegrity functionality
    """

    @pytest.fixture(autouse=True)
    def setup(self, mocker, tmp_path):
        """
        Setup method to initialize base class and HMACIntegrity before each test
        """
        first_file = tmp_path / "test_file.txt"
        first_file.write_text("This is a test file.")
        second_file = tmp_path / "test_file2.txt"
        second_file.write_text("This is another test file.")
        self.checksum_integrity = ChecksumIntegrity()
        mocker.patch.object(self.checksum_integrity, "processing_path", tmp_path)
        mocker.patch.object(
            self.checksum_integrity,
            "get_files_from_processing_path",
            return_value=[first_file, second_file],
        )
        mocker.patch.object(self.checksum_integrity, "check_path", return_value=None)

    def test_initialize(self, tmp_path):
        """
        Test the initialization of ChecksumIntegrity
        """
        assert self.checksum_integrity.processing_path == tmp_path

    def test_create_integrity_success(self, mocker):
        """
        Test the create_integrity method for successful checksum file creation
        """
        mocker.patch.object(
            self.checksum_integrity, "generate_sha256", return_value="dummychecksum"
        )
        checksum_file = self.checksum_integrity.create_integrity()
        assert checksum_file.exists()
        with open(checksum_file, "r") as f:
            content = f.read()
        assert "dummychecksum  test_file.txt" in content
        assert "dummychecksum  test_file2.txt" in content

    def test_create_integrity_success_make_sure_pass_itself(self, mocker):
        """
        Test the create_integrity method for successful checksum file creation
        """
        files = self.checksum_integrity.get_files_from_processing_path()
        files.append(self.checksum_integrity.processing_path / "integrity.sha256")
        mocker.patch.object(
            self.checksum_integrity,
            "get_files_from_processing_path",
            return_value=files,
        )
        mocker.patch.object(
            self.checksum_integrity, "generate_sha256", return_value="dummychecksum"
        )
        checksum_file = self.checksum_integrity.create_integrity()
        assert checksum_file.exists()
        with open(checksum_file, "r") as f:
            content = f.read()
        assert "dummychecksum  test_file.txt" in content
        assert "dummychecksum  test_file2.txt" in content

    def test_create_integrity_failure(self, mocker):
        """
        Test the create_integrity method for failure when no files are present
        """
        mocker.patch("builtins.open", side_effect=IOError("Failed to open file"))
        with pytest.raises(RuntimeError) as exc_info:
            self.checksum_integrity.create_integrity()
        assert "Failed to create checksum file" in str(exc_info.value)

    def test_verify_integrity_success(self, mocker, tmp_path):
        """
        Test the verify_integrity method for successful checksum verification
        """
        integrity_file = tmp_path / "integrity.sha256"
        integrity_file.write_text(
            "dummychecksum  test_file.txt\ndummychecksum  test_file2.txt\n"
        )
        mocker.patch.object(
            self.checksum_integrity, "generate_sha256", return_value="dummychecksum"
        )
        result = self.checksum_integrity.verify_integrity(integrity_file)
        assert result is True

    def test_verify_integrity_success_pass_itself(self, mocker, tmp_path):
        """
        Test the verify_integrity method for successful checksum verification
        """
        integrity_file = tmp_path / "integrity.sha256"
        integrity_file.write_text(
            "dummychecksum  test_file.txt\n"
            "dummychecksum  test_file2.txt\n"
            "dummychecksum  integrity.sha256\n"
        )
        mocker.patch.object(
            self.checksum_integrity, "generate_sha256", return_value="dummychecksum"
        )
        result = self.checksum_integrity.verify_integrity(integrity_file)
        assert result is True

    def test_verify_integrity_failure(self, mocker, tmp_path):
        """
        Test the verify_integrity method for failure when checksums do not match
        """
        integrity_file = tmp_path / "integrity.sha256"
        integrity_file.write_text(
            "dummychecksum  test_file.txt\nwrongchecksum  test_file2.txt\n"
        )
        mocker.patch.object(
            self.checksum_integrity,
            "generate_sha256",
            side_effect=RuntimeError("Checksum mismatch"),
        )
        with pytest.raises(RuntimeError) as exc_info:
            self.checksum_integrity.verify_integrity(integrity_file)
        assert "Failed to verify checksum file" in str(exc_info.value)

    def test_generate_sha256_with_success(self):
        """
        Test that the generate_sha256 function generates the correct checksum for a valid file.
        """
        files = self.checksum_integrity.get_files_from_processing_path()
        checksum = self.checksum_integrity.generate_sha256(files[0])
        assert checksum is not None
        assert isinstance(checksum, str)
        assert len(checksum) == 64
        expected_checksum = hashlib.sha256(files[0].read_bytes()).hexdigest()
        assert checksum == expected_checksum

    def test_generate_sha256_with_empty_file(self, tmp_path):
        """
        Test that the generate_sha256 function generates the correct checksum for an empty file.
        """
        empty_file = tmp_path / "empty_file.txt"
        empty_file.touch()
        checksum = self.checksum_integrity.generate_sha256(empty_file)
        assert checksum is not None
        assert isinstance(checksum, str)
        assert len(checksum) == 64
        expected_checksum = hashlib.sha256(empty_file.read_bytes()).hexdigest()
        assert checksum == expected_checksum

    def test_generate_sha256_with_error_handling(self, tmp_path, mocker):
        """
        Test that the generate_sha256 function raises RuntimeError on unexpected errors.
        """
        files = self.checksum_integrity.get_files_from_processing_path()
        test_file = files[0]
        mocker.patch("builtins.open", side_effect=IOError("Mocked IOError"))
        with pytest.raises(RuntimeError) as e:
            self.checksum_integrity.generate_sha256(test_file)
        assert f"Failed to generate checksum for {test_file}" in str(e.value)
