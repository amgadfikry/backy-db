# tests/integration/test_databases_integration.py
from databases.database_manager import DatabaseManager
import pytest


@pytest.mark.usefixtures("require_mysql")
class TestDatabasesIntegration:
    """ """

    @pytest.fixture(autouse=True)
    def setup_database(self, request, mysql_port, monkeypatch):
        """
        Setup the database for testing.
        """
        # Set the password for the MySQL user
        monkeypatch.setenv("DB_PASSWORD", "test_password")
        config = {
            "db_type": "mysql",
            "host": "localhost",
            "port": mysql_port,
            "user": "test_user",
            "db_name": "test_db",
            "multiple_files": False,
            "features": {
                "tables": True,
                "data": True,
            },
            "restore_mode": "statement",
        }
        override = request.param if hasattr(request, "param") else {}
        config.update(override)
        db_manager = DatabaseManager(config)

        yield db_manager

        db_manager.connect()
        cursor = db_manager.db.connection.cursor()
        # Clean up the database after tests
        cursor.execute("DROP TABLE IF EXISTS test;")
        cursor.execute("DROP VIEW IF EXISTS test_view;")
        cursor.execute("DROP PROCEDURE IF EXISTS test_procedure;")
        db_manager.db.connection.commit()
        cursor.close()

    @pytest.fixture
    def statments(self):
        """
        Fixture to provide sample SQL statements for testing.
        """
        return [
            ("tables", "CREATE TABLE test (id INT PRIMARY KEY);"),
            ("data", "INSERT INTO test (id) VALUES (1);"),
            ("data", "INSERT INTO test (id) VALUES (2);"),
        ]

    def test_mysql_restore_statments_and_backup_them_one_file(
        self, setup_database, statments
    ):
        """
        Test that the restore statements are correctly generated and can be backed up.
        """
        db_manager = setup_database
        statements = statments
        # restore the statements to database
        with db_manager as manager:
            for feature, statement in statements:
                manager.restore((feature, statement))
        # Verify that the statements were executed
        with db_manager as manager:
            results = list(manager.backup())
        assert len(results) == 3
        assert results[0][0] == "full"

        db_manager.connect()
        cursor = db_manager.db.connection.cursor()
        cursor.execute("SELECT * FROM test;")
        rows = cursor.fetchall()
        assert len(rows) == 2

    @pytest.mark.parametrize(
        "setup_database", [{"multiple_files": True}], indirect=True
    )
    def test_mysql_restore_statements_and_backup_them_multiple_files(
        self, setup_database, statments
    ):
        """
        Test that the restore statements are correctly generated and can be backed up in multiple files.
        """
        db_manager = setup_database
        db_manager.db.multiple_files = True
        statements = statments
        # restore the statements to database
        with db_manager as manager:
            for feature, statement in statements:
                manager.restore((feature, statement))
        # Verify that the statements were executed
        with db_manager as manager:
            results = list(manager.backup())
        assert len(results) == 4
        assert results[0][0] == "tables"
        assert "-- Backup for Tables" in results[0][1]
        assert results[1][0] == "tables"
        assert "CREATE TABLE `test`" in results[1][1]
        assert results[2][0] == "data"
        assert "-- Backup for Data" in results[2][1]
        assert "INSERT INTO `test`" in results[3][1]

    @pytest.mark.parametrize(
        "setup_database", [{"restore_mode": "file"}], indirect=True
    )
    def test_mysql_restore_file_and_backup_them_one_file(
        self, setup_database, tmp_path, statments
    ):
        """
        Test that the restore file is correctly generated and can be backed up.
        """
        db_manager = setup_database
        db_manager.db.restore_mode = "file"
        # Create a backup file
        backup_file = tmp_path / "test_backup.sql"
        with open(backup_file, "w") as f:
            for feature, statement in statments:
                f.write(f"{statement}\n")

        # Restore the backup file to database
        with db_manager as manager:
            manager.restore(("full", backup_file))

        # Verify that the statements were executed
        with db_manager as manager:
            results = list(manager.backup())
        assert len(results) == 3
        assert results[0][0] == "full"
        assert "-- Backup" in results[0][1]
        assert results[1][0] == "full"
        assert "CREATE TABLE `test`" in results[1][1]
        assert results[2][0] == "full"
        assert "INSERT INTO `test`" in results[2][1]

    @pytest.mark.parametrize(
        "setup_database",
        [{"restore_mode": "file", "multiple_files": True}],
        indirect=True,
    )
    def test_mysql_restore_file_and_backup_them_multiple_files(
        self, setup_database, tmp_path, statments
    ):
        """
        Test that the restore file is correctly generated and can be backed up in multiple files.
        """
        db_manager = setup_database
        # Create a backup file
        backup_file = tmp_path / "test_backup.sql"
        with open(backup_file, "w") as f:
            for feature, statement in statments:
                f.write(f"{statement}\n")

        # Restore the backup file to database
        with db_manager as manager:
            manager.restore(("full", backup_file))

        # Verify that the statements were executed
        with db_manager as manager:
            results = list(manager.backup())
        assert len(results) == 4
        assert results[0][0] == "tables"
        assert "-- Backup for Tables" in results[0][1]
        assert results[1][0] == "tables"
        assert "CREATE TABLE `test`" in results[1][1]
        assert results[2][0] == "data"
        assert "-- Backup for Data" in results[2][1]
        assert "INSERT INTO `test`" in results[3][1]

    @pytest.mark.parametrize(
        "setup_database",
        [
            {
                "restore_mode": "statement",
                "multiple_files": True,
                "features": {
                    "tables": True,
                    "data": True,
                    "views": True,
                    "procedures": True,
                },
            }
        ],
        indirect=True,
    )
    def test_mysql_restore_statments_with_multiple_features_and_backup_them_multiple_files(
        self, setup_database
    ):
        """
        Test that the restore statements for all features are correctly generated and can be backed up.
        """
        db_manager = setup_database
        statements = [
            ("tables", "CREATE TABLE test (id INT PRIMARY KEY);"),
            ("data", "INSERT INTO test (id) VALUES (1);"),
            ("views", "CREATE VIEW test_view AS SELECT * FROM test;"),
            ("procedures", "CREATE PROCEDURE test_procedure() BEGIN SELECT 1; END;"),
        ]
        # restore the statements to database
        with db_manager as manager:
            for feature, statement in statements:
                manager.restore((feature, statement))
        # Verify that the statements were executed
        with db_manager as manager:
            results = list(manager.backup())
            for feature, statement in results:
                print(f"Feature: {feature}, Statement: {statement}")
        assert len(results) == 8
        assert results[0][0] == "tables"
        assert "-- Backup for Tables" in results[0][1]
        assert results[1][0] == "tables"
        assert "CREATE TABLE `test`" in results[1][1]
        assert results[2][0] == "data"
        assert "-- Backup for Data" in results[2][1]
        assert results[3][0] == "data"
        assert "INSERT INTO `test`" in results[3][1]
        assert results[4][0] == "views"
        assert "-- Backup for Views" in results[4][1]
        assert results[5][0] == "views"
        assert "VIEW `test_view`" in results[5][1]
        assert results[6][0] == "procedures"
        assert "-- Backup for Procedures" in results[6][1]
        assert results[7][0] == "procedures"
        assert "PROCEDURE `test_procedure`" in results[7][1]

    @pytest.mark.parametrize(
        "setup_database", [{"conflict_mode": "abort"}], indirect=True
    )
    def test_mysql_restore_statements_with_abort_conflict(self, setup_database):
        """
        Test that the restore statements with abort conflict mode raises an error on conflict.
        """
        db_manager = setup_database
        statements = [
            ("tables", "CREATE TABLE test (id INT PRIMARY KEY);"),
            ("data", "INSERT INTO test (id) VALUES (1);"),
        ]
        # restore the statements to database
        with db_manager as manager:
            for feature, statement in statements:
                manager.restore((feature, statement))

        # Attempt to restore conflicting statement
        with pytest.raises(RuntimeError):
            with db_manager as manager:
                manager.restore(("data", "INSERT INTO test (id) VALUES (1);"))

    def test_mysql_restore_statements_with_skip_conflict(self, setup_database):
        """
        Test that the restore statements with skip conflict mode skips conflicting statements.
        """
        db_manager = setup_database
        statements = [
            ("tables", "CREATE TABLE test (id INT PRIMARY KEY);"),
            ("data", "INSERT INTO test (id) VALUES (1);"),
        ]
        # restore the statements to database
        with db_manager as manager:
            for feature, statement in statements:
                manager.restore((feature, statement))

        # Attempt to restore conflicting statement
        with db_manager as manager:
            manager.restore(("data", "INSERT INTO test (id) VALUES (1);"))
            manager.restore(("data", "INSERT INTO test (id) VALUES (2);"))

        # Verify that the statements were executed
        with db_manager as manager:
            results = list(manager.backup())
        assert len(results) == 3
        assert results[0][0] == "full"
        assert "-- Backup" in results[0][1]
        assert results[1][0] == "full"
        assert "CREATE TABLE `test`" in results[1][1]
        assert results[2][0] == "full"

        db_manager.connect()
        cursor = db_manager.db.connection.cursor()
        cursor.execute("SELECT * FROM test;")
        rows = cursor.fetchall()
        assert len(rows) == 2
        assert rows[0][0] == 1
        assert rows[1][0] == 2
        cursor.close()

    @pytest.mark.parametrize(
        "setup_database",
        [{"restore_mode": "statement", "multiple_files": True}],
        indirect=True,
    )
    def test_mysql_restore_statements_and_backup_2000_data_multiple_files(
        self, setup_database
    ):
        """
        Test that the restore statements with 2000 data can be backed up.
        """
        db_manager = setup_database
        statements = [
            ("tables", "CREATE TABLE test (id INT PRIMARY KEY);"),
        ]
        statements.extend(
            [("data", f"INSERT INTO test (id) VALUES ({i});") for i in range(2000)]
        )

        # restore the statements to database
        with db_manager as manager:
            for feature, statement in statements:
                manager.restore((feature, statement))

        # Verify that the statements were executed
        with db_manager as manager:
            results = list(manager.backup())

        assert len(results) == 5

        db_manager.connect()
        cursor = db_manager.db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM test;")
        count = cursor.fetchone()[0]
        assert count == 2000
        cursor.close()
