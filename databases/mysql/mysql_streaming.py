# databases/mysql/mysql_streaming.py
from typing import Iterator
import mysql.connector
from databases.mysql.mysql_sorting import MySQLSorting
from databases.mysql.mysql_utils import MySQLUtils
import sqlparse
import re
from logger.logger_manager import LoggerManager


class MySQLStreaming:
    """
    Class for streaming MySQL statements for MySQL database objects like tables, data, views,
    functions, procedures, triggers, and events.
    It uses MySQLSorting to ensure the correct order based on dependencies.
    """

    def __init__(self):
        """
        Initialize MySQLStreaming with the logger and MySQL utilities.
        """
        self.logger = LoggerManager.setup_logger("database")
        self.sorting = MySQLSorting()

    def stream_tables_statements(self, cursor: mysql.connector.cursor) -> Iterator[str]:
        """
        Stream the SQL statements to create tables in the MySQL database.
        It gets the sorted list of tables based on their dependencies.
        It retrieves the table creation statements and yields them one by one.
        Args:
            cursor: MySQL cursor object to execute SQL commands.
        Raises:
            RuntimeError: If the retrieval of table creation statements fails.
        Returns:
            Iterator[str]: An iterator that yields SQL statements to create tables.
        """
        try:
            # Get tables sorted by dependencies
            tables = self.sorting.get_tables_sorted(cursor)

            # Retrieve table creation statements
            for table_name in tables:
                cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
                create_statement = cursor.fetchone()[1]
                statement = f"-- Create {table_name.capitalize()} Table\n{create_statement};\n\n"
                yield statement

        except Exception as e:
            self.logger.error(f"Error retrieving table creation statements: {e}")
            raise RuntimeError(f"Error retrieving table creation statements: {e}")

    def stream_data_statements(self, cursor: mysql.connector.cursor) -> Iterator[str]:
        """
        Stream the SQL statements to insert data into tables in the MySQL database.
        It retrieves the sorted list of tables based on their dependencies
        and generates SQL statements to insert data into each table.
        It uses a batch size of 1000 rows to fetch data for each table.
        Args:
            cursor: MySQL cursor object to execute SQL commands.
        Raises:
            RuntimeError: If the retrieval of data insertion statements fails.
        Returns:
            Iterator[str]: An iterator that yields SQL statements to insert data into tables.
        """
        try:
            # Get tables sorted by dependencies
            tables = self.sorting.get_tables_sorted(cursor)

            # Retrieve data insertion statements
            for table_name in tables:
                cursor.execute(f"SELECT * FROM `{table_name}`")

                while True:
                    rows = cursor.fetchmany(1000)
                    if not rows:
                        break
                    values_list = [
                        f"({MySQLUtils.raw_to_mysql_values(row)})" for row in rows
                    ]
                    statement = f"-- Insert Into {table_name.capitalize()} Table\nINSERT INTO `{table_name}` VALUES\n"
                    statement += "\t" + ",\n\t".join(values_list) + ";\n\n"
                    yield statement

        except Exception as e:
            self.logger.error(f"Error retrieving data insertion statements: {e}")
            raise RuntimeError(f"Error retrieving data insertion statements: {e}")

    def stream_views_statements(self, cursor: mysql.connector.cursor) -> Iterator[str]:
        """
        Stream the SQL statements to create views in the MySQL database.
        It gets the sorted list of views based on their dependencies.
        It retrieves the view creation statements and yields them one by one.
        Args:
            cursor: MySQL cursor object to execute SQL commands.
        Raises:
            RuntimeError: If the retrieval of view creation statements fails.
        Returns:
            Iterator[str]: An iterator that yields SQL statements to create views.
        """
        try:
            # Get views sorted by dependencies
            views = self.sorting.get_views_sorted(cursor)

            # Retrieve view creation statements
            for view_name in views:
                cursor.execute(f"SHOW CREATE VIEW `{view_name}`")
                create_statement = cursor.fetchone()[1]
                statement = (
                    f"-- Create {view_name.capitalize()} view\n{create_statement};\n\n"
                )
                yield sqlparse.format(statement, reindent=True, keyword_case="upper")

        except Exception as e:
            self.logger.error(f"Error retrieving view creation statements: {e}")
            raise RuntimeError(f"Error retrieving view creation statements: {e}")

    def stream_functions_statements(
        self, cursor: mysql.connector.cursor
    ) -> Iterator[str]:
        """
        Stream the SQL statements to create functions in the MySQL database.
        It retrieves the sorted list of functions based on their dependencies
        and generates SQL statements to create each function.
        It retrieves the function creation statements and yields them one by one.
        Args:
            cursor: MySQL cursor object to execute SQL commands.
        Raises:
            RuntimeError: If the retrieval of function creation statements fails.
        Returns:
            Iterator[str]: An iterator that yields SQL statements to create functions.
        """
        try:
            # Get functions sorted by dependencies
            functions = self.sorting.get_functions_sorted(cursor)

            # Retrieve function creation statements
            for function_name in functions:
                cursor.execute(f"SHOW CREATE FUNCTION `{function_name}`")
                create_statement = cursor.fetchone()[2]
                statement = (
                    f"\n\n-- Create {function_name.capitalize()} Function\n"
                    "DELIMITER $$\n"
                    f"{create_statement}\n"
                    "$$\n"
                    "DELIMITER ;\n\n"
                )
                yield statement

        except Exception as e:
            self.logger.error(f"Error retrieving function creation statements: {e}")
            raise RuntimeError(f"Error retrieving function creation statements: {e}")

    def stream_procedures_statements(
        self, cursor: mysql.connector.cursor
    ) -> Iterator[str]:
        """
        Stream the SQL statements to create procedures in the MySQL database.
        It retrieves the procedure creation statements and yields them one by one.
        Args:
            cursor: MySQL cursor object to execute SQL commands.
        Raises:
            RuntimeError: If the retrieval of procedure creation statements fails.
        Returns:
            Iterator[str]: An iterator that yields SQL statements to create procedures.
        """
        try:
            # Get all procedures in the database
            cursor.execute("SHOW PROCEDURE STATUS WHERE Db = DATABASE()")
            all_procedures = [row[1] for row in cursor.fetchall()]

            # Retrieve procedure creation statements
            for procedure in all_procedures:
                cursor.execute(f"SHOW CREATE PROCEDURE `{procedure}`")
                create_statement = cursor.fetchone()[2]
                statement = (
                    f"-- Create {procedure.capitalize()} Procedure\n"
                    "DELIMITER $$\n"
                    f"{create_statement}\n"
                    "$$\n"
                    "DELIMITER ;\n\n"
                )
                yield statement

        except Exception as e:
            self.logger.error(f"Error retrieving procedure creation statements: {e}")
            raise RuntimeError(f"Error retrieving procedure creation statements: {e}")

    def stream_triggers_statements(
        self, cursor: mysql.connector.cursor
    ) -> Iterator[str]:
        """
        Stream the SQL statements to create triggers in the MySQL database.
        It retrieves the trigger creation statements and yields them one by one.
        Args:
            cursor: MySQL cursor object to execute SQL commands.
        Raises:
            RuntimeError: If the retrieval of trigger creation statements fails.
        Returns:
            Iterator[str]: An iterator that yields SQL statements to create triggers.
        """
        try:
            # Get all triggers in the database
            cursor.execute("SHOW TRIGGERS")
            triggers = [row[0] for row in cursor.fetchall()]

            # Retrieve trigger creation statements
            for trigger_name in triggers:
                cursor.execute(f"SHOW CREATE TRIGGER `{trigger_name}`")
                create_stmt = cursor.fetchone()[2]
                statement = (
                    f"-- Create {trigger_name.capitalize()} Trigger\n"
                    "DELIMITER $$\n"
                    f"{create_stmt}\n"
                    "$$\n"
                    "DELIMITER ;\n\n"
                )
                yield statement

        except Exception as e:
            self.logger.error(f"Error retrieving trigger creation statements: {e}")
            raise RuntimeError(f"Error retrieving trigger creation statements: {e}")

    def stream_events_statements(self, cursor: mysql.connector.cursor) -> Iterator[str]:
        """
        Stream the SQL statements to create events in the MySQL database.
        It retrieves the event creation statements and yields them one by one.
        It also handles the enabling/disabling of events based on their original state.
        Args:
            cursor: MySQL cursor object to execute SQL commands.
        Raises:
            RuntimeError: If the retrieval of event creation statements fails.
        Returns:
            Iterator[str]: An iterator that yields SQL statements to create events.
        """
        try:
            originally_enabled_events = []
            # Get all events in the database
            cursor.execute("SHOW EVENTS WHERE Db = DATABASE()")
            events = cursor.fetchall()

            # Retrieve event creation statements
            for row in events:
                event_name = row[1]
                status = row[10]

                # Get the CREATE EVENT statement
                cursor.execute(f"SHOW CREATE EVENT `{event_name}`")
                create_statement = cursor.fetchone()[3]

                # Check if the events were originally enabled and modify them to be disabled
                if status == "ENABLED":
                    originally_enabled_events.append(event_name)
                create_statement = re.sub(
                    r"\bENABLE\b", "DISABLE", create_statement, count=1
                )

                # Append the modified create statement to the event statements
                statement = (
                    f"-- Create {event_name.capitalize()} Event\n"
                    "DELIMITER $$\n"
                    f"{create_statement};\n"
                    "$$\n"
                    "DELIMITER ;\n\n"
                )

                yield statement

            # If there were originally enabled events, add statements to re-enable them at the end
            if originally_enabled_events:
                for event_name in originally_enabled_events:
                    restore_event = (
                        f"-- Restore {event_name.capitalize()} Event that was originally enabled\n"
                        f"ALTER EVENT `{event_name}` ENABLE;\n\n"
                    )
                    yield restore_event

        except Exception as e:
            self.logger.error(f"Error retrieving event creation statements: {e}")
            raise RuntimeError(f"Error retrieving event creation statements: {e}")
