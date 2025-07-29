# utils/generate_checksum.py
import hashlib
from pathlib import Path
from logger.logger_manager import LoggerManager

logger = LoggerManager.setup_logger("utils")

def generate_sha256(path: Path) -> str:
    """
    Generate SHA-256 checksum for a file at the given path.
    Args:
        path (Path): The path to the file for which to generate the checksum.
    Returns:
        str: The SHA-256 checksum of the file.
    """
    if not path.exists() or not path.is_file():
        logger.error(f"File {path} does not exist or is not a file.")
        raise FileNotFoundError(f"File {path} does not exist or is not a file.")
    
    try:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        logger.error(f"Error generating SHA-256 checksum for {path}: {e}")
        raise RuntimeError(f"Failed to generate checksum for {path}") from e
