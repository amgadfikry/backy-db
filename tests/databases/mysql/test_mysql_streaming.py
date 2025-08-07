# tests/databases/mysql/test_mysql_streaming.py
import pytest
from databases.mysql.mysql_streaming import MySQLStreaming


@pytest.mark.usefixtures("require_mysql")
class TestMySQLStreaming:
    """
    Test class for MySQLStreaming to ensure streaming of SQL statements works correctly.
    """

    @pytest.fixture
    def setup_method(self, mysql_port, mocker):
        """
        Setup method to mock the MySQLSorting instance.
        and return an instance of MySQLStreaming.
        """
        mock_sorting = mocker.Mock()
        mocker.patch(
            "databases.mysql.mysql_sorting.MySQLSorting", return_value=mock_sorting
        )
        return MySQLStreaming()

    def test_stream_table_statements_successfully(
        self, setup_method, mocker, seed_database
    ):
        """
        Test to ensure that the MySQL database returns table creation statements.
        """
        db = setup_method
        cursor = seed_database
        mocker.patch.object(
            db.sorting,
            "get_tables_sorted",
            return_value=["departments", "employees", "projects"],
        )
        create_statements = list(db.stream_tables_statements(cursor))
        assert "CREATE TABLE `departments`" in create_statements[0]
        assert "CREATE TABLE `employees`" in create_statements[1]
        assert "CREATE TABLE `projects`" in create_statements[2]

    def test_stream_table_statements_empty_database(
        self, setup_method, mocker, empty_database
    ):
        """
        Test to ensure that the MySQL database returns an empty string when no tables exist.
        """
        db = setup_method
        cursor = empty_database
        mocker.patch.object(db.sorting, "get_tables_sorted", return_value=[])
        create_statements = list(db.stream_tables_statements(cursor))
        assert isinstance(create_statements, list)
        assert len(create_statements) == 0

    def test_stream_table_statements_failure(
        self, setup_method, mocker, empty_database, caplog
    ):
        """
        Ensure that an error is raised when the database has no tables.
        """
        db = setup_method
        cursor = empty_database
        mocker.patch.object(
            db.sorting, "get_tables_sorted", side_effect=Exception("No tables found")
        )
        with pytest.raises(RuntimeError) as exc_info:
            list(db.stream_tables_statements(cursor))
        assert "Error retrieving table creation statements: No tables found" in str(
            exc_info.value
        )
        assert (
            "Error retrieving table creation statements: No tables found" in caplog.text
        )

    def test_stream_data_statements_successfully(
        self, setup_method, mocker, seed_database
    ):
        """
        Test to ensure that the MySQL database returns data insertion statements.
        """
        db = setup_method
        cursor = seed_database
        mocker.patch.object(
            db.sorting,
            "get_tables_sorted",
            return_value=["departments", "employees", "projects"],
        )
        insert_statements = list(db.stream_data_statements(cursor))
        assert isinstance(insert_statements, list)
        assert "INSERT INTO `departments`" in insert_statements[0]
        assert "INSERT INTO `employees`" in insert_statements[1]
        assert "INSERT INTO `projects`" in insert_statements[2]

    def test_stream_data_statements_with_no_data_in_tables(
        self, setup_method, mocker, seed_database
    ):
        """
        Test to ensure that the MySQL database returns an empty string when no data exists in tables.
        """
        db = setup_method
        cursor = seed_database
        mocker.patch.object(
            db.sorting,
            "get_tables_sorted",
            return_value=["departments", "employees", "projects"],
        )
        # Clear data from tables
        cursor.execute("DELETE FROM projects")
        cursor.execute("DELETE FROM employees")
        cursor.execute("DELETE FROM departments")
        insert_statements = list(db.stream_data_statements(cursor))
        assert isinstance(insert_statements, list)
        assert len(insert_statements) == 0

    def test_stream_data_statements_empty_database(
        self, setup_method, mocker, empty_database
    ):
        """
        Test to ensure that the MySQL database returns an empty string when no data exists.
        """
        db = setup_method
        cursor = empty_database
        mocker.patch.object(db.sorting, "get_tables_sorted", return_value=[])
        insert_statements = list(db.stream_data_statements(cursor))
        assert isinstance(insert_statements, list)
        assert len(insert_statements) == 0

    def test_stream_data_statements_failure(
        self, setup_method, mocker, empty_database, caplog
    ):
        """
        Ensure that an error is raised when the database has no data.
        """
        db = setup_method
        cursor = empty_database
        mocker.patch.object(
            db.sorting, "get_tables_sorted", side_effect=Exception("No data found")
        )
        with pytest.raises(RuntimeError) as exc_info:
            list(db.stream_data_statements(cursor))
        assert "Error retrieving data insertion statements: No data found" in str(
            exc_info.value
        )
        assert (
            "Error retrieving data insertion statements: No data found" in caplog.text
        )

    def test_stream_views_statements_successfully(
        self, setup_method, mocker, seed_database
    ):
        """
        Test to ensure that the MySQL database returns view creation statements.
        """
        db = setup_method
        cursor = seed_database
        mocker.patch.object(
            db.sorting,
            "get_views_sorted",
            return_value=[
                "view_employee_departments",
                "view_project_employees",
                "view_department_project_counts",
            ],
        )
        view_statements = list(db.stream_views_statements(cursor))
        assert isinstance(view_statements, list)
        assert "`view_employee_departments` AS" in view_statements[0]
        assert "`view_project_employees` AS" in view_statements[1]
        assert "`view_department_project_counts` AS" in view_statements[2]

    def test_stream_views_statements_empty_database(
        self, setup_method, mocker, empty_database
    ):
        """
        Test to ensure that the MySQL database returns an empty string when no views exist.
        """
        db = setup_method
        cursor = empty_database
        mocker.patch.object(db.sorting, "get_views_sorted", return_value=[])
        view_statements = list(db.stream_views_statements(cursor))
        assert isinstance(view_statements, list)
        assert len(view_statements) == 0

    def test_stream_views_statements_failure(
        self, setup_method, mocker, empty_database, caplog
    ):
        """
        Ensure that an error is raised when the database has no views.
        """
        db = setup_method
        cursor = empty_database
        mocker.patch.object(
            db.sorting, "get_views_sorted", side_effect=Exception("No views found")
        )
        with pytest.raises(RuntimeError) as exc_info:
            list(db.stream_views_statements(cursor))
        assert "Error retrieving view creation statements: No views found" in str(
            exc_info.value
        )
        assert (
            "Error retrieving view creation statements: No views found" in caplog.text
        )

    def test_stream_functions_statements_successfully(
        self, setup_method, mocker, seed_database
    ):
        """
        Test to ensure that the MySQL database returns function creation statements.
        """
        db = setup_method
        cursor = seed_database
        mocker.patch.object(
            db.sorting,
            "get_functions_sorted",
            return_value=[
                "dummy_get_department_name",
                "dummy_get_project_info",
                "dummy_department_project_summary",
            ],
        )
        function_statements = list(db.stream_functions_statements(cursor))
        assert isinstance(function_statements, list)
        assert "FUNCTION `dummy_get_department_name`" in function_statements[0]
        assert "FUNCTION `dummy_get_project_info`" in function_statements[1]
        assert "FUNCTION `dummy_department_project_summary`" in function_statements[2]

    def test_stream_functions_statements_empty_database(
        self, setup_method, mocker, empty_database
    ):
        """
        Test to ensure that the MySQL database returns an empty string when no functions exist.
        """
        db = setup_method
        cursor = empty_database
        mocker.patch.object(db.sorting, "get_functions_sorted", return_value=[])
        function_statements = list(db.stream_functions_statements(cursor))
        assert isinstance(function_statements, list)
        assert len(function_statements) == 0

    def test_stream_functions_statements_failure(
        self, setup_method, mocker, empty_database, caplog
    ):
        """
        Ensure that an error is raised when the database has no functions.
        """
        db = setup_method
        cursor = empty_database
        mocker.patch.object(
            db.sorting,
            "get_functions_sorted",
            side_effect=Exception("No functions found"),
        )
        with pytest.raises(RuntimeError) as exc_info:
            list(db.stream_functions_statements(cursor))
        assert (
            "Error retrieving function creation statements: No functions found"
            in str(exc_info.value)
        )
        assert (
            "Error retrieving function creation statements: No functions found"
            in caplog.text
        )

    def test_stream_procedures_statements_successfully(
        self, setup_method, seed_database
    ):
        """
        Test to ensure that the MySQL database returns procedure creation statements.
        """
        db = setup_method
        cursor = seed_database
        procedure_statements = list(db.stream_procedures_statements(cursor))
        assert isinstance(procedure_statements, list)
        assert "PROCEDURE `department_summary`" in procedure_statements[0]
        assert "PROCEDURE `employee_project_info`" in procedure_statements[1]

    def test_stream_procedures_statements_empty_database(
        self, setup_method, mocker, empty_database
    ):
        """
        Test to ensure that the MySQL database returns an empty string when no procedures exist.
        """
        db = setup_method
        cursor = empty_database
        procedure_statements = list(db.stream_procedures_statements(cursor))
        assert isinstance(procedure_statements, list)
        assert len(procedure_statements) == 0

    def test_stream_procedures_statements_failure(
        self, setup_method, mocker, empty_database, caplog
    ):
        """
        Ensure that an error is raised when the database has no procedures.
        """
        db = setup_method
        cursor = empty_database
        mocker.patch.object(
            cursor, "execute", side_effect=Exception("No procedures found")
        )
        with pytest.raises(RuntimeError) as exc_info:
            list(db.stream_procedures_statements(cursor))
        assert (
            "Error retrieving procedure creation statements: No procedures found"
            in str(exc_info.value)
        )
        assert (
            "Error retrieving procedure creation statements: No procedures found"
            in caplog.text
        )

    def test_stream_triggers_statements_successfully(self, setup_method, seed_database):
        """
        Test to ensure that the MySQL database returns trigger creation statements.
        """
        db = setup_method
        cursor = seed_database
        trigger_statements = list(db.stream_triggers_statements(cursor))
        assert isinstance(trigger_statements, list)
        assert any(
            "TRIGGER" in stmt and "after_project_insert" in stmt
            for stmt in trigger_statements
        )
        assert any(
            "TRIGGER" in stmt and "after_employee_insert" in stmt
            for stmt in trigger_statements
        )

    def test_stream_triggers_statements_empty_database(
        self, setup_method, mocker, empty_database
    ):
        """
        Test to ensure that the MySQL database returns an empty string when no triggers exist.
        """
        db = setup_method
        cursor = empty_database
        trigger_statements = list(db.stream_triggers_statements(cursor))
        assert isinstance(trigger_statements, list)
        assert len(trigger_statements) == 0

    def test_stream_triggers_statements_failure(
        self, setup_method, mocker, empty_database, caplog
    ):
        """
        Ensure that an error is raised when the database has no triggers.
        """
        db = setup_method
        cursor = empty_database
        mocker.patch.object(
            cursor, "execute", side_effect=Exception("No triggers found")
        )
        with pytest.raises(RuntimeError) as exc_info:
            list(db.stream_triggers_statements(cursor))
        assert "Error retrieving trigger creation statements: No triggers found" in str(
            exc_info.value
        )
        assert (
            "Error retrieving trigger creation statements: No triggers found"
            in caplog.text
        )

    def test_stream_events_statements_successfully(self, setup_method, seed_database):
        """
        Test to ensure that the MySQL database returns event creation statements.
        """
        db = setup_method
        cursor = seed_database
        event_statements = list(db.stream_events_statements(cursor))
        assert isinstance(event_statements, list)
        event_statements = "".join(event_statements)
        assert "EVENT `dummy_event_1`" in event_statements
        assert "EVENT `dummy_event_2`" in event_statements
        assert "EVENT `dummy_event_3`" in event_statements
        assert "ALTER EVENT `dummy_event_1` ENABLE;" in event_statements
        assert "ALTER EVENT `dummy_event_2` ENABLE;" not in event_statements
        assert "ALTER EVENT `dummy_event_3` ENABLE;" in event_statements

    def test_stream_events_statements_empty_database(
        self, setup_method, empty_database
    ):
        """
        Test to ensure that the MySQL database returns an empty string when no events exist.
        """
        db = setup_method
        cursor = empty_database
        event_statements = list(db.stream_events_statements(cursor))
        assert isinstance(event_statements, list)
        assert len(event_statements) == 0

    def test_stream_events_statements_failure(
        self, setup_method, mocker, empty_database, caplog
    ):
        """
        Ensure that an error is raised when the database has no events.
        """
        db = setup_method
        cursor = empty_database
        mocker.patch.object(cursor, "execute", side_effect=Exception("No events found"))
        with pytest.raises(RuntimeError) as exc_info:
            list(db.stream_events_statements(cursor))
        assert "Error retrieving event creation statements: No events found" in str(
            exc_info.value
        )
        assert (
            "Error retrieving event creation statements: No events found" in caplog.text
        )
