# tests/databases/mysql/test_mysql_sorting.py
import pytest
from databases.mysql.mysql_sorting import MySQLSorting


@pytest.mark.usefixtures("require_mysql")
class TestMySQLSorting:
    """
    Test class for MySQLSorting to ensure tables are sorted correctly based on dependencies.
    """

    @pytest.fixture
    def setup_method(self, mysql_port):
        """
        Setup method to create an instance of MySQLSorting.
        """
        return MySQLSorting()

    def test_get_tables_sorted_sucessfully(self, setup_method, seed_database):
        """
        Test to ensure that the MySQL database returns sorted table names.
        """
        db = setup_method
        cursor = seed_database
        tables = db.get_tables_sorted(cursor)
        excpected_tables = ["departments", "employees", "projects"]
        assert isinstance(tables, list)
        assert len(tables) == len(excpected_tables)
        assert tables == excpected_tables

    def test_get_tables_sorted_empty_database(self, setup_method, empty_database):
        """
        Test to ensure that the MySQL database returns an empty list when no tables exist.
        """
        db = setup_method
        cursor = empty_database
        tables = db.get_tables_sorted(cursor)
        assert isinstance(tables, list)
        assert len(tables) == 0

    def test_get_tables_sorted_failure(
        self, setup_method, mocker, empty_database, caplog
    ):
        """
        Ensure that an error is raised when the database has no tables.
        """
        db = setup_method
        cursor = empty_database
        mocker.patch.object(cursor, "execute", side_effect=Exception("No tables found"))

        with pytest.raises(RuntimeError) as exc_info:
            db.get_tables_sorted(cursor)
        assert "Error in get and sort tables by dependencies: No tables found" in str(
            exc_info.value
        )
        assert (
            "Error in get and sort tables by dependencies: No tables found"
            in caplog.text
        )

    def test_get_views_sorted_successfully(self, setup_method, seed_database):
        """
        Test to ensure that the MySQL database returns sorted view names.
        """
        db = setup_method
        cursor = seed_database
        views = db.get_views_sorted(cursor)
        expected_views = [
            "view_employee_departments",
            "view_project_employees",
            "view_department_project_counts",
        ]
        assert isinstance(views, list)
        assert len(views) == len(expected_views)
        assert views == expected_views

    def test_get_views_sorted_empty_database(self, setup_method, empty_database):
        """
        Test to ensure that the MySQL database returns an empty list when no views exist.
        """
        db = setup_method
        cursor = empty_database
        views = db.get_views_sorted(cursor)
        assert isinstance(views, list)
        assert len(views) == 0

    def test_get_views_sorted_failure(
        self, setup_method, mocker, empty_database, caplog
    ):
        """
        Ensure that an error is raised when the database has no views.
        """
        db = setup_method
        cursor = empty_database
        mocker.patch.object(cursor, "execute", side_effect=Exception("error views"))

        with pytest.raises(RuntimeError) as exc_info:
            db.get_views_sorted(cursor)
        assert "Error in get and sort views by dependencies: error views" in str(
            exc_info.value
        )
        assert "Error in get and sort views by dependencies: error views" in caplog.text

    def test_get_functions_sorted_successfully(self, setup_method, seed_database):
        """
        Test to ensure that the MySQL database returns sorted function names.
        """
        db = setup_method
        cursor = seed_database
        functions = db.get_functions_sorted(cursor)
        expected_functions = [
            "dummy_get_department_name",
            "dummy_get_project_info",
            "dummy_department_project_summary",
        ]
        assert isinstance(functions, list)
        assert len(functions) == len(expected_functions)
        assert functions == expected_functions

    def test_get_functions_sorted_empty_database(self, setup_method, empty_database):
        """
        Test to ensure that the MySQL database returns an empty list when no functions exist.
        """
        db = setup_method
        cursor = empty_database
        functions = db.get_functions_sorted(cursor)
        assert isinstance(functions, list)
        assert len(functions) == 0

    def test_get_functions_sorted_failure(
        self, setup_method, mocker, empty_database, caplog
    ):
        """
        Ensure that an error is raised when the database has no functions.
        """
        db = setup_method
        cursor = empty_database
        mocker.patch.object(cursor, "execute", side_effect=Exception("error functions"))

        with pytest.raises(RuntimeError) as exc_info:
            db.get_functions_sorted(cursor)
        assert (
            "Error in get and sort functions by dependencies: error functions"
            in str(exc_info.value)
        )
        assert (
            "Error in get and sort functions by dependencies: error functions"
            in caplog.text
        )
