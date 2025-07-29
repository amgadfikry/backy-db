# tests/utils/test_to_sql_values.py
from utils.to_sql_values import to_sql_values
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID
import json


class TestToSQLValues:
    """
    Test cases for the to_sql_values function.
    """

    def test_to_sql_values_with_None(self):
        """
        Test that None values are converted to SQL NULL.
        """
        assert to_sql_values((None,)) == "NULL"
        assert to_sql_values((None, None)) == "NULL, NULL"

    def test_to_sql_values_with_bool(self):
        """
        Test that boolean values are converted to SQL boolean.
        """
        assert to_sql_values((True,)) == "1"
        assert to_sql_values((False,)) == "0"
        assert to_sql_values((True, False)) == "1, 0"

    def test_to_sql_values_with_numbers(self):
        """
        Test that numeric values are converted to their string representation.
        """
        assert to_sql_values((123,)) == "123"
        assert to_sql_values((123.456,)) == "123.456"
        assert to_sql_values((Decimal("123.456"),)) == "123.456"
        assert to_sql_values((123, 456.789)) == "123, 456.789"
        assert (
            to_sql_values((Decimal("123.456"), Decimal("789.012")))
            == "123.456, 789.012"
        )

    def test_to_sql_values_with_datetime(self):
        """
        Test that datetime, date, and time values are formatted correctly.
        """
        dt = datetime(2023, 10, 1, 12, 30, 45)
        assert to_sql_values((dt,)) == f"'{dt.isoformat(sep=' ', timespec='seconds')}'"
        assert (
            to_sql_values((dt, dt))
            == f"'{dt.isoformat(sep=' ', timespec='seconds')}', '{dt.isoformat(sep=' ', timespec='seconds')}'"
        )
        ti = time(12, 30, 45)
        assert to_sql_values((ti,)) == f"'{ti.isoformat(timespec='seconds')}'"
        assert (
            to_sql_values((dt, ti))
            == f"'{dt.isoformat(sep=' ', timespec='seconds')}', '{ti.isoformat(timespec='seconds')}'"
        )
        d = date(2023, 10, 1)
        assert to_sql_values((d,)) == f"'{d.isoformat()}'"
        assert (
            to_sql_values((d, dt))
            == f"'{d.isoformat()}', '{dt.isoformat(sep=' ', timespec='seconds')}'"
        )

    def test_to_sql_values_with_bytes(self):
        """
        Test that bytes and bytearray values are converted to hexadecimal format.
        """
        b = b"\x00\x01\x02"
        assert to_sql_values((b,)) == f"X'{b.hex()}'"
        assert to_sql_values((b, b)) == f"X'{b.hex()}', X'{b.hex()}'"
        barray = bytearray(b"\x03\x04\x05")
        assert to_sql_values((barray,)) == f"X'{barray.hex()}'"
        assert to_sql_values((b, barray)) == f"X'{b.hex()}', X'{barray.hex()}'"

    def test_to_sql_values_with_uuid(self):
        """
        Test that UUID values are formatted correctly.
        """
        uid = UUID("12345678-1234-5678-1234-567812345678")
        assert to_sql_values((uid,)) == f"'{str(uid)}'"
        assert to_sql_values((uid, uid)) == f"'{str(uid)}', '{str(uid)}'"

    def test_to_sql_values_with_dict_and_list(self):
        """
        Test that dict and list values are converted to JSON strings.
        """
        d = {"key": "value"}
        li = [1, 2, 3]
        assert to_sql_values((d,)) == f"'{json.dumps(d).replace("'", "''")}'"
        assert to_sql_values((li,)) == f"'{json.dumps(li).replace("'", "''")}'"
        assert (
            to_sql_values((d, li))
            == f"'{json.dumps(d).replace("'", "''")}', '{json.dumps(li).replace("'", "''")}'"
        )
        assert (
            to_sql_values((li, d))
            == f"'{json.dumps(li).replace("'", "''")}', '{json.dumps(d).replace("'", "''")}'"
        )

    def test_to_sql_values_string_escaping(self):
        """
        Test that strings with single quotes are escaped correctly.
        """
        assert to_sql_values(("O'Reilly",)) == "'O''Reilly'"
        assert to_sql_values(("Hello 'World'",)) == "'Hello ''World'''"
        assert (
            to_sql_values(("Normal String", "String with 'quote'"))
            == "'Normal String', 'String with ''quote'''"
        )
        assert (
            to_sql_values(('String with "double quotes"',))
            == "'String with \"double quotes\"'"
        )

    def test_to_sql_values_mixed_types(self):
        """
        Test that a mix of different types is handled correctly.
        """
        dt = datetime(2023, 10, 1, 12, 30, 45)
        uid = UUID("12345678-1234-5678-1234-567812345678")
        assert (
            to_sql_values((None, True, 123, dt, uid))
            == "NULL, 1, 123, '2023-10-01 12:30:45', '12345678-1234-5678-1234-567812345678'"
        )
        assert (
            to_sql_values(
                (False, 456.789, b"\x00\x01", date(2023, 10, 1), time(12, 30))
            )
            == "0, 456.789, X'0001', '2023-10-01', '12:30:00'"
        )
