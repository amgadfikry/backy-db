# tests/compression/test_tar_compression.py
import tarfile
from pathlib import Path
from compression.tar_compression import TarCompression
import pytest
import io


class TestTarCompression:
    """
    Test suite for TarCompression class.
    """

    @pytest.fixture
    def setup(self):
        """
        Setup fixture to create a TarCompression instance.
        """
        tar_compression = TarCompression(compression_type="tar")
        return tar_compression

    def test_compress_folder_success(self, setup, tmp_path):
        """
        Test successful folder compression.
        """
        compressor = setup
        # Create a test folder with some files
        test_folder = tmp_path / "test_folder2"
        test_folder.mkdir(parents=True, exist_ok=True)
        (test_folder / "file1.txt").write_text("This is a test file.")
        (test_folder / "file2.txt").write_text("This is another test file.")
        # Compress the folder
        compressed_file = compressor.compress_folder(test_folder)
        # Check the results
        assert compressed_file.parent == test_folder.parent
        assert compressed_file.exists()
        assert compressed_file.suffix == ".tar"
        assert not test_folder.exists()

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
        assert "No valid folder path or directory provided for compression." in str(
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
        assert "No valid folder path or directory provided for compression." in str(
            exc_info.value
        )

    def test_compress_folder_not_a_directory(self, setup, caplog, tmp_path):
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
        assert "No valid folder path or directory provided for compression." in str(
            exc_info.value
        )

    def test_compress_folder_failure(self, setup, mocker, tmp_path, caplog):
        """
        Test compression failure due to an exception.
        """
        compressor = setup
        # Create a test folder
        folder_path = tmp_path / "test_folder1"
        folder_path.mkdir(parents=True, exist_ok=True)
        # Mock the tarfile.open to raise an exception
        mocker.patch("tarfile.open", side_effect=Exception("Mocked exception"))
        # Check if compression raises an error
        with pytest.raises(RuntimeError) as exc_info:
            compressor.compress_folder(folder_path)
        assert "Failed to compress tar file" in str(exc_info.value)
        assert "Failed to compress tar file: Mocked exception" in caplog.text

    def test_decompress_folder_success(self, setup, tmp_path):
        """
        Test successful folder decompression.
        """
        compressor = setup
        # Create a test tar file with some files
        test_folder = tmp_path / "test_folder3"
        test_folder.mkdir(parents=True, exist_ok=True)
        (test_folder / "file1.txt").write_text("This is a test file.")
        (test_folder / "file2.txt").write_text("This is another test file.")
        # Compress the folder to create a tar file
        compressed_file = test_folder.with_suffix(".tar")
        with tarfile.open(compressed_file, "w") as tarf:
            tarf.add(test_folder, arcname=test_folder.name)
        # Decompress the tar file
        extracted_folder = compressor.decompress_folder(compressed_file)
        # Check the results
        assert isinstance(extracted_folder, Path)
        assert extracted_folder.parent == compressed_file.parent
        assert extracted_folder.exists()
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
        assert "No valid tar file path provided for decompression." in caplog.text
        assert "No valid tar file path provided for decompression." in str(
            exc_info.value
        )

    def test_decompress_folder_nonexistent_path(self, setup, caplog):
        """
        Test decompression with a nonexistent folder path.
        """
        compressor = setup
        # Check if folder_path does not exist, raise an error
        nonexistent_file = Path(f"nonexistent_file.{compressor.extension}")
        with pytest.raises(ValueError) as exc_info:
            compressor.decompress_folder(nonexistent_file)
        assert "No valid tar file path provided for decompression." in caplog.text
        assert "No valid tar file path provided for decompression." in str(
            exc_info.value
        )

    def test_decompress_folder_not_a_file(self, setup, tmp_path, caplog):
        """
        Test decompression with a path that is not a file.
        """
        compressor = setup
        # Create a test folder instead of a file
        test_folder = tmp_path / "test_folder4"
        test_folder.mkdir(parents=True, exist_ok=True)
        # Check if folder_path is not a file, raise an error
        with pytest.raises(ValueError) as exc_info:
            compressor.decompress_folder(test_folder)
        assert "No valid tar file path provided for decompression." in caplog.text
        assert "No valid tar file path provided for decompression." in str(
            exc_info.value
        )

    def test_decompress_folder_failure(self, setup, mocker, tmp_path, caplog):
        """
        Test decompression failure due to an exception.
        """
        compressor = setup
        # Create a test tar file that is not valid
        tar_file_path = tmp_path / "test_file.tar"
        tar_file_path.write_text("This is not a valid tar file.")
        # Mock the tarfile.open to raise an exception
        mocker.patch("tarfile.open", side_effect=Exception("Mocked exception"))
        # Check if decompression raises an error
        with pytest.raises(RuntimeError) as exc_info:
            compressor.decompress_folder(tar_file_path)
        assert "Failed to extract tar file" in str(exc_info.value)
        assert "Failed to extract tar file: Mocked exception" in caplog.text

    def test_compress_bytes_success(self, setup):
        """
        Test successful byte compression.
        """
        compressor = setup
        # Create some data to compress
        data = b"This is some test data."
        compressed_data = compressor.compress_bytes(data)
        # Check the results
        assert isinstance(compressed_data, bytes)
        assert compressed_data != data

    def test_compress_bytes_empty_data(self, setup, caplog):
        """
        Test compression with empty data.
        """
        compressor = setup
        # Check if data is None or empty, raise an error
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
        # Mock the tarfile.open to raise an exception
        mocker.patch("tarfile.open", side_effect=Exception("Mocked exception"))
        # Check if compression raises an error
        with pytest.raises(RuntimeError) as exc_info:
            compressor.compress_bytes(data)
        assert "Failed to compress bytes with tar" in str(exc_info.value)
        assert "Failed to compress bytes with tar: Mocked exception" in caplog.text

    def test_decompress_bytes_success(self, setup):
        """
        Test successful byte decompression.
        """
        compressor = setup
        # Create some data to compress and then decompress
        data = b"This is some test data."
        # Compress the data into tar format
        with io.BytesIO() as buf:
            with tarfile.open(fileobj=buf, mode="w") as tarf:
                tar_info = tarfile.TarInfo(name="data")
                tar_info.size = len(data)
                tarf.addfile(tar_info, fileobj=io.BytesIO(data))
            compressed_data = buf.getvalue()
        # Decompress the data
        decompressed_data = compressor.decompress_bytes(compressed_data)
        # Check the results
        assert isinstance(decompressed_data, bytes)
        assert decompressed_data == data

    def test_decompress_bytes_empty_data(self, setup, caplog):
        """
        Test decompression with empty data.
        """
        compressor = setup
        # Check if data is None or empty, raise an error
        with pytest.raises(ValueError) as exc_info:
            compressor.decompress_bytes(b"")
        assert "No data provided for decompression." in caplog.text
        assert "No data provided for decompression." in str(exc_info.value)

    def test_decompress_bytes_if_no_members(self, setup, caplog):
        """
        Test decompression of bytes with no members in the tar archive.
        """
        compressor = setup
        # Create an empty tar file in memory
        empty_tar_data = io.BytesIO()
        with tarfile.open(fileobj=empty_tar_data, mode="w"):
            pass
        # Check if decompression raises an error
        with pytest.raises(ValueError) as exc_info:
            compressor.decompress_bytes(empty_tar_data.getvalue())
        assert "No files found in tar archive." in caplog.text
        assert "No files found in tar archive." in str(exc_info.value)

    def test_decompress_bytes_if_no_fileobj(self, setup, mocker, caplog):
        """
        Test decompression of bytes where the file object is None.
        """
        compressor = setup
        # Create an empty tar file in memory
        buff = io.BytesIO()
        with tarfile.open(fileobj=buff, mode="w") as tarf:
            tar_info = tarfile.TarInfo(name="data")
            tar_info.size = 0
            tarf.addfile(tar_info, fileobj=io.BytesIO(b""))
        # Mock the extractfile method to return None
        mocker.patch(
            "compression.tar_compression.tarfile.TarFile.extractfile", return_value=None
        )
        # Check if decompression raises an error
        with pytest.raises(ValueError) as exc_info:
            compressor.decompress_bytes(buff.getvalue())
        assert "Failed to extract file from tar archive." in caplog.text
        assert "Failed to extract file from tar archive." in str(exc_info.value)

    def test_decompress_bytes_failure(self, setup, mocker, tmp_path, caplog):
        """
        Test decompression failure due to an exception.
        """
        compressor = setup
        # Create a test tar file that is not valid
        tar_file_path = tmp_path / "test_file.tar"
        tar_file_path.write_text("This is not a valid tar file.")
        # Mock the tarfile.open to raise an exception
        mocker.patch("tarfile.open", side_effect=Exception("Mocked exception"))
        # Check if decompression raises an error
        with pytest.raises(RuntimeError) as exc_info:
            compressor.decompress_bytes(tar_file_path.read_bytes())
        assert "Failed to decompress bytes with tar" in str(exc_info.value)
        assert "Failed to decompress bytes with tar: Mocked exception" in caplog.text
