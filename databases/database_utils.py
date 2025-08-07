# database/database_utils.py
from collections import defaultdict, deque
from typing import Dict
from logger.logger_manager import LoggerManager


class DatabaseUtils:
    """
    Utility class for common database operations.
    """

    def __init__(self):
        """
        Initialize the DatabaseUtils with a logger.
        """
        self.logger = LoggerManager.setup_logger("database")

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
