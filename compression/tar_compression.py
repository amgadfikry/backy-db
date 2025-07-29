# compression/tar_compression.py
import tarfile
from pathlib import Path
from compression.compression_base import CompressionBase
from utils.delete_folder import delete_folder


class TarCompression(CompressionBase):
    """
    A class to handle tar compression and decompression.
    Inherits from CompressionBase and implements methods for tar-specific operations.
    """
    TAR_READ_MODES = {
    'tar': 'r',
    'tar.gz': 'r:gz',
    }

    TAR_WRITE_MODES = {
    'tar': 'w',
    'tar.gz': 'w:gz',
    }

    def compress_folder(self) -> str:
        """
        Compress the given folder into a .tar archive preserving the folder structure.
        Then remove the original folder.
        Returns:
            extension (str): The file extension used for the compressed file.
        """
        # Assign the folder path name
        folder_path = self.get_folder_from_processing_path()
        tar_folder_path = folder_path.with_suffix(f".{self.extension}")
        tar_type = self.TAR_WRITE_MODES[self.extension]

        # Create a tar file and add the folder contents
        try:
            with tarfile.open(tar_folder_path, tar_type) as tarf:
                tarf.add(folder_path, arcname=folder_path.name)
            self.logger.info(f"Successfully created tar file: {tar_folder_path}")
        except Exception as e:
            self.logger.error(f"Failed to create tar file: {e}")
            raise RuntimeError("Failed to create tar file") from e

        # Remove the original folder after compression
        delete_folder(folder_path)

        return self.extension

    def decompress_folder(self) -> Path:
        """
        Decompress a .tar file to a folder preserving the original structure.
        it will extract to the same directory as the tar file
        Then remove the original tar file.
            Path: Path to the extracted folder.
        """
        # Get the tar file from processing path
        tar_path = self.get_compressed_file_from_processing_path()
        tar_type = self.TAR_READ_MODES[self.extension]

        # Extract the tar file to a folder with the same name as the tar file
        try:
            with tarfile.open(tar_path, tar_type) as tarf:
                tarf.extractall(path=self.processing_path)
            self.logger.info(f"Successfully extracted tar file: {tar_path}")
        except Exception as e:
            self.logger.error(f"Failed to extract tar file: {e}")
            raise RuntimeError("Failed to extract tar file") from e
        delete_folder(tar_path)

        return self.processing_path / tar_path.stem
