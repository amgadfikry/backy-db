# tests/databases/mysql/test_mysql_utils.py
import pytest
from databases.mysql.mysql_utils import MySQLUtils
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID
import json


class TestMySQLUtils:
    """
    This class tests the MySQL utility functions for database operations.
    """

    def test_create_mysql_file_opening(self):
        """
        Test the creation of the opening SQL statements for the backup file.
        """
        db_name = "test_db"
        opening_statements = MySQLUtils.create_mysql_file_opening(db_name)
        expected_statements = (
            f"-- Backup for {db_name}\n"
            f"CREATE DATABASE IF NOT EXISTS `{db_name}`;\n"
            f"USE `{db_name}`;\n\n"
        )
        assert opening_statements == expected_statements

    def test_raw_to_mysql_values_with_None(self):
        """
        Test that None values are converted to MySQL NULL.
        """
        assert MySQLUtils.raw_to_mysql_values((None,)) == "NULL"
        assert MySQLUtils.raw_to_mysql_values((None, None)) == "NULL, NULL"

    def test_raw_to_mysql_values_with_bool(self):
        """
        Test that boolean values are converted to MySQL boolean.
        """
        assert MySQLUtils.raw_to_mysql_values((True,)) == "1"
        assert MySQLUtils.raw_to_mysql_values((False,)) == "0"
        assert MySQLUtils.raw_to_mysql_values((True, False)) == "1, 0"

    def test_raw_to_mysql_values_with_numbers(self):
        """
        Test that numeric values are converted to their string representation.
        """
        assert MySQLUtils.raw_to_mysql_values((123,)) == "123"
        assert MySQLUtils.raw_to_mysql_values((123.456,)) == "123.456"
        assert MySQLUtils.raw_to_mysql_values((Decimal("123.456"),)) == "123.456"
        assert MySQLUtils.raw_to_mysql_values((123, 456.789)) == "123, 456.789"
        assert (
            MySQLUtils.raw_to_mysql_values((Decimal("123.456"), Decimal("789.012")))
            == "123.456, 789.012"
        )

    def test_raw_to_mysql_values_with_datetime(self):
        """
        Test that datetime, date, and time values are formatted correctly.
        """
        dt = datetime(2023, 10, 1, 12, 30, 45)
        assert (
            MySQLUtils.raw_to_mysql_values((dt,))
            == f"'{dt.isoformat(sep=' ', timespec='seconds')}'"
        )
        assert (
            MySQLUtils.raw_to_mysql_values((dt, dt))
            == f"'{dt.isoformat(sep=' ', timespec='seconds')}', '{dt.isoformat(sep=' ', timespec='seconds')}'"
        )
        ti = time(12, 30, 45)
        assert (
            MySQLUtils.raw_to_mysql_values((ti,))
            == f"'{ti.isoformat(timespec='seconds')}'"
        )
        assert (
            MySQLUtils.raw_to_mysql_values((dt, ti))
            == f"'{dt.isoformat(sep=' ', timespec='seconds')}', '{ti.isoformat(timespec='seconds')}'"
        )
        d = date(2023, 10, 1)
        assert MySQLUtils.raw_to_mysql_values((d,)) == f"'{d.isoformat()}'"
        assert (
            MySQLUtils.raw_to_mysql_values((d, dt))
            == f"'{d.isoformat()}', '{dt.isoformat(sep=' ', timespec='seconds')}'"
        )

    def test_raw_to_mysql_values_with_bytes(self):
        """
        Test that bytes and bytearray values are converted to hexadecimal format.
        """
        b = b"\x00\x01\x02"
        assert MySQLUtils.raw_to_mysql_values((b,)) == f"X'{b.hex()}'"
        assert MySQLUtils.raw_to_mysql_values((b, b)) == f"X'{b.hex()}', X'{b.hex()}'"
        barray = bytearray(b"\x03\x04\x05")
        assert MySQLUtils.raw_to_mysql_values((barray,)) == f"X'{barray.hex()}'"
        assert (
            MySQLUtils.raw_to_mysql_values((b, barray))
            == f"X'{b.hex()}', X'{barray.hex()}'"
        )

    def test_raw_to_mysql_values_with_uuid(self):
        """
        Test that UUID values are formatted correctly.
        """
        uid = UUID("12345678-1234-5678-1234-567812345678")
        assert MySQLUtils.raw_to_mysql_values((uid,)) == f"'{str(uid)}'"
        assert (
            MySQLUtils.raw_to_mysql_values((uid, uid)) == f"'{str(uid)}', '{str(uid)}'"
        )

    def test_raw_to_mysql_values_with_dict_and_list(self):
        """
        Test that dict and list values are converted to JSON strings.
        """
        d = {"key": "value"}
        li = [1, 2, 3]
        assert (
            MySQLUtils.raw_to_mysql_values((d,))
            == f"'{json.dumps(d).replace("'", "''")}'"
        )
        assert (
            MySQLUtils.raw_to_mysql_values((li,))
            == f"'{json.dumps(li).replace("'", "''")}'"
        )
        assert (
            MySQLUtils.raw_to_mysql_values((d, li))
            == f"'{json.dumps(d).replace("'", "''")}', '{json.dumps(li).replace("'", "''")}'"
        )
        assert (
            MySQLUtils.raw_to_mysql_values((li, d))
            == f"'{json.dumps(li).replace("'", "''")}', '{json.dumps(d).replace("'", "''")}'"
        )

    def test_raw_to_mysql_values_string_escaping(self):
        """
        Test that strings with single quotes are escaped correctly.
        """
        assert MySQLUtils.raw_to_mysql_values(("O'Reilly",)) == "'O''Reilly'"
        assert MySQLUtils.raw_to_mysql_values(("Hello 'World'",)) == "'Hello ''World'''"
        assert (
            MySQLUtils.raw_to_mysql_values(("Normal String", "String with 'quote'"))
            == "'Normal String', 'String with ''quote'''"
        )
        assert (
            MySQLUtils.raw_to_mysql_values(('String with "double quotes"',))
            == "'String with \"double quotes\"'"
        )

    def test_raw_to_mysql_values_mixed_types(self):
        """
        Test that a mix of different types is handled correctly.
        """
        dt = datetime(2023, 10, 1, 12, 30, 45)
        uid = UUID("12345678-1234-5678-1234-567812345678")
        assert (
            MySQLUtils.raw_to_mysql_values((None, True, 123, dt, uid))
            == "NULL, 1, 123, '2023-10-01 12:30:45', '12345678-1234-5678-1234-567812345678'"
        )
        assert (
            MySQLUtils.raw_to_mysql_values(
                (False, 456.789, b"\x00\x01", date(2023, 10, 1), time(12, 30))
            )
            == "0, 456.789, X'0001', '2023-10-01', '12:30:00'"
        )

    def test_convert_mysql_file_to_statments_remove_comments(self, tmp_path):
        """
        Test the conversion of a MySQL file to statements.
        """
        file_path = tmp_path / "test_backup.sql"
        with open(file_path, "w") as f:
            f.write("-- This is a comment\n")
            f.write("CREATE DATABASE IF NOT EXISTS `test_db`;\n")
            f.write("-- Another comment\n")

        statements = list(MySQLUtils.convert_mysql_file_to_statments(str(file_path)))
        assert len(statements) == 1
        assert statements[0] == "CREATE DATABASE IF NOT EXISTS `test_db`"

    def test_convert_mysql_file_to_statments_empty_file(self, tmp_path):
        """
        Test the conversion of an empty MySQL file.
        """
        file_path = tmp_path / "empty_backup.sql"
        with open(file_path, "w"):
            pass

        statements = list(MySQLUtils.convert_mysql_file_to_statments(str(file_path)))
        assert len(statements) == 0

    def test_convert_mysql_file_to_statments_multiple_empty_lines(self, tmp_path):
        """
        Test the conversion of a MySQL file with multiple empty lines.
        """
        file_path = tmp_path / "multiple_empty_lines.sql"
        with open(file_path, "w") as f:
            f.write("\n\n-- Comment line\n\n")
            f.write("USE `test_db`;\n\n")

        statements = list(MySQLUtils.convert_mysql_file_to_statments(str(file_path)))
        assert len(statements) == 1
        assert statements[0] == "USE `test_db`"

    def test_convert_mysql_file_to_statments_with_dilmiter(self, tmp_path):
        """
        Test the conversion of a MySQL file with custom delimiters.
        """
        file_path = tmp_path / "custom_delimiter.sql"
        with open(file_path, "w") as f:
            f.write("-- This is a comment\n")
            f.write("DELIMITER //\n")
            f.write("CREATE PROCEDURE test_proc()\n")
            f.write("BEGIN\n")
            f.write("SELECT 1;\n")
            f.write("END //\n")
            f.write("DELIMITER ;\n")

        statements = list(MySQLUtils.convert_mysql_file_to_statments(str(file_path)))
        assert len(statements) == 1
        assert statements[0] == "CREATE PROCEDURE test_proc()\nBEGIN\nSELECT 1;\nEND"

    def test_convert_mysql_file_to_statments_with_different_delimiters(self, tmp_path):
        """
        Test the conversion of a MySQL file with different delimiters.
        """
        file_path = tmp_path / "different_delimiters.sql"
        with open(file_path, "w") as f:
            f.write("-- This is a comment\n")
            f.write("DELIMITER $$\n")
            f.write("CREATE TRIGGER test_trigger BEFORE INSERT ON test_table\n")
            f.write("FOR EACH ROW BEGIN\n")
            f.write("SET NEW.column = 'value';\n")
            f.write("END$$\n")
            f.write("DELIMITER ;\n")

        statements = list(MySQLUtils.convert_mysql_file_to_statments(str(file_path)))
        assert len(statements) == 1
        assert (
            statements[0]
            == "CREATE TRIGGER test_trigger BEFORE INSERT ON test_table\nFOR EACH ROW BEGIN\nSET NEW.column = 'value';\nEND"
        )

    def test_convert_mysql_file_to_statments_with_empty_lines_inside_dilimiter(
        self, tmp_path
    ):
        """
        Test the conversion of a MySQL file with empty lines inside a delimiter block.
        """
        file_path = tmp_path / "empty_lines_inside_delimiter.sql"
        with open(file_path, "w") as f:
            f.write("-- This is a comment\n")
            f.write("DELIMITER //\n\n")
            f.write("CREATE PROCEDURE test_empty()\n")
            f.write("BEGIN\n")
            f.write("\n")
            f.write("SELECT 1;\n")
            f.write("\n")
            f.write("END //\n\n")
            f.write("DELIMITER ;\n")

        statements = list(MySQLUtils.convert_mysql_file_to_statments(str(file_path)))
        assert len(statements) == 1
        assert statements[0] == "CREATE PROCEDURE test_empty()\nBEGIN\nSELECT 1;\nEND"

    def test_convert_mysql_file_to_statments_with_multiple_inside_dilimiter(
        self, tmp_path
    ):
        """
        Test the conversion of a MySQL file with multiple statements inside a delimiter block.
        """
        file_path = tmp_path / "multiple_statements_inside_delimiter.sql"
        with open(file_path, "w") as f:
            f.write("-- This is a comment\n")
            f.write("DELIMITER //\n")
            f.write("CREATE PROCEDURE test_multi()\n")
            f.write("BEGIN\n")
            f.write("SELECT 1;\n")
            f.write("SELECT 2;\n")
            f.write("END //\n")
            f.write("//\n")
            f.write("CREATE PROCEDURE test_another()\n")
            f.write("BEGIN\n")
            f.write("SELECT 3;\n")
            f.write("END //\n")
            f.write("DELIMITER ;\n")

        statements = list(MySQLUtils.convert_mysql_file_to_statments(str(file_path)))
        assert len(statements) == 2
        assert (
            statements[0]
            == "CREATE PROCEDURE test_multi()\nBEGIN\nSELECT 1;\nSELECT 2;\nEND"
        )
        assert statements[1] == "CREATE PROCEDURE test_another()\nBEGIN\nSELECT 3;\nEND"

    def test_convert_mysql_file_to_statments_with_space_around_statement(
        self, tmp_path
    ):
        """
        Test the conversion of a MySQL file with spaces around statements.
        """
        file_path = tmp_path / "spaces_around_statement.sql"
        with open(file_path, "w") as f:
            f.write("   -- This is a comment\n")
            f.write("   CREATE TABLE test_table (id INT);\n   ")
            f.write("   INSERT INTO test_table (id) VALUES (1);\n   ")

        statements = list(MySQLUtils.convert_mysql_file_to_statments(str(file_path)))
        assert len(statements) == 2
        assert statements[0] == "CREATE TABLE test_table (id INT)"
        assert statements[1] == "INSERT INTO test_table (id) VALUES (1)"

    def test_convert_mysql_file_to_statements_ignores_blank_delimiter_line(
        self, tmp_path
    ):
        """
        Test the conversion of a MySQL file with a blank line containing just the delimiter.
        """
        file_path = tmp_path / "blank_delimiter_line.sql"
        with open(file_path, "w") as f:
            f.write("DELIMITER //\n")
            f.write("CREATE PROCEDURE test()\nBEGIN\nSELECT 1;\nEND //\n")
            f.write("//\n")  # blank line with just the delimiter
            f.write("CREATE PROCEDURE test2()\nBEGIN\nSELECT 2;\nEND //\n")
            f.write("DELIMITER ;\n")

        statements = list(MySQLUtils.convert_mysql_file_to_statments(str(file_path)))
        assert statements == [
            "CREATE PROCEDURE test()\nBEGIN\nSELECT 1;\nEND",
            "CREATE PROCEDURE test2()\nBEGIN\nSELECT 2;\nEND",
        ]

    def test_convert_mysql_file_to_statements_malformed_delimiter(self, tmp_path):
        """
        Test the conversion of a MySQL file with a malformed delimiter line.
        """
        file_path = tmp_path / "malformed_delimiter.sql"
        with open(file_path, "w") as f:
            f.write("DELIMITER\n")  # Missing the actual delimiter
            f.write("CREATE TABLE x (id INT);\n")

        with pytest.raises(ValueError) as exc_info:
            list(MySQLUtils.convert_mysql_file_to_statments(str(file_path)))
        assert "Error processing SQL file" in str(exc_info.value)

    def test_multiple_consecutive_delimiters(self, tmp_path):
        """
        Test the conversion of a MySQL file with multiple consecutive delimiter lines.
        """
        file_path = tmp_path / "multiple_consecutive_delimiters.sql"
        with open(file_path, "w") as f:
            f.write("DELIMITER //\n")
            f.write("DELIMITER $$\n")  # Should override previous one
            f.write("CREATE PROCEDURE x()\nBEGIN\nSELECT 1;\nEND$$\n")

        statements = list(MySQLUtils.convert_mysql_file_to_statments(str(file_path)))
        assert statements == ["CREATE PROCEDURE x()\nBEGIN\nSELECT 1;\nEND"]

    def test_delimiter_with_inline_comment(self, tmp_path):
        """
        Test the conversion of a MySQL file with a delimiter line that includes an inline comment.
        """
        file_path = tmp_path / "delimiter_with_inline_comment.sql"
        with open(file_path, "w") as f:
            f.write("DELIMITER // -- change delimiter\n")
            f.write("CREATE PROCEDURE x()\nBEGIN\nSELECT 1;\nEND //\n")
            f.write("DELIMITER ; -- back to normal\n")

        statements = list(MySQLUtils.convert_mysql_file_to_statments(str(file_path)))
        assert statements == ["CREATE PROCEDURE x()\nBEGIN\nSELECT 1;\nEND"]

    def test_convert_mysql_file_to_statements_with_4_statements(self, tmp_path):
        """
        Test the conversion of a MySQL file with multiple statements.
        """
        file_path = tmp_path / "multiple_statements.sql"
        with open(file_path, "w") as f:
            f.write("CREATE TABLE test (id INT);\n")
            f.write("INSERT INTO test (id) VALUES (1);\n")
            f.write("UPDATE test SET id = 2 WHERE id = 1;\n")
            f.write("DELETE FROM test WHERE id = 2;\n")

        statements = list(MySQLUtils.convert_mysql_file_to_statments(str(file_path)))
        assert len(statements) == 4
        assert statements[0] == "CREATE TABLE test (id INT)"
        assert statements[1] == "INSERT INTO test (id) VALUES (1)"
        assert statements[2] == "UPDATE test SET id = 2 WHERE id = 1"
        assert statements[3] == "DELETE FROM test WHERE id = 2"

    def test_clean_single_sql_statement_empty(self):
        """
        Test the cleaning of an empty SQL statement.
        """
        sql = ""
        cleaned = MySQLUtils().clean_single_sql_statement(sql)
        assert cleaned == ""

    def test_clean_single_sql_statement_comment_only(self):
        """
        Test the cleaning of a SQL statement that contains only comments.
        """
        sql = "-- This is a comment"
        cleaned = MySQLUtils().clean_single_sql_statement(sql)
        assert cleaned == ""

    def test_clean_single_sql_statement_create_database_statement(self):
        """
        Test the cleaning of a CREATE DATABASE SQL statement.
        """
        sql = (
            "-- CREATE DATABASE `test_db`\n"
            "CREATE DATABASE `test_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"
        )
        cleaned = MySQLUtils().clean_single_sql_statement(sql)
        expected = "CREATE DATABASE `test_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
        assert cleaned == expected

    def test_clean_single_sql_statement_use_database_statement(self):
        """
        Test the cleaning of a USE DATABASE SQL statement.
        """
        sql = "-- USE `test_db`\nUSE `test_db`;"
        cleaned = MySQLUtils().clean_single_sql_statement(sql)
        expected = "USE `test_db`"
        assert cleaned == expected

    def test_clean_single_sql_statement_table_statement(self):
        """
        Test the cleaning of a single SQL statement.
        """
        sql = (
            "-- CREATE TABLE `users`\n"
            "CREATE TABLE `users` (\n"
            "  `user_id` int NOT NULL AUTO_INCREMENT,\n"
            "  `username` varchar(50) NOT NULL,\n"
            "  PRIMARY KEY (`user_id`)\n"
            ") ENGINE=InnoDB AUTO_INCREMENT=1048561 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;"
        )
        cleaned = MySQLUtils().clean_single_sql_statement(sql)
        expected = (
            "CREATE TABLE `users` (\n"
            "  `user_id` int NOT NULL AUTO_INCREMENT,\n"
            "  `username` varchar(50) NOT NULL,\n"
            "  PRIMARY KEY (`user_id`)\n"
            ") ENGINE=InnoDB AUTO_INCREMENT=1048561 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
        )
        assert cleaned == expected

    def test_clean_single_sql_statement_insert_statement(self):
        """
        Test the cleaning of an INSERT SQL statement.
        """
        sql = (
            "-- INSERT INTO `users` VALUES\n"
            "INSERT INTO `users` VALUES\n"
            "\t(1, 'user_1'),\n"
            "\t(2, 'user_2'),\n"
            "\t(3, 'user_3');"
        )
        cleaned = MySQLUtils().clean_single_sql_statement(sql)
        expected = (
            "INSERT INTO `users` VALUES\n"
            "\t(1, 'user_1'),\n"
            "\t(2, 'user_2'),\n"
            "\t(3, 'user_3')"
        )
        assert cleaned == expected

    def test_clean_single_sql_statement_views_statement(self):
        """
        Test the cleaning of a VIEW SQL statement.
        """
        sql = (
            "-- CREATE VIEW `user_view`\n"
            "CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`%` SQL SECURITY DEFINER VIEW `v_orders_users_50k` AS\n"
            "SELECT `o`.`order_id` AS `order_id`,\n"
            "`o`.`order_date` AS `order_date`,\n"
            "`u`.`username` AS `username`\n"
            "FROM (`orders` `o`\n"
            "JOIN `users` `u` on((`o`.`user_id` = `u`.`user_id`)))\n"
            "ORDER BY `o`.`order_id`\n"
            "LIMIT 50000;"
        )
        cleaned = MySQLUtils().clean_single_sql_statement(sql)
        expected = (
            "CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`%` SQL SECURITY DEFINER VIEW `v_orders_users_50k` AS\n"
            "SELECT `o`.`order_id` AS `order_id`,\n"
            "`o`.`order_date` AS `order_date`,\n"
            "`u`.`username` AS `username`\n"
            "FROM (`orders` `o`\n"
            "JOIN `users` `u` on((`o`.`user_id` = `u`.`user_id`)))\n"
            "ORDER BY `o`.`order_id`\n"
            "LIMIT 50000"
        )
        cleaned = MySQLUtils().clean_single_sql_statement(sql)
        assert cleaned == expected

    def test_clean_single_sql_statement_function_statement(self):
        """
        Test the cleaning of a FUNCTION SQL statement.
        """
        sql = (
            "-- Create Get_total_orders_for_user Function\n"
            "DELIMITER $$\n"
            "CREATE DEFINER=`root`@`%` FUNCTION `get_total_orders_for_user`(p_user_id INT) RETURNS int\n"
            "    DETERMINISTIC\n"
            "BEGIN\n"
            "    DECLARE order_count INT;\n"
            "    SELECT COUNT(*) INTO order_count\n"
            "    FROM orders\n"
            "    WHERE user_id = p_user_id;\n"
            "    RETURN IFNULL(order_count, 0);\n"
            "END\n"
            "$$\n"
            "DELIMITER ;"
        )
        cleaned = MySQLUtils().clean_single_sql_statement(sql)
        expected = (
            "CREATE DEFINER=`root`@`%` FUNCTION `get_total_orders_for_user`(p_user_id INT) RETURNS int\n"
            "    DETERMINISTIC\n"
            "BEGIN\n"
            "    DECLARE order_count INT;\n"
            "    SELECT COUNT(*) INTO order_count\n"
            "    FROM orders\n"
            "    WHERE user_id = p_user_id;\n"
            "    RETURN IFNULL(order_count, 0);\n"
            "END"
        )
        assert cleaned == expected

    def test_clean_single_sql_statement_procedure_statement(self):
        """
        Test the cleaning of a PROCEDURE SQL statement.
        """
        sql = (
            "-- Create Sp_get_total_orders_for_user Procedure\n"
            "DELIMITER //\n"
            "CREATE DEFINER=`root`@`%` PROCEDURE `sp_get_total_orders_for_user`(IN p_user_id INT, OUT p_order_count INT)\n"
            "BEGIN\n"
            "    SELECT COUNT(*) INTO p_order_count\n"
            "    FROM orders\n"
            "    WHERE user_id = p_user_id;\n"
            "END\n"
            "//\n"
            "DELIMITER ;\n\n"
        )
        cleaned = MySQLUtils().clean_single_sql_statement(sql)
        expected = (
            "CREATE DEFINER=`root`@`%` PROCEDURE `sp_get_total_orders_for_user`(IN p_user_id INT, OUT p_order_count INT)\n"
            "BEGIN\n"
            "    SELECT COUNT(*) INTO p_order_count\n"
            "    FROM orders\n"
            "    WHERE user_id = p_user_id;\n"
            "END"
        )
        assert cleaned == expected

    def test_clean_single_sql_statement_trigger_statement(self):
        """
        Test the cleaning of a TRIGGER SQL statement.
        """
        sql = (
            "-- Create Trg_after_order_item_insert Trigger\n"
            "DELIMITER $$\n"
            "CREATE DEFINER=`root`@`%` TRIGGER `trg_after_order_item_insert` AFTER INSERT ON `order_items` FOR EACH ROW BEGIN\n"
            "    INSERT INTO user_activity_log(user_id, activity)\n"
            "    VALUES (NEW.user_id, CONCAT('New order item added: ', NEW.product_name, ', qty: ', NEW.quantity));\n"
            "END\n"
            "$$\n"
            "DELIMITER ;\n\n"
        )
        cleaned = MySQLUtils().clean_single_sql_statement(sql)
        expected = (
            "CREATE DEFINER=`root`@`%` TRIGGER `trg_after_order_item_insert` AFTER INSERT ON `order_items` FOR EACH ROW BEGIN\n"
            "    INSERT INTO user_activity_log(user_id, activity)\n"
            "    VALUES (NEW.user_id, CONCAT('New order item added: ', NEW.product_name, ', qty: ', NEW.quantity));\n"
            "END"
        )
        assert cleaned == expected

    def test_clean_single_sql_statement_event_statement(self):
        """
        Test the cleaning of an EVENT SQL statement.
        """
        sql = (
            "-- Create Ev_log_daily_order_count Event\n"
            "DELIMITER $$\n"
            "CREATE DEFINER=`root`@`%` EVENT `ev_log_daily_order_count` ON SCHEDULE EVERY 1 DAY STARTS '2025-08-09 12:55:27' ON COMPLETION NOT PRESERVE DISABLE DO BEGIN\n"
            "    INSERT INTO user_activity_log(user_id, activity)\n"
            "    SELECT user_id, CONCAT('Daily order count: ', COUNT(*))\n"
            "    FROM orders\n"
            "    GROUP BY user_id;\n"
            "END;\n"
            "$$\n"
            "DELIMITER ;\n"
        )
        cleaned = MySQLUtils().clean_single_sql_statement(sql)
        expected = (
            "CREATE DEFINER=`root`@`%` EVENT `ev_log_daily_order_count` ON SCHEDULE EVERY 1 DAY STARTS '2025-08-09 12:55:27' ON COMPLETION NOT PRESERVE DISABLE DO BEGIN\n"
            "    INSERT INTO user_activity_log(user_id, activity)\n"
            "    SELECT user_id, CONCAT('Daily order count: ', COUNT(*))\n"
            "    FROM orders\n"
            "    GROUP BY user_id;\n"
            "END"
        )
        assert cleaned == expected
        
    def test_clean_single_sql_statement_with_alter_event_statement(self):
        """
        Test the cleaning of an ALTER EVENT SQL statement.
        """
        sql = (
            "-- Alter Ev_log_daily_order_count Event\n"
            "ALTER EVENT `ev_log_daily_order_count` ENABLE;\n"
        )
        cleaned = MySQLUtils().clean_single_sql_statement(sql)
        expected = (
            "ALTER EVENT `ev_log_daily_order_count` ENABLE"
        )
        assert cleaned == expected
