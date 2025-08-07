# databases/database_base.py
from abc import ABC, abstractmethod
from databases.database_context import DatabaseContext
from typing import Iterator, Tuple


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
        """
        self.logger.error(
            f"connect method not implemented in subclass {self.__class__.__name__}"
        )
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def backup(self) -> Iterator[Tuple[str, str]]:
        """
        Perform a backup of the database.
        Returns:
            Iterator[Tuple[str, str]]: An iterator yielding tuples of feature or naming
            and the corresponding backup statement to it
        """
        self.logger.error(
            f"backup method not implemented in subclass {self.__class__.__name__}"
        )
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def restore(self, feature_data: Tuple[str, str]) -> None:
        """
        Restore the database from a backup file or files.
        Args:
            feature_data (Tuple[str, str]): A tuple containing the feature name and the
            corresponding statement.
        """
        self.logger.error(
            f"restore method not implemented in subclass {self.__class__.__name__}"
        )
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def close(self):
        """
        Close the database connection.
        """
        self.logger.error(
            f"close method not implemented in subclass {self.__class__.__name__}"
        )
        raise NotImplementedError("Subclasses must implement this method.")
