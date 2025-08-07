# tests/databases/test_database_utils.py
from databases.database_utils import DatabaseUtils
import pytest


class TestDatabaseUtils:
    """
    This class tests the utility functions for database operations.
    """

    @pytest.fixture
    def setup(self):
        """
        Fixture to initialize the DatabaseUtils class.
        """
        return DatabaseUtils()

    def test_topological_sort_success(self, setup):
        """
        Test the topological sort method with a valid dependency graph.
        """
        database_utils = setup
        deps = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        sorted_list = database_utils.topological_sort(deps)
        assert sorted_list == ["D", "B", "C", "A"]

    def test_topological_sort_cycle(self, setup, caplog):
        """
        Test the topological sort method with a cyclic dependency graph.
        """
        database_utils = setup
        deps = {"A": ["B"], "B": ["C"], "C": ["A"]}
        with pytest.raises(RuntimeError) as exc_info:
            database_utils.topological_sort(deps)
        assert (
            str(exc_info.value)
            == "Cycle detected in dependency graph, cannot perform topological sort."
        )
        assert (
            "Cycle detected in dependency graph, cannot perform topological sort."
            in caplog.text
        )

    def test_topological_sort_empty(self, setup):
        """
        Test the topological sort method with an empty dependency graph.
        """
        database_utils = setup
        deps = {}
        sorted_list = database_utils.topological_sort(deps)
        assert sorted_list == []

    def test_topological_sort_single_node(self, setup):
        """
        Test the topological sort method with a single node dependency graph.
        """
        database_utils = setup
        deps = {"A": []}
        sorted_list = database_utils.topological_sort(deps)
        assert sorted_list == ["A"]
