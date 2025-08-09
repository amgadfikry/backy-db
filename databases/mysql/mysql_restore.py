# databases/mysql/mysql_restore.py
from logger.logger_manager import LoggerManager
import mysql.connector
from pathlib import Path
from databases.mysql.mysql_utils import MySQLUtils


class MySQLRestore:
    """
    Class for restoring MySQL databases from backup files.
    It provides methods to restore the database from SQL files or statements.
    """

    def __init__(self, db_name: str, conflict: str = "skip"):
        """
        Initialize MySQLRestore with the logger.
        """
        self.logger = LoggerManager.setup_logger("database")
        self.conflict = conflict
        self.db_name = db_name

    def restore_file(self, cursor: mysql.connector.cursor, file_path: str):
        """
        Restore the database from a SQL file.
        It coverts the file into SQL statements and executes them one by one.
        Args:
            cursor (mysql.connector.cursor): The MySQL cursor to execute the command.
            file_path (str): The path to the SQL file to restore.
        Raises:
            RuntimeError: If any error occurs during the restore process.
        """
        # check if the file exists and is readable
        if (
            not file_path
            or not Path(file_path).exists()
            or not Path(file_path).is_file()
        ):
            self.logger.error(f"File {file_path} does not exist or is not a file.")
            raise FileNotFoundError(
                f"File {file_path} does not exist or is not a file."
            )

        for stmt in MySQLUtils.convert_mysql_file_to_statments(file_path):
            self.execute_with_conflict_handling(cursor, stmt)

    def restore_statement(self, cursor: mysql.connector.cursor, statement: str):
        """
        Restore the database from a SQL statement.
        Args:
            cursor (mysql.connector.cursor): The MySQL cursor to execute the command.
            statement (str): The SQL statement to execute.
        """
        statement = MySQLUtils().clean_single_sql_statement(statement)
        self.execute_with_conflict_handling(cursor, statement)

    def execute_with_conflict_handling(
        self, cursor: mysql.connector.cursor, statement: str
    ):
        """
        Execute a SQL statement with conflict handling.
        If the conflict mode is 'clean', it will clean the database before executing.
        If the conflict mode is 'skip', it will skip the statement if a conflict occurs.
        If the conflict mode is 'abort', it will raise an error if a conflict occurs.
        Args:
            cursor (mysql.connector.cursor): The MySQL cursor to execute the command.
            statement (str): The SQL statement to execute.
        Raises:
            RuntimeError: If any error occurs during the execution.
        """
        try:
            if not statement.strip():
                self.logger.warning("Empty statement, skipping execution.")
                return
            cursor.execute(statement)
            while cursor.nextset():
                pass
        except mysql.connector.Error as e:
            if self.conflict == "skip":
                self.logger.warning(f"Conflict occurred: {e}. Skipping statement.")
            elif self.conflict == "abort":
                self.logger.error(f"Conflict occurred: {e}. Aborting operation.")
                raise e
            else:
                self.logger.error(f"Unknown conflict handling mode: {self.conflict}")
                raise ValueError(f"Unknown conflict handling mode: {self.conflict}")
