# tests/config_schemas.py/schemas/test_database_schema.py
from config_schemas.schemas.database_schema import DatabaseSchema, MySQLFeaturesSchema
import pytest


class TestDatabaseSchema:
    """
    Test cases for DatabaseSchema.
    This class contains tests to validate the DatabaseSchema
    and ensure it behaves as expected.
    """

    def test_database_schema_with_default_values(self):
        """
        Test DatabaseSchema with default values.
        """
        schema = DatabaseSchema(
            db_type="mysql",
            host="localhost",
            port=3306,
            user="test_user",
            db_name="test_db",
        )
        assert schema.db_type == "mysql"
        assert schema.host == "localhost"
        assert schema.port == 3306
        assert schema.db_name == "test_db"
        assert schema.user == "test_user"
        assert schema.multiple_files is False
        assert schema.restore_mode == "sql"
        assert schema.features.tables is not None

    def test_database_schema_with_empty_values(self):
        """
        Test DatabaseSchema with empty values.
        """
        with pytest.raises(ValueError) as exc_info:
            DatabaseSchema()
        assert "validation error" in str(exc_info.value)
        assert "required" in str(exc_info.value)

    def test_database_schema_with_invalid_db_type(self):
        """
        Test DatabaseSchema with an invalid db_type.
        """
        with pytest.raises(ValueError) as exc_info:
            DatabaseSchema(
                db_type="invalid_db",
                host="localhost",
                port=3306,
                user="test_user",
                db_name="test_db",
            )
        assert "validation error" in str(exc_info.value)
        assert "db_type" in str(exc_info.value)

    def test_mysql_features_schema_with_default_values(self):
        """
        Test MySQLFeaturesSchema with default values.
        """
        features = MySQLFeaturesSchema()
        assert features.tables is True
        assert features.data is True
        assert features.views is False
        assert features.functions is False
        assert features.procedures is False
        assert features.triggers is False
        assert features.events is False

    def test_mysql_features_schema_with_custom_values(self):
        """
        Test MySQLFeaturesSchema with custom values.
        """
        features = MySQLFeaturesSchema(
            tables=False,
            data=True,
            views=True,
            functions=True,
            procedures=False,
            triggers=True,
            events=False,
        )
        assert features.tables is False
        assert features.data is True
        assert features.views is True
        assert features.functions is True
        assert features.procedures is False
        assert features.triggers is True
        assert features.events is False

    def test_mysql_features_schema_with_no_features_enabled(self):
        """
        Test MySQLFeaturesSchema with no features enabled.
        """
        with pytest.raises(ValueError) as exc_info:
            MySQLFeaturesSchema(
                tables=False,
                data=False,
                views=False,
                functions=False,
                procedures=False,
                triggers=False,
                events=False,
            )
        assert "At least one MySQL feature must be enabled." in str(exc_info.value)
