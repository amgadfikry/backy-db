# databases/database_base.py
from pathlib import Path
from abc import ABC, abstractmethod
from databases.database_context import DatabaseContext


class DatabaseBase(ABC, DatabaseContext):
    """
    Base class for all database implementations in the Backy project.
    This class defines the common interface and methods that all database
    classes should implement.
    """

    @abstractmethod
    def connect(self):
        """
        Connect to the database using the provided configuration.
        This method should be implemented by subclasses.
        """
        self.logger.error(
            f"connect method not implemented in subclass {self.__class__.__name__}"
        )
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def backup(self, timestamp: str) -> Path:
        """
        Perform a backup of the database.
        This method should be implemented by subclasses.
        """
        self.logger.error(
            f"backup method not implemented in subclass {self.__class__.__name__}"
        )
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def restore(self, backup_file: Path):
        """
        Restore the database from a backup file.
        Args:
            backup_file (Path): The path to the backup file.
        This method should be implemented by subclasses.
        """
        self.logger.error(
            f"restore method not implemented in subclass {self.__class__.__name__}"
        )
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def close(self):
        """
        Close the database connection.
        This method should be implemented by subclasses.
        """
        self.logger.error(
            f"close method not implemented in subclass {self.__class__.__name__}"
        )
        raise NotImplementedError("Subclasses must implement this method.")
