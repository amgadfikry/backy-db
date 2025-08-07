# databases/database_context.py
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv
import os
from logger.logger_manager import LoggerManager

load_dotenv()


class DatabaseContext:
    """
    context class for all database shared logic and states
    It easily make separation between abstracted database logic and the shared logic
    like the logger and the backup folder path.
    """

    def __init__(self, database_config: Dict):
        """
        Initialize the database with the given configuration
        and set the default processing path.
        Args:
            database_config (Dict): Configuration dictionary for the database.
                it should contain keys like host, port, user, password, db_name, etc.
                it has includes for the backup features according to the database type.
                this includes should be a dictionary with keys like tables, data.
                it will be managed by schema.
        """
        self.logger = LoggerManager.setup_logger("database")
        self.host = database_config.get("host", "localhost")
        self.port = database_config.get("port", 5432)
        self.user = database_config.get("user", "root")
        self.password = os.getenv("DB_PASSWORD")
        self.db_name = database_config.get("db_name")
        self.multiple_files = database_config.get("multiple_files", False)
        self.backup_folder_path: Path = Path(os.getenv("MAIN_BACKUP_PATH"))
        self.version = "Unknown"
        self.connection = None
