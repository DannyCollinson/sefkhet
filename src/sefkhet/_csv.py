"""CSV formatting utilities for `sefkhet`."""

import logging as _logging
from typing import TYPE_CHECKING as _TYPE_CHECKING


if _TYPE_CHECKING:  # pragma: no cover
    import logging
    from collections.abc import Mapping
    from typing import Any, Literal

    from sefkhet._typing import CsvSpec, FormatStyle


# Define fields to include for a default CSV formatter
_DEFAULT_CSV_FIELDS: tuple[str, ...] = (
    "timestamp",
    "level",
    "levelno",
    "message",
    "logger",
)


def _parse_csv_spec(
    spec: "Literal[True] | CsvSpec",
) -> "tuple[tuple[str, ...], str, int, bool]":
    """
    Returns the result of parsing a CSV spec
    into resolved configuration values.

    Args:
        spec (Literal[True] | CsvSpec): Either `True` for
            defaults or a `CsvSpec` dict with optional keys
            `fields`, `delimiter`, `quoting`, and `header`.

    Returns:
        tuple[tuple[str, ...], str, int, bool]: A tuple of
            `(fields, delimiter, quoting, header)`
    """
    import csv

    # Handle boolean case
    if isinstance(spec, bool):
        return _DEFAULT_CSV_FIELDS, ",", csv.QUOTE_MINIMAL, False
    # Use values from spec if given, otherwise use defaults
    fields = tuple(spec.get("fields", _DEFAULT_CSV_FIELDS))
    delimiter = spec.get("delimiter", ",")
    quoting = spec.get("quoting", csv.QUOTE_MINIMAL)
    header = spec.get("header", False)
    return fields, delimiter, quoting, header


class CsvFormatter(_logging.Formatter):
    """
    A `logging.Formatter` subclass that
    outputs log records as CSV rows.

    Each log line is a single CSV row with configurable
    fields. Extra attributes passed via `extra={...}` are
    automatically included. Exception and stack info are
    serialised as strings when present.
    """

    def __init__(  # ruff: ignore[too-many-arguments]
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: "FormatStyle" = "%",
        *,
        validate: bool = True,
        defaults: "Mapping[str, Any] | None" = None,
        csv: "Literal[True] | CsvSpec",
    ) -> None:
        """
        A `logging.Formatter` subclass that
        outputs log records as CSV rows.

        Each log line is a single CSV row with configurable
        fields. Extra attributes passed via `extra={...}` are
        automatically included. Exception and stack info are
        serialised as strings when present.

        Args:
            fmt (str | None, optional): Format string (unused
                in CSV output but accepted for interface
                compatibility). Defaults to `None`.
            datefmt (str | None, optional): Date format string
                used by `formatTime`. Defaults to `None`.
            style (FormatStyle, optional): Format style.
                Defaults to `"%"`.
            validate (bool, optional): If `True`, validates
                the format string. Defaults to `True`.
            defaults (Mapping[str, Any] | None, optional):
                Default values for string interpolation.
                Defaults to `None`.
            csv (Literal[True] | CsvSpec): CSV configuration.
                `True` for defaults, or a `CsvSpec` dict with
                optional keys `fields`, `delimiter`, `quoting`,
                and `header`.
        """
        super().__init__(
            fmt=fmt,
            datefmt=datefmt,
            style=style,
            validate=validate,
            defaults=defaults,
        )

        # Parse the CSV-specific options
        (
            self._csv_fields,
            self._csv_delimiter,
            self._csv_quoting,
            self._csv_header,
        ) = _parse_csv_spec(csv)

        # Track if the header has been written
        self._csv_header_written = False

    def format(self, record: "logging.LogRecord") -> str:
        """
        Formats the log record as a CSV string.

        Args:
            record (logging.LogRecord): Log record to format

        Returns:
            str: CSV-formatted log record string
        """
        import csv
        import io

        from sefkhet._constants import (
            _KNOWN_FIELDS,
            _STANDARD_RECORD_ATTRS,
            _extract_known_field,
        )

        values: list[str] = []

        # Build values from configured fields
        for field in self._csv_fields:
            if field in _KNOWN_FIELDS:
                val = _extract_known_field(field, record, self)
            else:
                val = getattr(record, field, None)
            values.append(str(val))

        # Handle exc_info
        if record.exc_info and record.exc_info[0] is not None:
            values.append(self.formatException(record.exc_info))

        # Handle stack_info
        if record.stack_info:
            values.append(self.formatStack(record.stack_info))

        # Append extra fields
        existing_fields = set(self._csv_fields) | _STANDARD_RECORD_ATTRS
        existing_fields.add("exc_info")
        existing_fields.add("stack_info")
        for k, v in record.__dict__.items():
            if k not in existing_fields:
                values.append(str(v))

        # Write CSV row
        output = io.StringIO()
        writer = csv.writer(
            output,
            delimiter=self._csv_delimiter,
            quoting=self._csv_quoting,  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]
        )

        # Prepend header row on first call if requested
        result_lines: list[str] = []
        if self._csv_header and not self._csv_header_written:
            header_fields = list(self._csv_fields)
            # Add extra column names for exc_info/stack_info
            if record.exc_info and record.exc_info[0] is not None:
                header_fields.append("exc_info")
            if record.stack_info:
                header_fields.append("stack_info")
            # Add any extra field columns defined by user
            extras = [k for k in record.__dict__ if k not in existing_fields]
            header_fields.extend(extras)
            # Write header to buffer
            writer.writerow(header_fields)
            # Add header to CSV output
            result_lines.append(output.getvalue().rstrip("\r\n"))
            # Reset the buffer to beginning to prepare for actual log
            output.seek(0)
            output.truncate()
            # Mark header as written
            self._csv_header_written = True

        # Write logged values to buffer
        writer.writerow(values)
        # Add log row to CSV output
        result_lines.append(output.getvalue().rstrip("\r\n"))

        # Return CSV output row with possible header above
        return "\n".join(result_lines)
