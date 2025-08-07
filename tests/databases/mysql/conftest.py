# tests/databases/mysql/conftest.py
import pytest
import mysql.connector
from databases.mysql.mysql_utils import MySQLUtils
from pathlib import Path


@pytest.fixture
def empty_database(mysql_port):
    """
    Fixture to create an empty MySQL database for testing.
    """
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        port=mysql_port,
        database="test_db",
    )
    cursor = connection.cursor()
    yield cursor
    # Cleanup after tests
    cursor.close()
    connection.close()


@pytest.fixture
def seed_database(mysql_port):
    """
    Fixture that seed data to the database to use it with tests
    then run test then remove the database contents again
    """
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="test_db",
        port=mysql_port,
    )
    cursor = connection.cursor()
    seed_file = Path(__file__).parent.parent / "test_scripts" / "mysql_seed.sql"
    statements = MySQLUtils.convert_mysql_file_to_statments(str(seed_file))
    for statement in statements:
        cursor.execute(statement)
    connection.commit()

    yield cursor

    # Cleanup after tests
    restore_file = Path(__file__).parent.parent / "test_scripts" / "mysql_restore.sql"
    statements = MySQLUtils.convert_mysql_file_to_statments(str(restore_file))
    for statement in statements:
        cursor.execute(statement)
    connection.commit()
    cursor.close()
    connection.close()
