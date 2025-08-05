# tests/compression/test_compression_manager.py
import pytest
from pathlib import Path
from compression.compression_manager import CompressionManager


class TestCompressionManager:
    """
    Test suite for the CompressionManager class.
    This suite tests the compression and decompression functionalities for both zip and tar formats.
    """

    def test_valid_compression_type(self):
        """
        Test that CompressionManager initializes with a valid compression type.
        """
        manager = CompressionManager("zip")
        assert isinstance(manager, CompressionManager)
        manager = CompressionManager("tar")
        assert isinstance(manager, CompressionManager)

    def test_invalid_compression_type(self, caplog):
        """
        Test that CompressionManager raises ValueError for an unsupported compression type.
        """
        with pytest.raises(ValueError) as excinfo:
            CompressionManager("unsupported")
        assert "Unsupported compression type: unsupported." in str(excinfo.value)
        assert "Unsupported compression type: unsupported." in caplog.text

    def test_compress_folder(self, mocker):
        """
        Test the compress_folder method for both zip and tar formats.
        """
        # Test zip compression
        manager = CompressionManager("zip")
        folder_path = Path("/path/to/folder")
        mocker.patch.object(
            manager.compressor,
            "compress_folder",
            return_value=Path("/path/to/archive.zip"),
        )
        result = manager.compress_folder(folder_path)
        assert result == Path("/path/to/archive.zip")
        # Test tar compression
        manager = CompressionManager("tar")
        mocker.patch.object(
            manager.compressor,
            "compress_folder",
            return_value=Path("/path/to/archive.tar"),
        )
        result = manager.compress_folder(folder_path)
        assert result == Path("/path/to/archive.tar")

    def test_decompress_folder(self, mocker):
        """
        Test the decompress_folder method for both zip and tar formats.
        """
        # Test zip decompression
        manager = CompressionManager("zip")
        file_path = Path("/path/to/archive.zip")
        mocker.patch.object(
            manager.compressor,
            "decompress_folder",
            return_value=Path("/path/to/extracted_folder"),
        )
        result = manager.decompress_folder(file_path)
        assert result == Path("/path/to/extracted_folder")
        # Test tar decompression
        manager = CompressionManager("tar")
        file_path = Path("/path/to/archive.tar")
        mocker.patch.object(
            manager.compressor,
            "decompress_folder",
            return_value=Path("/path/to/extracted_folder"),
        )
        result = manager.decompress_folder(file_path)
        assert result == Path("/path/to/extracted_folder")

    def test_compress_bytes(self, mocker):
        """
        Test the compress_bytes method for both zip and tar formats.
        """
        # Test zip compression of bytes
        manager = CompressionManager("zip")
        data = b"test data"
        mocker.patch.object(
            manager.compressor, "compress_bytes", return_value=b"compressed data"
        )
        result = manager.compress_bytes(data)
        assert result == b"compressed data"
        # Test tar compression of bytes
        manager = CompressionManager("tar")
        mocker.patch.object(
            manager.compressor, "compress_bytes", return_value=b"compressed data"
        )
        result = manager.compress_bytes(data)
        assert result == b"compressed data"

    def test_decompress_bytes(self, mocker):
        """
        Test the decompress_bytes method for both zip and tar formats.
        """
        # Test zip decompression of bytes
        manager = CompressionManager("zip")
        data = b"compressed data"
        mocker.patch.object(
            manager.compressor, "decompress_bytes", return_value=b"decompressed data"
        )
        result = manager.decompress_bytes(data)
        assert result == b"decompressed data"
        # Test tar decompression of bytes
        manager = CompressionManager("tar")
        mocker.patch.object(
            manager.compressor, "decompress_bytes", return_value=b"decompressed data"
        )
        result = manager.decompress_bytes(data)
        assert result == b"decompressed data"
