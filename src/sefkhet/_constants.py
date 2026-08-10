"""Defines constants used in `sefkhet`."""

from typing import TYPE_CHECKING as _TYPE_CHECKING


if _TYPE_CHECKING:  # pragma: no cover
    import logging


# Define fields with existing formatter interpolations
_KNOWN_FIELDS: frozenset[str] = frozenset(
    {
        "timestamp",
        "level",
        "levelno",
        "message",
        "logger",
        "module",
        "funcName",
        "lineno",
        "pathname",
    }
)

# Attributes that are standard on every LogRecord and should
# not be treated as "extra" fields.
_STANDARD_RECORD_ATTRS: frozenset[str] = frozenset(
    {
        "args",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
    }
)


def _extract_known_field(  # pyright: ignore[reportUnusedFunction]
    field: str, record: "logging.LogRecord", formatter: "logging.Formatter"
) -> object:
    """
    Extracts a known field value from a `LogRecord`.

    Args:
        field (str): The field name to extract
        record (logging.LogRecord): The log record
        formatter (logging.Formatter): The formatter instance,
            used for `formatTime`

    Returns:
        object: The extracted field value
    """
    # Handle special time and message cases
    if field == "timestamp":
        return formatter.formatTime(record, formatter.datefmt)
    if field == "message":
        return record.getMessage()
    # All remaining known fields are simple record attributes
    attr_map: dict[str, str] = {
        "level": "levelname",
        "levelno": "levelno",
        "logger": "name",
        "module": "module",
        "funcName": "funcName",
        "lineno": "lineno",
        "pathname": "pathname",
    }
    return getattr(record, attr_map[field])
