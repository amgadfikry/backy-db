# databases/database_manager.py
from databases.mysql.mysql_manager import MySQLManager
from logger.logger_manager import LoggerManager
from typing import Iterator, Tuple


class DatabaseManager:
    """
    Manages the database operations for the Backy project.
    This class is responsible for providing a unified interface for database operations,
    including backup and restore functionalities.
    It supports multiple database types, allowing for extensibility in the future.
    """

    DATABASES = {
        "mysql": MySQLManager,
    }

    def __init__(self, database_config: dict):
        """
        Initialize the DatabaseManager with a specific database configuration.
        args:
            database_config (dict): Configuration dictionary for the database.
        Raises:
            ValueError: If the database type is not supported.
        """
        self.logger = LoggerManager.setup_logger("database")
        database_type = database_config.get("db_type").lower()
        if database_type not in self.DATABASES:
            self.logger.error(f"Unsupported database type: {database_type}")
            raise ValueError(f"Unsupported database type: {database_type}")
        self.db = self.DATABASES[database_type](database_config)
        self.feature = None

    def __enter__(self):
        """
        This method is called when the object is used in a 'with' statement.
        It establishes a connection to the database.
        Returns:
            self: The instance of the DatabaseManager.
        """
        self.db.connect()
        self.db.connection.start_transaction()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        This method is called when the 'with' statement is exited.
        It closes the database connection.
        """
        self.db.connection.commit()
        self.db.close()

    def connect(self):
        """
        Connect to the database.
        This method is called to establish a connection to the database.
        """
        self.db.connect()
        self.db.connection.start_transaction()

    def close(self):
        """
        Close the database connection.
        This method is called to close the connection to the database.
        """
        self.db.connection.commit()
        self.db.close()

    def backup(self) -> Iterator[Tuple[str, str]]:
        """
        This method connects to the database, retrieves the backup statements,
        and yields them one by one.
        It is designed to be used in a streaming context, allowing for efficient memory usage.
        Returns:
            Iterator[Tuple[str, str]]: An iterator yielding tuples of feature names and their corresponding  statements.
        """
        try:
            # yield the backup statements from the database
            for feature, statement in self.db.backup():
                yield feature, statement
        except Exception as e:
            self.logger.error(f"Error during backup process: {e}")
            raise RuntimeError(f"Error during backup process: {e}")

    def restore(self, feature_data: Tuple[str, str]):
        """
        This method restores the database from a backup file or statement.
        It connects to the database, checks the active features, and restores
        the database based on the restore mode and conflict handling.
        Args:
            feature_data (Tuple[str, str]): A tuple containing the feature name and the corresponding SQL statement or file path.
        """
        try:
            feature, data = feature_data
            if self.feature is None or self.feature != feature:
                self.db.connection.commit()
                self.feature = feature
            # Restore the database using the provided feature data
            self.db.restore(feature_data)
        except Exception as e:
            self.db.connection.rollback()
            self.logger.error(f"Error during restore process: {e}")
            raise RuntimeError(f"Error during restore process: {e}")
