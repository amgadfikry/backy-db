# /utils/path.py
import platform
from pathlib import Path
import os
from logger.logger_manager import LoggerManager

logger = LoggerManager.setup_logger("utils")
APP_NAME = "backydb"

def generate_main_backup_path(subfolder: str = "") -> Path:
    """
    Generate and create a default backup path based on the system and user
    Check if there is a subfolder specified, and if so, append it to the backup path.
    then ensure the path exists or create it if it does not.
    This function sets the environment variable `MAIN_BACKUP_PATH` to the generated path.
    Args:
        subfolder (str): Optional subfolder to append to the backup path.
    Returns:
        Path: The default backup path.
    """
    system = platform.system()

    if system == "Windows":
        base = Path.home() / "AppData" / "Roaming"
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".local" / "share"

    backup_path = base / APP_NAME

    if subfolder:
        backup_path /= subfolder

    backup_path.mkdir(parents=True, exist_ok=True)

    os.environ["MAIN_BACKUP_PATH"] = str(backup_path)

    return backup_path
