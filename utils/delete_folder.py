# utils/delete_folder.py
import shutil
from pathlib import Path
from logger.logger_manager import LoggerManager

logger = LoggerManager.setup_logger("utils")


def delete_folder(folder_path: Path) -> None:
    """
    Deletes a folder and all its contents.
    Args:
        folder_path (Path): The path to the folder to be deleted.
    Raises:
        Exception: If an error occurs during deletion.
    """
    try:
        if folder_path.exists() and folder_path.is_dir():
            shutil.rmtree(folder_path)
        else:
            logger.warning(
                f"Folder {folder_path} does not exist or is not a directory."
            )
    except Exception as e:
        logger.error(f"Error deleting folder {folder_path}: {e}")
        raise RuntimeError(f"Failed to delete folder {folder_path}") from e
