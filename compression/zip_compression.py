# compression/zip_compression.py
import zipfile
from pathlib import Path
from compression.compression_base import CompressionBase
from utils.delete_folder import delete_folder


class ZipCompression(CompressionBase):
    """
    A class to handle zip compression and decompression.
    Inherits from CompressionBase and implements methods for zip-specific operations.
    """

    def compress_folder(self) -> str:
        """
        Compress the given folder into a .zip archive preserving the folder structure.
        Then remove the original folder.
        Returns:
            extension (str): The file extension used for the compressed file.
        """
        # Assign the folder path name
        folder_path = self.get_folder_from_processing_path()
        zip_folder_path = folder_path.with_suffix(f".{self.extension}")

        # Create a zip file and add the folder contents
        try:
            with zipfile.ZipFile(zip_folder_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file in folder_path.rglob("*"):
                    if file.is_file():
                        arcname = Path(folder_path.name) / file.relative_to(folder_path)
                        zipf.write(file, arcname=arcname)
            self.logger.info(f"Successfully created zip file: {zip_folder_path}")
        except Exception as e:
            self.logger.error(f"Failed to create zip file: {e}")
            raise RuntimeError("Failed to create zip file") from e

        # Remove the original folder after compression
        delete_folder(folder_path)

        return self.extension

    def decompress_folder(self) -> Path:
        """
        Decompress a .zip file to a folder preserving the original structure.
        it will extract to the same directory as the zip file
        Then remove the original zip file.
            Path: Path to the extracted folder.
        """
        # Get the zip file from processing path
        zip_path = self.get_compressed_file_from_processing_path()

        # Extract the zip file to a folder with the same name as the zip file
        try:
            with zipfile.ZipFile(zip_path, "r") as zipf:
                if zipf.testzip() is None:
                    zipf.extractall(path=self.processing_path)
                else:
                    self.logger.error(f"Corrupted zip file: {zip_path}")
                    raise ValueError("Corrupted zip file!")
            self.logger.info(f"Successfully extracted zip file: {zip_path}")
        except Exception as e:
            self.logger.error(f"Failed to extract zip file: {e}")
            raise RuntimeError("Failed to extract zip file") from e

        delete_folder(zip_path)

        return self.processing_path / zip_path.stem
