# tests/compression/test_compression_base.py
import pytest
from compression.compression_base import CompressionBase
from pathlib import Path


class MockCompression(CompressionBase):
    """Mock class for CompressionBase to test abstract methods."""

    def compress_folder(self, folder_path: Path) -> Path:
        """Mock implementation of compress_folder."""
        return super().compress_folder(folder_path)

    def decompress_folder(self, file_path: Path) -> Path:
        """Mock implementation of decompress_folder."""
        return super().decompress_folder(file_path)

    def compress_bytes(self, data: bytes) -> bytes:
        """Mock implementation of compress_bytes."""
        return super().compress_bytes(data)

    def decompress_bytes(self, data: bytes) -> bytes:
        """Mock implementation of decompress_bytes."""
        return super().decompress_bytes(data)


class TestCompressionBase:
    """
    Test cases for the CompressionBase abstract class.
    """

    @pytest.fixture
    def setup(self):
        """
        Fixture to create a MockCompression instance.
        """
        return MockCompression(compression_type="zip")

    @pytest.mark.parametrize(
        "method_name",
        ["compress_folder", "decompress_folder", "compress_bytes", "decompress_bytes"],
    )
    def test_abstracted_methods(self, setup, method_name):
        """
        Test that abstract methods raise NotImplementedError with the correct message.
        """
        mock_compression = setup
        # Check if the method exists and call it to ensure it raises NotImplementedError
        with pytest.raises(NotImplementedError) as exc_info:
            method = getattr(mock_compression, method_name)
            if method_name in ["compress_folder", "decompress_folder"]:
                method(Path("/some/path"))
            else:
                method(b"some data")
        assert str(exc_info.value) == "Subclasses must implement this method."

    def test_compression_type(self, setup):
        """
        Test that the compression type is set correctly.
        """
        mock_compression = setup
        assert mock_compression.compression_type == "zip"
        assert mock_compression.extension == ".zip"

    def test_wrong_compression_type(self):
        """
        Test that an unsupported compression type raises a ValueError.
        """
        with pytest.raises(ValueError) as exc_info:
            MockCompression(compression_type="unsupported")
        assert str(exc_info.value) == "Unsupported compression type: unsupported"
