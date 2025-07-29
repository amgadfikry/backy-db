# databases/mysql.py
import mysql.connector
from pathlib import Path
from typing import List
from collections import defaultdict
import re
from databases.database_base import DatabaseBase
from utils.to_sql_values import to_sql_values


class MySQLDatabase(DatabaseBase):
    """
    MySQL database implementation for the Backy project.
    This class provides methods to connect, backup, restore, and close the MySQL database.
    """
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
                database=self.db_name
            )

            # Set the version of mysql
            self.version = self.connection.get_server_info()
    
            self.logger.info(f"Connected to MySQL database successfully {self.db_name} version {self.version}")
        except Exception as e:
            self.logger.error(f"Failed to connect to MySQL database: {e}")
            raise ConnectionError(f"Failed to connect to MySQL database: {e}")
        
    def get_tables_sorted(self, cursor: mysql.connector.cursor) -> List[str]:
        """
        Sort tables by their dependencies to ensure correct order for backup.
        This method retrieves the foreign key relationships and sorts the tables accordingly.
        Args:
            cursor: MySQL cursor object to execute SQL commands.
        Raises:
            RuntimeError: If the retrieval of foreign key relationships fails.
        Returns:
            list: Sorted list of table names based on dependencies.
        """
        try:
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]

            if not tables:
                self.logger.error("No tables found in the database.")
                raise RuntimeError("No tables found in the database.")

            cursor.execute("""
                SELECT TABLE_NAME, REFERENCED_TABLE_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL
            """, (self.db_name,))

            deps = defaultdict(list)
            for child, parent in cursor.fetchall():
                deps[child].append(parent)

            for table in tables:
                deps.setdefault(table, [])
        except Exception as e:
            self.logger.error(f"Error in get and sort tables by dependencies: {e}")
            raise RuntimeError(f"Failed to retrieve and sort tables by dependencies: {e}")

        sorted_tables = self.topological_sort(deps)

        self.logger.info(f"Tables sorted by dependencies successfully: {sorted_tables}")
        return sorted_tables

    def get_views_sorted(self, cursor: mysql.connector.cursor) -> list[str]:
        """
        Sort views by their dependencies to ensure correct order for backup.
        This method retrieves the view definitions and sorts them based on their dependencies.
        Args:
            cursor: MySQL cursor object to execute SQL commands.
        Raises:
            RuntimeError: If the retrieval of view definitions fails.
        Returns:
            list: Sorted list of view names based on dependencies.
        """
        try:
            cursor.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW'")
            all_views = [row[0] for row in cursor.fetchall()]

            if not all_views:
                self.logger.error("No views found in the database.")
                raise RuntimeError("No views found in the database.")
            
            deps = defaultdict(list)
            view_definitions = {}

            for view in all_views:
                cursor.execute(f"SHOW CREATE VIEW `{view}`")
                view_definitions[view] = cursor.fetchone()[1].lower()

            for view, create_stmt in view_definitions.items():
                for other_view in all_views:
                    if other_view == view:
                        continue
                    if f"`{other_view.lower()}`" in create_stmt or f"{other_view.lower()}" in create_stmt:
                        deps[view].append(other_view)

            for view in all_views:
                deps.setdefault(view, [])
        except Exception as e:
            self.logger.error(f"Error in get and sort views by dependencies: {e}")
            raise RuntimeError(f"Failed to retrieve and sort views by dependencies: {e}")

        sorted_views = self.topological_sort(deps)
        self.logger.info(f"Views sorted by dependencies successfully: {sorted_views}")
        return sorted_views

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
            cursor.execute("SHOW FUNCTION STATUS WHERE Db = %s", (self.db_name,))
            all_functions = [row[1] for row in cursor.fetchall()]

            if not all_functions:
                self.logger.error("No functions found in the database.")
                raise RuntimeError("No functions found in the database.")

            deps = defaultdict(list)
            function_definitions = {}

            for function in all_functions:
                cursor.execute(f"SHOW CREATE FUNCTION `{function}`")
                function_definitions[function] = cursor.fetchone()[2].lower()

            for function, create_stmt in function_definitions.items():
                for other_function in all_functions:
                    if other_function == function:
                        continue
                    if f"`{other_function.lower()}`" in create_stmt or f"{other_function.lower()}" in create_stmt:
                        deps[function].append(other_function)

            for function in all_functions:
                deps.setdefault(function, [])
        except Exception as e:
            self.logger.error(f"Error in get and sort functions by dependencies: {e}")
            raise RuntimeError(f"Failed to retrieve and sort functions by dependencies: {e}")

        sorted_functions = self.topological_sort(deps)
        self.logger.info(f"Functions sorted by dependencies successfully: {sorted_functions}")
        return sorted_functions

    def create_tables_statements(self, cursor: mysql.connector.cursor) -> str:
        """
        Get the SQL statements to create tables in the MySQL database.
        Args:
            cursor: MySQL cursor object to execute SQL commands.
        Raises:
            RuntimeError: If the retrieval of table creation statements fails.
        Returns:
            str: SQL statements to create tables.
        """
        table_statements = []
        try:
            # Get tables sorted by dependencies
            tables = self.get_tables_sorted(cursor)

            # Retrieve table creation statements
            for table_name in tables:
                cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
                create_statement = cursor.fetchone()[1]
                table_statements.append(f"-- Create {table_name.capitalize()} Table\n{create_statement}")
    
        except Exception as e:
            self.logger.error(f"Error retrieving table creation statements: {e}")
            raise RuntimeError(f"Failed to retrieve table creation statements: {e}")

        self.logger.info(f"Table creation statements retrieved successfully for {len(table_statements)} tables.")
        return ";\n\n".join(table_statements) + ";\n\n" if table_statements else ""

    def create_data_statements(self, cursor: mysql.connector.cursor) -> str:
        """
        Get the SQL statements to insert data into tables in the MySQL database.
        Args:
            cursor: MySQL cursor object to execute SQL commands.
        Raises:
            RuntimeError: If the retrieval of data insertion statements fails.
        Returns:
            str: SQL statements to insert data into tables.
        """
        data_statements = []
        try:
            # Get tables sorted by dependencies
            tables = self.get_tables_sorted(cursor)

            # Retrieve data insertion statements
            for table_name in tables:
                cursor.execute(f"SELECT * FROM `{table_name}`")
                rows = cursor.fetchall()
                if not rows:
                    self.logger.warning(f"No data found in table `{table_name}`. Skipping data insertion statements.")
                    continue
                values_list = [f"({to_sql_values(row)})" for row in rows]
                data_statements.append(f"-- Insert Into {table_name.capitalize()} Table\nINSERT INTO `{table_name}` VALUES")
                data_statements.append("\t" + ",\n\t".join(values_list) + ";")

        except Exception as e:
            self.logger.error(f"Error retrieving data insertion statements: {e}")
            raise RuntimeError(f"Failed to retrieve data insertion statements: {e}")

        self.logger.info("Data insertion statements retrieved successfully for all tables.")
        return "\n".join(data_statements) + "\n" if data_statements else ""

    def create_views_statements(self, cursor: mysql.connector.cursor) -> str:
        """
        Get the SQL statements to create views in the MySQL database.
        Args:
            cursor: MySQL cursor object to execute SQL commands.
        Raises:
            RuntimeError: If the retrieval of view creation statements fails.
        Returns:
            str: SQL statements to create views.
        """
        view_statements = []
        try:
            # Get views sorted by dependencies
            views = self.get_views_sorted(cursor)

            # Retrieve view creation statements
            for view_name in views:
                cursor.execute(f"SHOW CREATE VIEW `{view_name}`")
                create_statement = cursor.fetchone()[1]
                view_statements.append(f"-- Create {view_name.capitalize()} view\n{create_statement}")

        except Exception as e:
            self.logger.error(f"Error retrieving view creation statements: {e}")
            raise RuntimeError(f"Failed to retrieve view creation statements: {e}")

        self.logger.info(f"View creation statements retrieved successfully for {len(view_statements)} views.")
        return ";\n\n".join(view_statements) + ";\n\n" if view_statements else ""

    def create_functions_statements(self, cursor: mysql.connector.cursor) -> str:
        """
        Get the SQL statements to create functions in the MySQL database.
        Args:
            cursor: MySQL cursor object to execute SQL commands.
        Raises:
            RuntimeError: If the retrieval of function creation statements fails.
        Returns:
            str: SQL statements to create functions.
        """
        function_statements = []
        try:
            # Get functions sorted by dependencies
            functions = self.get_functions_sorted(cursor)

            # Retrieve function creation statements
            for function_name in functions:
                cursor.execute(f"SHOW CREATE FUNCTION `{function_name}`")
                create_statement = cursor.fetchone()[2]
                function_statements.append(f"-- Create {function_name.capitalize()} Function\nDELIMITER ;;\n{create_statement};;\nDELIMITER ;")

        except Exception as e:
            self.logger.error(f"Error retrieving function creation statements: {e}")
            raise RuntimeError(f"Failed to retrieve function creation statements: {e}")

        self.logger.info(f"Function creation statements retrieved successfully for {len(function_statements)} functions.")
        return "\n\n".join(function_statements) + "\n\n" if function_statements else ""

    def create_procedures_statements(self, cursor: mysql.connector.cursor) -> str:
        """
        Get the SQL statements to create procedures in the MySQL database.
        Args:
            cursor: MySQL cursor object to execute SQL commands.
        Raises:
            RuntimeError: If the retrieval of procedure creation statements fails.
        Returns:
            str: SQL statements to create procedures.
        """
        procedure_statements = []
        try:
            # Get all procedures in the database
            cursor.execute("SHOW PROCEDURE STATUS WHERE Db = %s", (self.db_name,))
            all_procedures = [row[1] for row in cursor.fetchall()]

            if not all_procedures:
                self.logger.error("No procedures found in the database.")
                raise RuntimeError("No procedures found in the database.")

            # Retrieve procedure creation statements
            for procedure in all_procedures:
                cursor.execute(f"SHOW CREATE PROCEDURE `{procedure}`")
                create_statement = cursor.fetchone()[2]
                procedure_statements.append(f"-- Create {procedure.capitalize()} Procedure\nDELIMITER ;;\n{create_statement};;\nDELIMITER ;")

        except Exception as e:
            self.logger.error(f"Error retrieving procedure creation statements: {e}")
            raise RuntimeError(f"Failed to retrieve procedure creation statements: {e}")

        self.logger.info(f"Procedure creation statements retrieved successfully for {len(procedure_statements)} procedures.")
        return "\n\n".join(procedure_statements) + "\n\n" if procedure_statements else ""

    def create_triggers_statements(self, cursor: mysql.connector.cursor) -> str:
        """
        Get the SQL statements to create triggers in the MySQL database.
        Args:
            cursor: MySQL cursor object to execute SQL commands.
        Raises:
            RuntimeError: If the retrieval of trigger creation statements fails.
        Returns:
            str: SQL statements to create triggers.
        """
        statements = []
        try:
            # Get all triggers in the database
            cursor.execute("SHOW TRIGGERS")
            triggers = [row[0] for row in cursor.fetchall()]

            if not triggers:
                self.logger.error("No triggers found in the database.")
                raise RuntimeError("No triggers found in the database.")

            # Retrieve trigger creation statements
            for trigger_name in triggers:
                cursor.execute(f"SHOW CREATE TRIGGER `{trigger_name}`")
                _, create_stmt = cursor.fetchone()
                statements.append(f"-- Create {trigger_name.capitalize()} Trigger\nDELIMITER ;;\n{create_stmt};;\nDELIMITER ;")

        except Exception as e:
            self.logger.error(f"Error retrieving trigger creation statements: {e}")
            raise RuntimeError(f"Failed to retrieve trigger creation statements: {e}")

        self.logger.info(f"Trigger creation statements retrieved successfully for {len(statements)} triggers.")
        return "\n\n".join(statements) + "\n\n" if statements else ""

    def create_events_statements(self, cursor: mysql.connector.cursor) -> str:
        """
        Get the SQL statements to create events in the MySQL database.
        Args:
            cursor: MySQL cursor object to execute SQL commands.
        Raises:
            RuntimeError: If the retrieval of event creation statements fails.
        Returns:
            str: SQL statements to create events.
        """
        event_statements = []
        originally_enabled_events = []
        try:
            # Get all events in the database
            cursor.execute("SHOW EVENTS WHERE Db = %s", (self.db_name,))
            events = cursor.fetchall()

            if not events:
                self.logger.error("No events found in the database.")
                raise RuntimeError("No events found in the database.")

            # Retrieve event creation statements
            for row in events:
                event_name = row[1]
                status = row[6]

                # Get the CREATE EVENT statement
                cursor.execute(f"SHOW CREATE EVENT `{event_name}`")
                create_statement = cursor.fetchone()[3]

                # Check if the events were originally enabled and modify them to be disabled
                if status == 'ENABLED':
                    originally_enabled_events.append(event_name)
                create_statement = re.sub(r'\bENABLE\b', 'DISABLE', create_statement, count=1)

                # Append the modified create statement to the event statements
                event_statements.append(f"-- Create {event_name.capitalize()} Event\nDELIMITER ;;\n{create_statement};;\nDELIMITER ;")

            # If there were originally enabled events, add statements to re-enable them at the end
            if originally_enabled_events:
                event_statements.append("-- Re-enable originally enabled events")
                for event_name in originally_enabled_events:
                    event_statements.append(f"ALTER EVENT `{event_name}` ENABLE;")

        except Exception as e:
            self.logger.error(f"Error retrieving event creation statements: {e}")
            raise RuntimeError(f"Failed to retrieve event creation statements: {e}")

        self.logger.info(f"Event creation statements retrieved successfully for {len(event_statements)} events.")
        return "\n\n".join(event_statements) + "\n\n" if event_statements else ""

    def backup(self, timestamp: str) -> List[Path]:
        """
        Perform a backup of the MySQL database.
        This method should implement the logic to create a backup file either
        as a single file or multiple files based on the features selected.
        Args:
            timestamp (str): Timestamp to append to the backup file name.
        Raises:
            RuntimeError: If the backup process fails.
        Returns:
            List[Path]: List of backup file paths created during the backup process.
        """
        backup_files: List[Path] = []
    
        ordered_features: List[tuple[str, callable]] = [
            ("tables", self.create_tables_statements),
            ("data", self.create_data_statements),
            ("views", self.create_views_statements),
            ("functions", self.create_functions_statements),
            ("procedures", self.create_procedures_statements),
            ("triggers", self.create_triggers_statements),
            ("events", self.create_events_statements),
        ]

        try:
            with self.connection.cursor() as cursor:
                content_dict = {}

                for feature, method in ordered_features:
                    if getattr(self, feature):
                        content = method(cursor)
                        if content:
                            content_dict[feature] = content

                if not content_dict:
                    self.logger.error("No content to write to backup files.")
                    raise RuntimeError("No content to write to backup files.")

                if self.one_file:
                    full_content = "\n\n".join(content_dict.values())
                    backup_file = self.processing_path / f"{self.db_name}_{timestamp}_backup.sql"
                    self.create_backup_file(backup_file, full_content)
                    backup_files.append(backup_file)
                else:
                    for feature, content in content_dict.items():
                        backup_file = self.processing_path / f"{self.db_name}_{feature}_{timestamp}_backup.sql"
                        self.create_sql_backup_file(backup_file, content)
                        backup_files.append(backup_file)

        except Exception as e:
            self.logger.error(f"Error during backup process: {e}")
            raise RuntimeError(f"Failed to perform backup: {e}")

        self.logger.info(f"Backup completed successfully. Created {len(backup_files)} backup files.")
        return backup_files

    def restore(self, backup_file: Path):
        self.logger.error("Restore method is not implemented for MySQLDatabase yet.")
        raise NotImplementedError("Restore method is not implemented for MySQLDatabase yet.")
    
    def close(self):
        """
        Close the MySQL database connection.
        """
        if self.connection.is_connected():
            self.connection.close()
            self.logger.info("MySQL database connection closed.")
        else:
            self.logger.warning("No active MySQL database connection to close.")
