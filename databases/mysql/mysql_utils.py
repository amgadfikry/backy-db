# databases/mysql/mysql_utils.py
from typing import Tuple, Any, Iterator
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID
import json


class MySQLUtils:
    """
    Utility class for MySQL-specific operations.
    """

    @staticmethod
    def create_mysql_file_opening(db_name: str) -> str:
        """
        create the opening statements for the MySQL file
        that will be used to backup the database
        Args:
            db_name (str): The name of the database to be backed up.
        Returns:
            String: The opening MySQL statements.
        """
        return (
            f"-- Backup for {db_name}\n"
            f"CREATE DATABASE IF NOT EXISTS `{db_name}`;\n"
            f"USE `{db_name}`;\n\n"
        )

    @staticmethod
    def raw_to_mysql_values(row: Tuple[Any, ...]) -> str:
        """
        Convert a row of data into a MySQL-compatible string representation.
        Args:
            row (tuple): A tuple containing the values of the row.
        Returns:
            str: A string representation of the row values suitable for MySQL insertion.
        """

        def format_value(val: Any) -> str:
            if val is None:
                return "NULL"
            elif isinstance(val, bool):
                return "1" if val else "0"
            elif isinstance(val, (int, float, Decimal)):
                return str(val)
            elif isinstance(val, datetime):
                return f"'{val.isoformat(sep=' ', timespec='seconds')}'"
            elif isinstance(val, time):
                return f"'{val.isoformat(timespec='seconds')}'"
            elif isinstance(val, date):
                return f"'{val.isoformat()}'"
            elif isinstance(val, (bytes, bytearray)):
                return f"X'{val.hex()}'"
            elif isinstance(val, UUID):
                return f"'{str(val)}'"
            elif isinstance(val, (dict, list)):
                escaped = json.dumps(val).replace("'", "''")
                return f"'{escaped}'"
            else:
                escaped = str(val).replace("'", "''")
                return f"'{escaped}'"

        return ", ".join(format_value(v) for v in row)

    @staticmethod
    def convert_mysql_file_to_statments(file_path: str) -> Iterator[str]:
        """
        Convert a MySQL SQL file content into a iterator of valid MySQL statements.
        that can be executed one by one.
        Args:
            file_path (str): The path to the MySQL SQL file.
        Returns:
            Iterator[str]: An iterator over valid MySQL statements.
        """
        current = []
        delimiter = ";"

        # Read the SQL file content
        with open(file_path, "r") as file:
            sql_script = file.read()
        # Split the script into lines and process each line
        try:
            for line in sql_script.splitlines():
                stripped = line.strip()

                if not stripped or stripped.startswith("--"):
                    continue

                if stripped.upper().startswith("DELIMITER"):
                    delimiter = stripped.split()[1]
                    continue

                current.append(line)

                if stripped.endswith(delimiter):
                    statement = "\n".join(current).rstrip(delimiter).strip()
                    if statement:
                        yield statement
                    current = []

            if current:
                yield "\n".join(current).strip()

        except Exception as e:
            raise ValueError(f"Error processing SQL file: {e}") from e

    def clean_single_sql_statement(self, sql: str) -> str:
        """
        Clean a single SQL statement string:
            - Removes single-line comments (-- ...)
            - Removes multi-line comments (/* ... */)
            - Removes DELIMITER lines
            - Strips trailing delimiter (; or custom)
        """
        delimiter = ";"
        inside_block_comment = False
        current = []

        for raw_line in sql.splitlines():
            line = raw_line.strip()

            if inside_block_comment:
                if "*/" in line:
                    inside_block_comment = False
                continue
            if line.startswith("/*"):
                if "*/" not in line:
                    inside_block_comment = True
                continue

            if not line or line.startswith("--"):
                continue

            if line.upper().startswith("DELIMITER"):
                parts = line.split()
                if len(parts) > 1:
                    delimiter = parts[1]
                continue

            if line == delimiter:
                continue

            current.append(raw_line.rstrip("\n"))

        statement = "\n".join(current).strip()

        # Strip trailing delimiter only if it matches the current one
        if statement.endswith(delimiter):
            statement = statement[: -len(delimiter)].strip()

        return statement
