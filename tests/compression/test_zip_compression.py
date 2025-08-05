# tests/compression/test_zip_compression.py
import zlib
from pathlib import Path
from compression.zip_compression import ZipCompression
import pytest
import zipfile


class TestZipCompression:
    """
    Test suite for ZipCompression class.
    """

    @pytest.fixture
    def setup(self):
        """
        Setup fixture to create a ZipCompression instance.
        """
        zip_compression = ZipCompression(compression_type="zip")
        return zip_compression

    def test_compress_folder_success(self, setup, tmp_path):
        """
        Test successful folder compression.
        """
        compressor = setup
        # Create a test folder with some files
        test_folder = tmp_path / "test_folder"
        test_folder.mkdir(parents=True, exist_ok=True)
        (test_folder / "file1.txt").write_text("This is a test file.")
        (test_folder / "file2.txt").write_text("This is another test file.")
        # Compress the folder
        compressed_file = compressor.compress_folder(test_folder)
        # Check results
        assert compressed_file.exists()
        assert compressed_file.suffix == ".zip"
        assert not test_folder.exists()
        assert compressed_file.parent == test_folder.parent

    def test_compress_folder_None_path(self, setup, caplog):
        """
        Test compression with an invalid folder path.
        """
        compressor = setup
        # Check if folder_path is None, raise an error
        with pytest.raises(ValueError) as exc_info:
            compressor.compress_folder(None)
        assert (
            "No valid folder path or directory provided for compression." in caplog.text
        )
        assert "Not a valid folder path or directory provided for compression." in str(
            exc_info.value
        )

    def test_compress_folder_nonexistent_path(self, setup, tmp_path, caplog):
        """
        Test compression with a nonexistent folder path.
        """
        compressor = setup
        # Check if folder_path does not exist, raise an error
        nonexistent_folder = tmp_path / "nonexistent_folder"
        with pytest.raises(ValueError) as exc_info:
            compressor.compress_folder(nonexistent_folder)
        assert (
            "No valid folder path or directory provided for compression." in caplog.text
        )
        assert "Not a valid folder path or directory provided for compression." in str(
            exc_info.value
        )

    def test_compress_folder_not_a_directory(self, setup, tmp_path, caplog):
        """
        Test compression with a path that is not a directory.
        """
        compressor = setup
        # Create a test file instead of a directory
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        # Check if folder_path is not a directory, raise an error
        with pytest.raises(ValueError) as exc_info:
            compressor.compress_folder(test_file)
        assert (
            "No valid folder path or directory provided for compression." in caplog.text
        )
        assert "Not a valid folder path or directory provided for compression." in str(
            exc_info.value
        )

    def test_compress_folder_failure(self, setup, mocker, caplog, tmp_path):
        """
        Test compression failure due to an exception.
        """
        compressor = setup
        # Create a test folder
        folder_path = tmp_path / "folder_path"
        folder_path.mkdir(parents=True, exist_ok=True)
        # Mock the zipfile.ZipFile to raise an exception
        mocker.patch("zipfile.ZipFile", side_effect=Exception("Mocked exception"))
        with pytest.raises(RuntimeError) as exc_info:
            compressor.compress_folder(folder_path)
        assert "Failed to compress folder: Mocked exception" in str(exc_info.value)
        assert "Failed to compress folder: Mocked exception" in caplog.text

    def test_decompress_folder_success(self, setup, tmp_path):
        """
        Test successful folder decompression.
        """
        compressor = setup
        # Create a test folder with some files
        test_folder = tmp_path / "test_folder"
        test_folder.mkdir(parents=True, exist_ok=True)
        (test_folder / "file1.txt").write_text("This is a test file.")
        (test_folder / "file2.txt").write_text("This is another test file.")
        # Compress the folder to create a zip file
        compressed_file = test_folder.with_suffix(".zip")
        with zipfile.ZipFile(compressed_file, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in test_folder.rglob("*"):
                if file.is_file():
                    zipf.write(file, arcname=file.relative_to(test_folder))
        # Decompress the zip file
        extracted_folder = compressor.decompress_folder(compressed_file)
        # Check results
        assert isinstance(extracted_folder, Path)
        assert extracted_folder.exists()
        assert extracted_folder.name == test_folder.name
        assert extracted_folder.parent == compressed_file.parent
        assert (extracted_folder / "file1.txt").exists()
        assert (extracted_folder / "file2.txt").exists()
        assert not compressed_file.exists()

    def test_decompress_folder_None_path(self, setup, caplog):
        """
        Test decompression with an invalid folder path.
        """
        compressor = setup
        # Check if folder_path is None, raise an error
        with pytest.raises(ValueError) as exc_info:
            compressor.decompress_folder(None)
        assert (
            "No valid zip file path or directory provided for decompression."
            in caplog.text
        )
        assert (
            "Not a valid zip file path or directory provided for decompression."
            in str(exc_info.value)
        )

    def test_decompress_folder_nonexistent_path(self, setup, tmp_path, caplog):
        """
        Test decompression with a nonexistent folder path.
        """
        compressor = setup
        # Check if folder_path does not exist, raise an error
        nonexistent_file = tmp_path / "nonexistent.zip"
        with pytest.raises(ValueError) as exc_info:
            compressor.decompress_folder(nonexistent_file)
        assert (
            "No valid zip file path or directory provided for decompression."
            in caplog.text
        )
        assert (
            "Not a valid zip file path or directory provided for decompression."
            in str(exc_info.value)
        )

    def test_decompress_folder_not_a_file(self, setup, tmp_path, caplog):
        """
        Test decompression with a path that is not a file.
        """
        compressor = setup
        # Create a test folder instead of a file
        test_folder = tmp_path / "test_folder"
        test_folder.mkdir(parents=True, exist_ok=True)
        # Check if folder_path is not a file, raise an error
        with pytest.raises(ValueError) as exc_info:
            compressor.decompress_folder(test_folder)
        assert (
            "No valid zip file path or directory provided for decompression."
            in caplog.text
        )
        assert (
            "Not a valid zip file path or directory provided for decompression."
            in str(exc_info.value)
        )

    def test_decompress_folder_not_a_zip_file(self, setup, tmp_path, caplog):
        """
        Test decompression with a file that is not a zip file.
        """
        compressor = setup
        # Create a test file that is not a zip file
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file.")
        # Check if folder_path is not a zip file, raise an error
        with pytest.raises(ValueError) as exc_info:
            compressor.decompress_folder(test_file)
        assert (
            "No valid zip file path or directory provided for decompression."
            in caplog.text
        )
        assert (
            "Not a valid zip file path or directory provided for decompression."
            in str(exc_info.value)
        )

    def test_decompress_folder_corrupted_zip(self, setup, mocker, tmp_path, caplog):
        """
        Test decompression with a corrupted zip file.
        """
        compressor = setup
        # Create a corrupted zip file
        corrupted_zip = tmp_path / "corrupted.zip"
        with zipfile.ZipFile(corrupted_zip, "w") as zipf:
            zipf.writestr("file.txt", "dummy")
        # Mock the testzip method to simulate a corrupted zip file
        mock_testzip = mocker.patch(
            "zipfile.ZipFile.testzip", return_value="corrupted_file.txt"
        )
        # Check if decompression raises an error for a corrupted zip file
        with pytest.raises(ValueError) as exc_info:
            compressor.decompress_folder(corrupted_zip)
        assert "Corrupted zip file" in caplog.text
        assert "Corrupted zip file" in str(exc_info.value)
        mock_testzip.assert_called_once()

    def test_decompress_folder_failure(self, setup, mocker, tmp_path, caplog):
        """
        Test decompression failure due to an exception.
        """
        compressor = setup
        # Create a test zip file
        zip_file_path = tmp_path / "test.zip"
        zip_file_path.write_text("This is not a valid zip file.")
        # Mock the zipfile.ZipFile to raise an exception
        mocker.patch("zipfile.ZipFile", side_effect=Exception("Mocked exception"))
        # Check if decompression raises an error
        with pytest.raises(RuntimeError) as exc_info:
            compressor.decompress_folder(zip_file_path)
        assert "Failed to extract zip file: Mocked exception" in str(exc_info.value)
        assert "Failed to extract zip file: Mocked exception" in caplog.text

    def test_compress_bytes_success(self, setup):
        """
        Test successful bytes compression.
        """
        compressor = setup
        # Compress some bytes
        data = b"This is some test data."
        compressed_data = compressor.compress_bytes(data)
        # Check results
        assert isinstance(compressed_data, bytes)
        assert compressed_data != data

    def test_compress_bytes_None_data(self, setup, caplog):
        """
        Test compression with None data.
        """
        compressor = setup
        # Check if data is None, raise an error
        with pytest.raises(ValueError) as exc_info:
            compressor.compress_bytes(None)
        assert "No data provided for compression." in caplog.text
        assert "No data provided for compression." in str(exc_info.value)

    def test_compress_bytes_empty_data(self, setup, caplog):
        """
        Test compression with empty data.
        """
        compressor = setup
        # Check if data is empty, raise an error
        with pytest.raises(ValueError) as exc_info:
            compressor.compress_bytes(b"")
        assert "No data provided for compression." in caplog.text
        assert "No data provided for compression." in str(exc_info.value)

    def test_compress_bytes_failure(self, setup, mocker, caplog):
        """
        Test compression failure due to an exception.
        """
        compressor = setup
        # Create some data to compress
        data = b"This is some test data."
        # Mock the zlib.compress to raise an exception
        mocker.patch("zlib.compress", side_effect=Exception("Mocked exception"))
        # Check if compression raises an error
        with pytest.raises(RuntimeError) as exc_info:
            compressor.compress_bytes(data)
        assert "Failed to compress bytes with zlib: Mocked exception" in str(
            exc_info.value
        )
        assert "Failed to compress bytes with zlib: Mocked exception" in caplog.text

    def test_decompress_bytes_success(self, setup):
        """
        Test successful bytes decompression.
        """
        compressor = setup
        # Create some data to compress and then decompress
        data = b"This is some test data."
        compressed_data = zlib.compress(data)
        decompressed_data = compressor.decompress_bytes(compressed_data)
        # Check results
        assert isinstance(decompressed_data, bytes)
        assert decompressed_data == data

    def test_decompress_bytes_None_data(self, setup, caplog):
        """
        Test decompression with None data.
        """
        compressor = setup
        # Check if data is None, raise an error
        with pytest.raises(ValueError) as exc_info:
            compressor.decompress_bytes(None)
        assert "No data provided for decompression." in caplog.text
        assert "No data provided for decompression." in str(exc_info.value)

    def test_decompress_bytes_empty_data(self, setup, caplog):
        """
        Test decompression with empty data.
        """
        compressor = setup
        # Check if data is empty, raise an error
        with pytest.raises(ValueError) as exc_info:
            compressor.decompress_bytes(b"")
        assert "No data provided for decompression." in caplog.text
        assert "No data provided for decompression." in str(exc_info.value)

    def test_decompress_bytes_failure(self, setup, mocker, caplog):
        """
        Test decompression failure due to an exception.
        """
        compressor = setup
        # Create some data to compress
        data = b"This is some test data."
        compressed_data = zlib.compress(data)
        # Mock the zlib.decompress to raise an exception
        mocker.patch("zlib.decompress", side_effect=Exception("Mocked exception"))
        # Check if decompression raises an error
        with pytest.raises(RuntimeError) as exc_info:
            compressor.decompress_bytes(compressed_data)
        assert "Failed to decompress bytes with zlib: Mocked exception" in str(
            exc_info.value
        )
        assert "Failed to decompress bytes with zlib: Mocked exception" in caplog.text
