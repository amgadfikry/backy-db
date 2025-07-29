# compression/compression_manger.py
from compression.zip_compression import ZipCompression
from compression.tar_compression import TarCompression
from pathlib import Path


class CompressionManager:
    """
    A class to manage compression and decompression of files.
    This class provides methods to compress a folder into a specific format (zip or tar) and decompress files.
    """
    def __init__(self, compression_type):
        """
        Initialize the CompressionManager with a specified compression type.
        Args:
            compression_type (str): Type of compression to use ('zip' or 'tar').
        """
        types = {
            'zip': ZipCompression,
            'tar': TarCompression,
            'targz': TarCompression,
        }
        self.compressor = types[compression_type](compression_type)

    def compress(self) -> Path:
        """
        Compress the folder in the processing path using the specified compression type.
        Returns:
            Path: Path to the created archive file.
        """
        return self.compressor.compress_folder()

    def decompress(self) -> Path:
        """
        Decompress the file in the processing path using the specified compression type.
        Returns:
            Path: Path to the extracted folder.
        """
        return self.compressor.decompress_folder()
