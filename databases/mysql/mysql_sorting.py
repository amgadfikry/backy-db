# databases/mysql/mysql_sorting.py
from collections import defaultdict
from typing import List
import mysql.connector
from databases.database_utils import DatabaseUtils
from logger.logger_manager import LoggerManager


class MySQLSorting:
    """
    Class for sorting MySQL database objects like tables, views, and functions
    based on their dependencies to ensure correct order for backup.
    """

    def __init__(self):
        """
        Initialize MySQLSorting with the logger and database utilities.
        """
        self.logger = LoggerManager.setup_logger("database")
        self.utils = DatabaseUtils()

    def get_tables_sorted(self, cursor: mysql.connector.cursor) -> List[str]:
        """
        Sort tables by their dependencies to ensure correct order for backup.
        It retrieves the foreign key relationships and sorts the tables accordingly.
        Args:
            cursor: MySQL cursor object to execute SQL commands.
        Raises:
            RuntimeError: If the retrieval of foreign key relationships fails.
        Returns:
            list: Sorted list of table names based on dependencies.
        """
        try:
            # Get all tables only not views from the database
            cursor.execute(
                """
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_TYPE = 'BASE TABLE'
            """
            )
            tables = [row[0] for row in cursor.fetchall()]

            # Get all references between tables according to foreign keys
            cursor.execute(
                """
                SELECT TABLE_NAME, REFERENCED_TABLE_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = DATABASE() AND REFERENCED_TABLE_NAME IS NOT NULL
            """
            )

            # Create a dictionary to hold dependencies
            deps = defaultdict(list)
            for child, parent in cursor.fetchall():
                deps[child].append(parent)

            # Ensure all tables are in the dependencies dictionary, even if they have no parents
            for table in tables:
                deps.setdefault(table, [])

            # Sort tables based on dependencies using topological sort
            sorted_tables = self.utils.topological_sort(deps)
            self.logger.info("Tables sorted by dependencies successfully")
            return sorted_tables

        except Exception as e:
            self.logger.error(f"Error in get and sort tables by dependencies: {e}")
            raise RuntimeError(f"Error in get and sort tables by dependencies: {e}")

    def get_views_sorted(self, cursor: mysql.connector.cursor) -> list[str]:
        """
        Sort views by their dependencies to ensure correct order for backup.
        It retrieves the view definitions and sorts them based on their dependencies.
        Args:
            cursor: MySQL cursor object to execute SQL commands.
        Raises:
            RuntimeError: If the retrieval of view definitions fails.
        Returns:
            list: Sorted list of view names based on dependencies.
        """
        try:
            # Get all views from the database
            cursor.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW'")
            all_views = [row[0] for row in cursor.fetchall()]

            # Create a dictionary to hold dependencies
            deps = defaultdict(list)
            view_definitions = {}

            # Retrieve view definitions
            for view in all_views:
                cursor.execute(f"SHOW CREATE VIEW `{view}`")
                view_definitions[view] = cursor.fetchone()[1].lower()

            # Analyze view definitions to find dependencies and skip self-references
            for view, create_stmt in view_definitions.items():
                for other_view in all_views:
                    if other_view == view:
                        continue
                    if (
                        f"`{other_view.lower()}`" in create_stmt
                        or f"{other_view.lower()}" in create_stmt
                    ):
                        deps[view].append(other_view)

            # Ensure all views are in the dependencies dictionary, even if they have no dependencies
            for view in all_views:
                deps.setdefault(view, [])

            # Sort views based on dependencies using topological sort
            sorted_views = self.utils.topological_sort(deps)
            self.logger.info("Views sorted by dependencies successfully")
            return sorted_views

        except Exception as e:
            self.logger.error(f"Error in get and sort views by dependencies: {e}")
            raise RuntimeError(f"Error in get and sort views by dependencies: {e}")

    def get_functions_sorted(self, cursor: mysql.connector.cursor) -> list[str]:
        """
        Sort functions by their dependencies to ensure correct order for backup.
        This method retrieves the function definitions and sorts them based on their dependencies.
        Args:
            cursor: MySQL cursor object to execute SQL commands.
        Raises:
            RuntimeError: If the retrieval of function definitions fails.
        Returns:
            list: Sorted list of function names based on dependencies.
        """
        try:
            # Get all functions in the database
            cursor.execute("SHOW FUNCTION STATUS WHERE Db = DATABASE()")
            all_functions = [row[1] for row in cursor.fetchall()]

            # Create a dictionary to hold dependencies
            deps = defaultdict(list)
            function_definitions = {}

            # Retrieve function definitions
            for function in all_functions:
                cursor.execute(f"SHOW CREATE FUNCTION `{function}`")
                function_definitions[function] = cursor.fetchone()[2].lower()

            # Analyze function definitions to find dependencies and skip self-references
            for function, create_stmt in function_definitions.items():
                for other_function in all_functions:
                    if other_function == function:
                        continue
                    if (
                        f"`{other_function.lower()}`" in create_stmt
                        or f"{other_function.lower()}" in create_stmt
                    ):
                        deps[function].append(other_function)

            # Ensure all functions are in the dependencies dictionary, even if they have no dependencies
            for function in all_functions:
                deps.setdefault(function, [])

            # Sort functions based on dependencies using topological sort
            sorted_functions = self.utils.topological_sort(deps)
            self.logger.info(
                f"Functions sorted by dependencies successfully: {sorted_functions}"
            )
            return sorted_functions

        except Exception as e:
            self.logger.error(f"Error in get and sort functions by dependencies: {e}")
            raise RuntimeError(f"Error in get and sort functions by dependencies: {e}")
