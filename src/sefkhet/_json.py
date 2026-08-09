"""JSON formatting utilities for `sefkhet`."""

import logging as _logging
from typing import TYPE_CHECKING as _TYPE_CHECKING


if _TYPE_CHECKING:  # pragma: no cover
    import logging
    from collections.abc import Mapping
    from typing import Any, Literal

    from sefkhet._typing import _FormatStyle, _JsonSpec


# Define fields to include for a default JSON formatter
_DEFAULT_JSON_FIELDS: tuple[str, ...] = (
    "timestamp",
    "level",
    "levelno",
    "message",
    "logger",
)


def _parse_json_spec(
    spec: "Literal[True] | _JsonSpec",
) -> "tuple[tuple[str, ...], int | None, bool, bool]":
    """
    Returns the result of parsing a JSON spec
    into resolved configuration values.

    Args:
        spec (Literal[True] | _JsonSpec): Either `True` for defaults or
            a `_JsonSpec` dict with optional keys `fields`, `indent`,
            `ensure_ascii`, and `sort_keys`.

    Returns:
        tuple[tuple[str, ...], int | None, bool, bool]: A tuple of
            `(fields, indent, ensure_ascii, sort_keys)`
    """
    # Handle boolean case
    if isinstance(spec, bool):
        return _DEFAULT_JSON_FIELDS, None, False, False
    # Use values from spec if given, otherwise use defaults
    fields = tuple(spec.get("fields", _DEFAULT_JSON_FIELDS))
    indent = spec.get("indent", None)
    ensure_ascii = spec.get("ensure_ascii", False)
    sort_keys = spec.get("sort_keys", False)
    return fields, indent, ensure_ascii, sort_keys


class JsonFormatter(_logging.Formatter):
    """
    A `logging.Formatter` subclass that outputs log records
    as JSON objects.

    Each log line is a single JSON object with configurable
    fields. Extra attributes passed via `extra={...}` are
    automatically included. Exception and stack info are
    serialised as strings when present.
    """

    def __init__(  # ruff: ignore[too-many-arguments]
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: "_FormatStyle" = "%",
        *,
        validate: bool = True,
        defaults: "Mapping[str, Any] | None" = None,
        json: "Literal[True] | _JsonSpec",
    ) -> None:
        """
        A `logging.Formatter` subclass that outputs log records
        as JSON objects.

        Each log line is a single JSON object with configurable
        fields. Extra attributes passed via `extra={...}` are
        automatically included. Exception and stack info are
        serialised as strings when present.

        Args:
            fmt (str | None, optional): Format string (unused in
                JSON output but accepted for interface
                compatibility). Defaults to `None`.
            datefmt (str | None, optional): Date format string
                used by `formatTime`. Defaults to `None`.
            style (_FormatStyle, optional): Format style.
                Defaults to `"%"`.
            validate (bool, optional): If `True`, validates the
                format string. Defaults to `True`.
            defaults (Mapping[str, Any] | None, optional): Default
                values for string interpolation.
                Defaults to `None`.
            json (Literal[True] | _JsonSpec): JSON configuration. `True`
                for defaults, or a `_JsonSpec` dict with optional
                keys `fields`, `indent`, `ensure_ascii`, and
                `sort_keys`.
        """
        super().__init__(
            fmt=fmt,
            datefmt=datefmt,
            style=style,
            validate=validate,
            defaults=defaults,
        )

        # Parse the JSON-specific options
        (
            self._json_fields,
            self._json_indent,
            self._json_ensure_ascii,
            self._json_sort_keys,
        ) = _parse_json_spec(json)

    def format(self, record: "logging.LogRecord") -> str:
        """
        Formats the log record as a JSON string.

        Args:
            record (logging.LogRecord): Log record to format

        Returns:
            str: JSON-formatted log record string
        """
        import json

        from sefkhet._constants import (
            _KNOWN_FIELDS,
            _STANDARD_RECORD_ATTRS,
            _extract_known_field,
        )

        data: dict[str, object] = {}

        # Build dict from configured fields
        for field in self._json_fields:
            if field in _KNOWN_FIELDS:
                data[field] = _extract_known_field(field, record, self)
            else:
                data[field] = getattr(record, field, None)

        # Handle exc_info
        if record.exc_info and record.exc_info[0] is not None:
            data["exc_info"] = self.formatException(record.exc_info)

        # Handle stack_info
        if record.stack_info:
            data["stack_info"] = self.formatStack(record.stack_info)

        # Append extra fields
        existing_fields = set(data.keys()) | _STANDARD_RECORD_ATTRS
        data.update(
            {
                k: v
                for k, v in record.__dict__.items()
                if k not in existing_fields
            }
        )

        # Return using json library for auto-formatting
        return json.dumps(
            data,
            indent=self._json_indent,
            ensure_ascii=self._json_ensure_ascii,
            sort_keys=self._json_sort_keys,
            default=str,
        )
