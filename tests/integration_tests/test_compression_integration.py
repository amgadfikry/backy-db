# tests/integration/test_compression_integration.py
import pytest
from pathlib import Path
from compression.compression_manager import CompressionManager


@pytest.mark.parametrize("compression_type", ["zip", "tar"])
class TestCompressionIntegration:
    """
    Integration tests for the CompressionManager class.
    This suite tests the end-to-end functionality of compression and decompression for both zip and tar formats.
    """

    @pytest.fixture
    def compressor(self, compression_type, tmp_path):
        """
        Fixture to create a CompressionManager instance for testing
        and the temporary directory for testing.
        """
        # Create a temporary directory for testing
        test_folder = tmp_path / "test_folder"
        test_folder.mkdir()
        (test_folder / "file1.txt").write_text("This is a test file.")
        (test_folder / "file2.txt").write_text("This is another test file.")
        # Initialize the CompressionManager with the specified compression type
        compressor = CompressionManager(compression_type)
        return compressor, test_folder, compression_type

    def test_compression_or_decompression_unsupported_type(
        self, compression_type, caplog
    ):
        """
        Test that CompressionManager raises ValueError for an unsupported compression type.
        """
        with pytest.raises(ValueError) as excinfo:
            CompressionManager("unsupported")
        assert "Unsupported compression type: unsupported." in str(excinfo.value)
        assert "Unsupported compression type: unsupported." in caplog.text

    def test_compress_folder_success(self, compressor):
        """
        Test the compress_folder method of CompressionManager.
        """
        compressor, test_folder, compression_type = compressor
        archive_path = compressor.compress_folder(test_folder)
        assert archive_path.exists()
        assert archive_path.suffix == f".{compression_type}"
        assert not test_folder.exists()
        assert archive_path.is_file()
        assert archive_path.parent == test_folder.parent

    def test_compress_folder_failure(self, compressor):
        """
        Test that compress_folder raises an error when the folder does not exist.
        """
        compressor, _, _ = compressor
        with pytest.raises(ValueError):
            compressor.compress_folder(Path("non_existent_folder"))

    def test_decompress_folder_success(self, compressor):
        """
        Test the decompress_folder method of CompressionManager.
        """
        compressor, test_folder, _ = compressor
        archive_path = compressor.compress_folder(test_folder)
        extracted_folder = compressor.decompress_folder(archive_path)
        assert extracted_folder.exists()
        assert extracted_folder.is_dir()
        assert (extracted_folder / "file1.txt").exists()
        assert (extracted_folder / "file2.txt").exists()
        assert archive_path.stem == extracted_folder.name
        assert not archive_path.exists()

    def test_decompress_folder_failure(self, compressor):
        """
        Test that decompress_folder raises an error when the file does not exist.
        """
        compressor, _, _ = compressor
        with pytest.raises(ValueError):
            compressor.decompress_folder(Path("non_existent_file.tar"))

    def test_compress_bytes_success(self, compressor):
        """
        Test the compress_bytes method of CompressionManager.
        """
        compressor, _, _ = compressor
        data = b"Test data for compression"
        compressed_data = compressor.compress_bytes(data)
        assert isinstance(compressed_data, bytes)
        assert compressed_data != data

    def test_compress_bytes_failure(self, compressor):
        """
        Test that compress_bytes raises an error when the data is not valid.
        """
        compressor, _, _ = compressor
        with pytest.raises(ValueError):
            compressor.compress_bytes(None)

    def test_decompress_bytes_success(self, compressor):
        """
        Test the decompress_bytes method of CompressionManager.
        """
        compressor, _, _ = compressor
        data = b"Test data for compression"
        compressed_data = compressor.compress_bytes(data)
        decompressed_data = compressor.decompress_bytes(compressed_data)
        assert decompressed_data == data

    def test_decompress_bytes_failure(self, compressor):
        """
        Test that decompress_bytes raises an error when the data is not valid.
        """
        compressor, _, _ = compressor
        with pytest.raises(ValueError):
            compressor.decompress_bytes(None)
