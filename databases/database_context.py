# databases/database_context.py
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv
import os
from collections import defaultdict, deque
from logger.logger_manager import LoggerManager

load_dotenv()


class DatabaseContext:
    """
    context class for all database shared logic and states
    and also use across the metadata files
    """

    def __init__(self, config: Dict):
        """
        Initialize the database with the given configuration
        and set the default processing path.
        Args:
            config: Configuration dictionary for the database.
        """
        self.logger = LoggerManager.setup_logger("database")
        for key, value in config.items():
            setattr(self, key, value)
        self.backup_folder_path: Path = Path(os.getenv("MAIN_BACKUP_PATH"))
        self.version: str = "Unknown"
        self.connection = None

    def topological_sort(self, deps: Dict[str, list[str]]) -> list[str]:
        """
        Perform a topological sort on the dependency graph to return sorted list
        from the least dependent to the most dependent.
        This is useful for ensuring that statements are backed up in the correct order.
        Args:
            deps (Dict[str, list[str]]): Dependency graph where keys are table names
        Returns:
            list[str]: Sorted list of table names.
        """
        graph = defaultdict(list)
        in_degree = defaultdict(int)

        # Build the graph and in-degree count
        for child, parents in deps.items():
            for parent in parents:
                graph[parent].append(child)
                in_degree[child] += 1
            in_degree.setdefault(child, 0)

        # Use the nodes with no incoming edges as the starting point
        queue = deque([node for node in in_degree if in_degree[node] == 0])
        sorted_nodes = []

        # Perform the topological sort
        while queue:
            node = queue.popleft()
            sorted_nodes.append(node)

            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check if we have a valid topological sort or if there is a cycle
        if len(sorted_nodes) != len(in_degree):
            self.logger.error(
                "Cycle detected in dependency graph, cannot perform topological sort."
            )
            raise RuntimeError(
                "Cycle detected in dependency graph, cannot perform topological sort."
            )

        self.logger.info(f"Topological sort completed successfully: {sorted_nodes}")
        return sorted_nodes

    def create_sql_backup_file(self, backup_file: Path, content: str) -> Path:
        """
        Create file and write all statements to it
        Args:
            backup_file (Path): path of the file will be created
            content (str): the string contents of statements
        Return:
            Path of the file after write contents to it
        """
        try:
            with open(backup_file, "w", encoding="utf-8") as f:
                f.write(f"-- Backup for {backup_file.name}\n")
                f.write(f"CREATE DATABASE IF NOT EXISTS `{self.db_name}`;\n")
                f.write(f"USE `{self.db_name}`;\n\n")
                f.write(content)
            self.logger.info(f"{backup_file.name} created successfully with content.")
            return backup_file
        except Exception as e:
            self.logger.error(f"Error creating backup file {backup_file.name}: {e}")
            raise RuntimeError("Failed to create backup file") from e
