# tests/integrity/test_integrity_base.py
import pytest
from integrity.integrity_base import IntegrityBase
from pathlib import Path
import os


class MockIntegrity(IntegrityBase):
    """Mock class for testing IntegrityBase functionality"""

    def create_integrity(self) -> Path:
        """Mock implementation of create_integrity method"""
        return super().create_integrity()

    def verify_integrity(self, integrity_file: Path) -> bool:
        """"""
        return super().verify_integrity(integrity_file)


class TestMockIntegrity:
    """
    Test class for MockIntegrity functionality
    """

    @pytest.fixture(autouse=True)
    def base_setup(self):
        """
        Setup method to initialize MockIntegrity before each test
        """
        self.mock_integrity = MockIntegrity()

    def test_initialize(self):
        """
        Test the initialization of MockIntegrity
        """
        assert self.mock_integrity.processing_path == Path(
            os.getenv("MAIN_BACKUP_PATH")
        )

    def test_create_integrity(self, caplog):
        """
        Test the create_integrity method of MockIntegrity. that return not implemented error
        """
        with pytest.raises(NotImplementedError) as excinfo:
            self.mock_integrity.create_integrity()
        assert "create_integrity method not implemented." in str(excinfo.value)
        assert "create_integrity method not implemented." in caplog.text

    def test_verify_integrity(self, caplog):
        """
        Test the verify_integrity method of MockIntegrity. that return not implemented error
        """
        with pytest.raises(NotImplementedError) as excinfo:
            self.mock_integrity.verify_integrity(Path("mock_integrity_file.txt"))
        assert "verify_integrity method not implemented." in str(excinfo.value)
        assert "verify_integrity method not implemented." in caplog.text

    def test_check_path_success(self, tmp_path):
        """
        Test the check_path method of MockIntegrity for successful path check
        """
        test_file = tmp_path / "mock_integrity_file.txt"
        test_file.write_text("This is a test file.")
        self.mock_integrity.check_path(test_file)

    def test_check_path_file_not_found(self):
        """
        Test the check_path method of MockIntegrity for file not found error
        """
        path = Path("non_existent_file.txt")
        with pytest.raises(FileNotFoundError) as excinfo:
            self.mock_integrity.check_path(path)
        assert f"Path {path} does not exist." in str(excinfo.value)

    def test_check_path_not_a_file(self, tmp_path):
        """
        Test the check_path method of MockIntegrity for not a file error
        """
        test_dir = tmp_path / "mock_directory"
        test_dir.mkdir()
        with pytest.raises(FileNotFoundError) as excinfo:
            self.mock_integrity.check_path(test_dir)
        assert f"Path {test_dir} is not a file." in str(excinfo.value)

    def test_get_files_from_processing_path_success_with_files_and_folders(self):
        """
        Test the get_files_from_processing_path method of MockIntegrity
        for successful retrieval of files from processing path.
        """
        test_file1 = self.mock_integrity.processing_path / "file1.txt"
        test_file1.write_text("This is file 1.")
        test_file2 = self.mock_integrity.processing_path / "file2.txt"
        test_file2.write_text("This is file 2.")
        test_dir = self.mock_integrity.processing_path / "mock_directory"
        test_dir.mkdir()

        files = self.mock_integrity.get_files_from_processing_path()
        assert len(files) == 2
        assert all(file.is_file() for file in files)
        assert files == sorted([test_file1, test_file2])

    def test_get_files_from_processing_path_no_files(self, caplog):
        """
        Test the get_files_from_processing_path method of MockIntegrity
        when no files are found in the processing path.
        """
        with pytest.raises(FileNotFoundError) as excinfo:
            self.mock_integrity.get_files_from_processing_path()
        assert "No files found in the processing path." in str(excinfo.value)
        assert "No files found in the processing path." in caplog.text
