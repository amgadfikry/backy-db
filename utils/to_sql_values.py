# utils/to_sql_values.py
import json
from decimal import Decimal
from uuid import UUID
from datetime import datetime, date, time
from typing import Any


def format_value(val: Any) -> str:
    """Format a single value for SQL insertion.
    Args:
        val: The value to format.
    Returns:
        str: A string representation of the value suitable for SQL insertion.
    """
    if val is None:
        return "NULL"
    elif isinstance(val, bool):
        return "1" if val else "0"
    elif isinstance(val, (int, float, Decimal)):
        return str(val)
    elif isinstance(val, datetime):
        return f"'{val.isoformat(sep=' ', timespec='seconds')}'"
    elif isinstance(val, time):
        return f"'{val.isoformat(timespec='seconds')}'"
    elif isinstance(val, date):
        return f"'{val.isoformat()}'"
    elif isinstance(val, (bytes, bytearray)):
        return f"X'{val.hex()}'"
    elif isinstance(val, UUID):
        return f"'{str(val)}'"
    elif isinstance(val, (dict, list)):
        escaped = json.dumps(val).replace("'", "''")
        return f"'{escaped}'"
    else:
        escaped = str(val).replace("'", "''")
        return f"'{escaped}'"


def to_sql_values(row: tuple) -> str:
    """Convert a row of data into a SQL-compatible string representation.
    Args:
        row (tuple): A tuple containing the values of the row.
    Returns:
        str: A string representation of the row values suitable for SQL insertion.
    """
    return ", ".join(format_value(v) for v in row)
