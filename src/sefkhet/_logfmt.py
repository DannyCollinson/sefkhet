"""Logfmt formatting utilities for `sefkhet`."""

import logging as _logging
from typing import TYPE_CHECKING as _TYPE_CHECKING


if _TYPE_CHECKING:  # pragma: no cover
    import logging
    from collections.abc import Mapping
    from typing import Any, Literal

    from sefkhet._typing import _FormatStyle, _LogfmtSpec


# Define fields to include for a default logfmt formatter
_DEFAULT_LOGFMT_FIELDS: tuple[str, ...] = (
    "timestamp",
    "level",
    "levelno",
    "message",
    "logger",
)


def _parse_logfmt_spec(
    spec: "Literal[True] | _LogfmtSpec",
) -> "tuple[tuple[str, ...], bool]":
    """
    Returns the result of parsing a logfmt spec
    into resolved configuration values.

    Args:
        spec (Literal[True] | _LogfmtSpec): Either `True`
            for defaults or a `_LogfmtSpec` dict with
            optional keys `fields` and `sort_keys`.

    Returns:
        tuple[tuple[str, ...], bool]: A tuple of
            `(fields, sort_keys)`
    """
    # Handle boolean case
    if isinstance(spec, bool):
        return _DEFAULT_LOGFMT_FIELDS, False
    # Use values from spec if given, otherwise use defaults
    fields = tuple(spec.get("fields", _DEFAULT_LOGFMT_FIELDS))
    sort_keys = spec.get("sort_keys", False)
    return fields, sort_keys


def _format_logfmt_value(value: object) -> str:
    """
    Converts a value to its logfmt representation.

    Quotes if the value contains spaces, equals signs,
    double quotes, or newlines. Escapes backslashes,
    double quotes, and newlines inside quoted values.
    Empty strings are represented as `""`.

    Args:
        value (object): The value to format

    Returns:
        str: The logfmt-formatted value string
    """
    s = str(value)
    if not s:
        return '""'
    needs_quote = " " in s or "=" in s or '"' in s or "\n" in s
    if needs_quote:
        escaped = s.replace("\\", "\\\\")
        escaped = escaped.replace('"', '\\"')
        escaped = escaped.replace("\n", "\\n")
        return f'"{escaped}"'
    return s


class LogfmtFormatter(_logging.Formatter):
    """
    A `logging.Formatter` subclass that outputs log records
    as logfmt key=value pairs.

    Each log line contains space-separated `key=value` pairs
    with configurable fields. Extra attributes passed via
    `extra={...}` are automatically included. Exception and
    stack info are serialised as strings when present.
    """

    def __init__(  # ruff: ignore[too-many-arguments]
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: "_FormatStyle" = "%",
        *,
        validate: bool = True,
        defaults: "Mapping[str, Any] | None" = None,
        logfmt: "Literal[True] | _LogfmtSpec",
    ) -> None:
        """
        A `logging.Formatter` subclass that outputs log
        records as logfmt key=value pairs.

        Each log line contains space-separated `key=value`
        pairs with configurable fields. Extra attributes
        passed via `extra={...}` are automatically included.
        Exception and stack info are serialised as strings
        when present.

        Args:
            fmt (str | None, optional): Format string
                (unused in logfmt output but accepted for
                interface compatibility).
                Defaults to `None`.
            datefmt (str | None, optional): Date format
                string used by `formatTime`.
                Defaults to `None`.
            style (_FormatStyle, optional): Format style.
                Defaults to `"%"`.
            validate (bool, optional): If `True`, validates
                the format string. Defaults to `True`.
            defaults (Mapping[str, Any] | None, optional):
                Default values for string interpolation.
                Defaults to `None`.
            logfmt (Literal[True] | _LogfmtSpec): Logfmt
                configuration. `True` for defaults, or a
                `_LogfmtSpec` dict with optional keys
                `fields` and `sort_keys`.
        """
        super().__init__(
            fmt=fmt,
            datefmt=datefmt,
            style=style,
            validate=validate,
            defaults=defaults,
        )

        # Parse the logfmt-specific options
        (self._logfmt_fields, self._logfmt_sort_keys) = _parse_logfmt_spec(
            logfmt
        )

    def format(self, record: "logging.LogRecord") -> str:
        """
        Formats the log record as a logfmt string.

        Args:
            record (logging.LogRecord): Log record to
                format

        Returns:
            str: Logfmt-formatted log record string
        """
        from sefkhet._constants import (
            _KNOWN_FIELDS,
            _STANDARD_RECORD_ATTRS,
            _extract_known_field,
        )

        pairs: list[str] = []

        # Build pairs from configured fields
        for field in self._logfmt_fields:
            if field in _KNOWN_FIELDS:
                val = _extract_known_field(field, record, self)
            else:
                val = getattr(record, field, None)
            pairs.append(f"{field}={_format_logfmt_value(val)}")

        # Handle exc_info
        if record.exc_info and record.exc_info[0] is not None:
            pairs.append(
                "exc_info="
                + _format_logfmt_value(self.formatException(record.exc_info))
            )

        # Handle stack_info
        if record.stack_info:
            pairs.append(
                "stack_info="
                + _format_logfmt_value(self.formatStack(record.stack_info))
            )

        # Append extra fields
        existing_fields = set(self._logfmt_fields) | _STANDARD_RECORD_ATTRS
        existing_fields.add("exc_info")
        existing_fields.add("stack_info")
        extras = {
            k: v for k, v in record.__dict__.items() if k not in existing_fields
        }

        # Sort extra keys if requested
        if self._logfmt_sort_keys:
            extras = dict(sorted(extras.items()))

        for k, v in extras.items():
            pairs.append(f"{k}={_format_logfmt_value(v)}")

        return " ".join(pairs)
