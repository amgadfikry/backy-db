# databases/mysql/mysql_manager.py
import mysql.connector
from typing import List, Iterator, Tuple
from databases.database_base import DatabaseBase
from databases.mysql.mysql_streaming import MySQLStreaming
from databases.mysql.mysql_utils import MySQLUtils
from databases.mysql.mysql_restore import MySQLRestore


class MySQLManager(DatabaseBase):
    """
    Class for managing MySQL database connections and operations.
    It extends the DatabaseBase class and implements methods for connecting,
    backing up, restoring, and closing the connection to the MySQL database.
    """

    def __init__(self, database_config: dict):
        """
        Initialize MySQLManager with the database configuration.
        Args:
            database_config (dict): Configuration dictionary containing MySQL connection parameters.
        """
        super().__init__(database_config)
        default_features = [
            "tables",
            "data",
            "views",
            "functions",
            "procedures",
            "triggers",
            "events",
        ]
        self.features = {
            key: database_config.get("features", {}).get(key, False)
            for key in default_features
        }
        self.restore_mode = database_config.get("restore_mode")
        self.conflict_mode = database_config.get("conflict_mode", "skip")
        self.streaming = MySQLStreaming()
        self.restoring = MySQLRestore(self.db_name, self.conflict_mode)

    def connect(self):
        """
        Connect to the MySQL database using the provided configuration.
        and set the version attribute.
        Raises:
            ConnectionError: If the connection to the MySQL database fails.
        Returns:
            None
        """
        try:
            # Connect to the MySQL database
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.db_name,
            )

            # Set the version of mysql
            self.version = self.connection.server_info

            self.logger.info(
                f"Connected to MySQL database successfully: version {self.version}"
            )
        except Exception as e:
            self.logger.error(f"Failed to connect to MySQL database: {e}")
            raise ConnectionError(f"Failed to connect to MySQL database: {e}")

    def backup(self) -> Iterator[Tuple[str, str]]:
        """
        Perform a backup of the MySQL database.
        It streams the SQL statements for various features of the database
        such as tables, data, views, functions, procedures, triggers, and events.
        It can yield the SQL statements in a single feature or multiple features.
        Raises:
            RuntimeError: If any error occurs during the backup process.
        Returns:
            Iterator[Tuple[str, str]]: An iterator that yields tuples containing the feature name and
            the corresponding SQL statement for backup.
        """
        ordered_features: List[tuple[str, callable]] = [
            ("tables", self.streaming.stream_tables_statements),
            ("data", self.streaming.stream_data_statements),
            ("views", self.streaming.stream_views_statements),
            ("functions", self.streaming.stream_functions_statements),
            ("procedures", self.streaming.stream_procedures_statements),
            ("triggers", self.streaming.stream_triggers_statements),
            ("events", self.streaming.stream_events_statements),
        ]

        # If not multiple_files, create the opening SQL statements only once
        if not self.multiple_files:
            yield "full", MySQLUtils.create_mysql_file_opening(self.db_name)

        cursor = self.connection.cursor()
        # Filter out features that are not enabled
        for feature, method in ordered_features:
            curr_feature = feature if self.multiple_files else "full"
            if not self.features.get(feature):
                continue

            # If multiple_files is True, create the opening SQL statements for each feature
            if self.multiple_files:
                yield feature, MySQLUtils.create_mysql_file_opening(
                    self.db_name
                ) + f"-- Backup for {feature.capitalize()}\n\n"

            self.logger.info(f"Starting backup for {feature}...")
            # Call the method to yield the SQL statements for the feature
            try:
                for statement in method(cursor):
                    yield curr_feature, statement
            except Exception as e:
                self.logger.error(f"Error during getting {feature} backup: {e}")
                raise RuntimeError(f"Error during getting {feature} backup: {e}")

    def restore(self, feature_data: Tuple[str, str]):
        """
        This method restores the MySQL database from a backup file or statement.
        It connects to the database, checks the active features, and restores
        the database based on the restore mode and conflict handling.
        Args:
            backup_file (str): The path to the backup folder containing the files
        """
        # connect to the database
        cursor = self.connection.cursor()

        # Select the active features based on the configuration
        active_features = [
            feature for feature in self.features if self.features[feature]
        ]
        feature, data = feature_data

        # If the feature is not active, skip the restore
        if feature != "full" and feature not in active_features:
            self.logger.info(f"Skipping restore for {feature} as it is not active.")
            return
        try:
            # If the restore mode is 'file', restore from the file
            if self.restore_mode == "file":
                self.restoring.restore_file(cursor, data)
            # If the restore mode is 'statement', restore from the statement
            elif self.restore_mode == "statement":
                self.restoring.restore_statement(cursor, data)
            # If the restore mode is not implemented, raise an error
            else:
                raise NotImplementedError(
                    f"Restore mode '{self.restore_mode}' is not implemented for MySQLDatabase"
                )
        except Exception as e:
            if isinstance(e, NotImplementedError):
                raise e
            self.logger.error(f"Error during restoring {feature} backup: {e}")
            raise RuntimeError(f"Error during restoring {feature} backup: {e}")

    def close(self):
        """
        Close the MySQL database connection.
        """
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None
            self.logger.info("MySQL database connection closed.")
        else:
            self.logger.warning("No active MySQL database connection to close.")
