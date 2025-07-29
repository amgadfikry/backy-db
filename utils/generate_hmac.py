# utils/generate_hmac.py
from pathlib import Path
import hmac
import hashlib
from logger.logger_manager import LoggerManager

logger = LoggerManager.setup_logger("utils")

def compute_hmac(file_path: Path, key: bytes) -> str:
    """
    Compute HMAC for a file using SHA256.
    Args:
        file_path (Path): The path to the file for which to compute the HMAC.
        key (bytes): The key to use for HMAC computation.
    Returns:
        str: The computed HMAC as a hexadecimal string.
    """
    if not file_path.exists() or not file_path.is_file():
        logger.error(f"File {file_path} does not exist or is not a file.")
        raise FileNotFoundError(f"File {file_path} does not exist or is not a file.")
    if not key:
        logger.error("HMAC key must be provided.")
        raise ValueError("HMAC key must be provided.")

    try:
        h = hmac.new(key, digestmod=hashlib.sha256)
        with open(file_path, "rb") as f:
            while chunk := f.read(4096):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        logger.error(f"Error computing HMAC for {file_path}: {e}")
        raise RuntimeError(f"Failed to compute HMAC for {file_path}") from e
