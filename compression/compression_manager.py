# compression/compression_manger.py
from compression.zip_compression import ZipCompression
from compression.tar_compression import TarCompression
from pathlib import Path
from logger.logger_manager import LoggerManager


class CompressionManager:
    """
    A class to manage compression and decompression of files.
    This class provides methods to compress a folder into a specific format eg. zip or tar,
    decompress files, and handle byte data compression and decompression.
    """

    # Supported compression types
    SUPPORTED_TYPES = {
        "zip": ZipCompression,
        "tar": TarCompression,
    }

    def __init__(self, compression_type):
        """
        Initialize the CompressionManager with a specified compression type.
        Args:
            compression_type (str): Type of compression to use ('zip' or 'tar').
        Raises:
            ValueError: If the compression_type is not supported.
        """
        self.logger = LoggerManager.setup_logger("compression")
        if not compression_type or compression_type not in self.SUPPORTED_TYPES:
            self.logger.error(f"Unsupported compression type: {compression_type}.")
            raise ValueError(f"Unsupported compression type: {compression_type}.")
        self.compressor = self.SUPPORTED_TYPES[compression_type](compression_type)

    def compress_folder(self, folder_path: Path) -> Path:
        """
        Compress the folder in the processing path using the specified compression type.
        This method will create an archive file in the same directory as the folder.
        It will remove the original folder after compression.
        Args:
            folder_path (Path): Path to the folder to compress.
        Returns:
            Path: Path to the created archive file.
        """
        return self.compressor.compress_folder(folder_path)

    def decompress_folder(self, folder_path: Path) -> Path:
        """
        Decompress a compressed file to a folder preserving the original structure.
        The decompressed folder will be created in the same directory as the compressed file.
        It will remove the original compressed file after decompression.
        Args:
            folder_path (Path): Path to the folder to decompress.
        Returns:
            Path: Path to the extracted folder.
        """
        return self.compressor.decompress_folder(folder_path)

    def compress_bytes(self, data: bytes) -> bytes:
        """
        Compress the given bytes using the specified compression type.
        Args:
            data (bytes): The data to compress.
        Returns:
            bytes: The compressed data.
        """
        return self.compressor.compress_bytes(data)

    def decompress_bytes(self, data: bytes) -> bytes:
        """
        Decompress the given bytes using the specified compression type.
        Args:
            data (bytes): The compressed data to decompress.
        Returns:
            bytes: The decompressed data.
        """
        return self.compressor.decompress_bytes(data)
