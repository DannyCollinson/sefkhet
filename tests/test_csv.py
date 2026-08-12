"""Tests for `sefkhet._csv`."""

import csv
import logging

import sefkhet._one_step as _one_step_module
from sefkhet._color import ColorFormatter
from sefkhet._csv import _DEFAULT_CSV_FIELDS, CsvFormatter, _parse_csv_spec
from sefkhet._functional import get_formatter, get_logger
from sefkhet._json import JsonFormatter
from sefkhet._object_oriented import Scribe
from sefkhet._one_step import configure_default_logger
from sefkhet._typing import HandlerOpts


def _make_record(
    msg: str = "hello",
    level: int = logging.INFO,
    args: tuple[object, ...] | None = None,
    name: str = "test",
) -> logging.LogRecord:
    """
    Create a minimal LogRecord for testing.

    Args:
        msg (str, default="hello"): Log message.
            Defaults to `"hello"`.
        level (int, default=logging.INFO): Log level.
            Defaults to `logging.INFO`.
        args (tuple[object, ...] | None, default=None): Format
            args. Defaults to `None`.
        name (str, default="test"): Logger name.
            Defaults to `"test"`.

    Returns:
        logging.LogRecord: A minimal log record for testing
    """
    return logging.LogRecord(
        name=name,
        level=level,
        pathname="test_csv.py",
        lineno=42,
        msg=msg,
        args=args,
        exc_info=None,
    )


class TestParseCsvSpec:
    """Tests for `_parse_csv_spec`."""

    @staticmethod
    def test_true_returns_defaults() -> None:
        """Passing `True` returns default config."""
        fields, delimiter, quoting, header = _parse_csv_spec(spec=True)
        assert fields == _DEFAULT_CSV_FIELDS
        assert delimiter == ","
        assert quoting == csv.QUOTE_MINIMAL
        assert header is False

    @staticmethod
    def test_custom_fields() -> None:
        """Custom fields are returned as a tuple."""
        fields, _, _, _ = _parse_csv_spec({"fields": ["level", "message"]})
        assert fields == ("level", "message")

    @staticmethod
    def test_custom_delimiter() -> None:
        """Custom delimiter is returned."""
        _, delimiter, _, _ = _parse_csv_spec({"delimiter": "\t"})
        assert delimiter == "\t"

    @staticmethod
    def test_custom_quoting() -> None:
        """Custom quoting is returned."""
        _, _, quoting, _ = _parse_csv_spec({"quoting": csv.QUOTE_ALL})
        assert quoting == csv.QUOTE_ALL

    @staticmethod
    def test_custom_header() -> None:
        """Custom header is returned."""
        _, _, _, header = _parse_csv_spec({"header": True})
        assert header is True

    @staticmethod
    def test_empty_dict_returns_defaults() -> None:
        """An empty dict returns defaults."""
        fields, delimiter, quoting, header = _parse_csv_spec({})
        assert fields == _DEFAULT_CSV_FIELDS
        assert delimiter == ","
        assert quoting == csv.QUOTE_MINIMAL
        assert header is False


class TestCsvFormatter:  # ruff: ignore[too-many-public-methods]
    """Tests for `CsvFormatter`."""

    @staticmethod
    def test_default_fields_present() -> None:
        """Default fields produce correct column count."""
        fmt = CsvFormatter(csv=True)
        record = _make_record()
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        assert len(parts) >= len(_DEFAULT_CSV_FIELDS)

    @staticmethod
    def test_output_is_valid_csv() -> None:
        """Output is valid CSV."""
        fmt = CsvFormatter(csv=True)
        record = _make_record()
        result = fmt.format(record)
        rows = list(csv.reader([result]))
        assert len(rows) == 1

    @staticmethod
    def test_message_field_value() -> None:
        """Message field contains the log message."""
        fmt = CsvFormatter(csv={"fields": ["message"]})
        record = _make_record(msg="test message")
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        assert parts[0] == "test message"

    @staticmethod
    def test_level_field_value() -> None:
        """Level field contains the level name."""
        fmt = CsvFormatter(csv={"fields": ["level"]})
        record = _make_record(level=logging.WARNING)
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        assert parts[0] == "WARNING"

    @staticmethod
    def test_levelno_field_value() -> None:
        """Levelno field contains the integer level."""
        fmt = CsvFormatter(csv={"fields": ["levelno"]})
        record = _make_record(level=logging.ERROR)
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        assert parts[0] == str(logging.ERROR)

    @staticmethod
    def test_logger_field_value() -> None:
        """Logger field contains the logger name."""
        fmt = CsvFormatter(csv={"fields": ["logger"]})
        record = _make_record(name="mylogger")
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        assert parts[0] == "mylogger"

    @staticmethod
    def test_timestamp_field_present() -> None:
        """Timestamp field is a non-empty string."""
        fmt = CsvFormatter(csv={"fields": ["timestamp"]})
        record = _make_record()
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        assert len(parts[0]) > 0

    @staticmethod
    def test_custom_fields_selection() -> None:
        """Custom fields selection only includes chosen."""
        fmt = CsvFormatter(csv={"fields": ["level", "message"]})
        record = _make_record()
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        assert len(parts) == 2

    @staticmethod
    def test_custom_delimiter() -> None:
        """Custom delimiter is used in output."""
        fmt = CsvFormatter(
            csv={"fields": ["level", "message"], "delimiter": "\t"}
        )
        record = _make_record(msg="hi")
        result = fmt.format(record)
        parts = result.split("\t")
        assert len(parts) == 2

    @staticmethod
    def test_quoting_all() -> None:
        """QUOTE_ALL quotes every field."""
        fmt = CsvFormatter(
            csv={"fields": ["message"], "quoting": csv.QUOTE_ALL}
        )
        record = _make_record(msg="hi")
        result = fmt.format(record)
        assert result == '"hi"'

    @staticmethod
    def test_header_first_call() -> None:
        """Header row is emitted on first call."""
        fmt = CsvFormatter(csv={"fields": ["level", "message"], "header": True})
        record = _make_record(msg="hi")
        result = fmt.format(record)
        lines = result.split("\n")
        assert len(lines) == 2
        header_parts = next(csv.reader([lines[0]]))
        assert header_parts == ["level", "message"]

    @staticmethod
    def test_header_only_first_call() -> None:
        """Header row is only emitted on the first call."""
        fmt = CsvFormatter(csv={"fields": ["level", "message"], "header": True})
        record = _make_record(msg="hi")
        fmt.format(record)
        result2 = fmt.format(record)
        lines = result2.split("\n")
        assert len(lines) == 1

    @staticmethod
    def test_header_includes_exc_info_column() -> None:
        """Header gains an exc_info column when the record has one."""  # ruff: ignore[docstring-missing-exception]
        fmt = CsvFormatter(csv={"fields": ["message"], "header": True})
        try:
            msg = "boom"
            raise ValueError(msg)  # ruff: ignore[raise-within-try]
        except ValueError:
            import sys

            record = _make_record()
            record.exc_info = sys.exc_info()
        result = fmt.format(record)
        lines = result.split("\n")
        header_parts = next(csv.reader([lines[0]]))
        assert header_parts == ["message", "exc_info"]

    @staticmethod
    def test_header_includes_stack_info_column() -> None:
        """Header gains a stack_info column when the record has one."""
        fmt = CsvFormatter(csv={"fields": ["message"], "header": True})
        record = _make_record()
        record.stack_info = "Stack trace here"
        result = fmt.format(record)
        lines = result.split("\n")
        header_parts = next(csv.reader([lines[0]]))
        assert header_parts == ["message", "stack_info"]

    @staticmethod
    def test_header_omits_exc_and_stack_columns_when_absent() -> None:
        """Header omits exc_info/stack_info for a plain record."""
        fmt = CsvFormatter(csv={"fields": ["message"], "header": True})
        result = fmt.format(_make_record())
        lines = result.split("\n")
        header_parts = next(csv.reader([lines[0]]))
        assert header_parts == ["message"]

    @staticmethod
    def test_extra_fields_included() -> None:
        """Extra fields via extra={} are included."""
        fmt = CsvFormatter(csv={"fields": ["message"]})
        record = _make_record()
        record.user = "alice"
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        assert "alice" in parts

    @staticmethod
    def test_exc_info_serialized() -> None:
        """exc_info is serialized when present."""  # ruff: ignore[docstring-missing-exception]
        fmt = CsvFormatter(csv={"fields": ["message"]})
        try:
            msg = "boom"
            raise ValueError(msg)  # ruff: ignore[raise-within-try]
        except ValueError:
            import sys

            record = _make_record()
            record.exc_info = sys.exc_info()
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        assert any("ValueError" in p for p in parts)

    @staticmethod
    def test_exc_info_absent_when_none() -> None:
        """No extra exc_info column when no exception."""
        fmt = CsvFormatter(csv={"fields": ["message"]})
        record = _make_record()
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        # Only the message field, no extras
        assert len(parts) == 1

    @staticmethod
    def test_stack_info_serialized() -> None:
        """stack_info is serialized when present."""
        fmt = CsvFormatter(csv={"fields": ["message"]})
        record = _make_record()
        record.stack_info = "Stack trace here"
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        assert "Stack trace here" in parts

    @staticmethod
    def test_stack_info_absent_when_none() -> None:
        """No extra stack_info column when not set."""
        fmt = CsvFormatter(csv={"fields": ["message"]})
        record = _make_record()
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        assert len(parts) == 1

    @staticmethod
    def test_unknown_field_getattr_fallback() -> None:
        """Unknown field name falls back to getattr."""
        fmt = CsvFormatter(csv={"fields": ["nonexistent_field"]})
        record = _make_record()
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        assert parts[0] == "None"

    @staticmethod
    def test_non_serializable_uses_str() -> None:
        """Non-serializable values use str()."""
        fmt = CsvFormatter(csv={"fields": ["message"]})
        record = _make_record()
        record.custom_obj = object()
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        # The extra field should be stringified
        assert len(parts) == 2
        assert parts[1].startswith("<object object at")

    @staticmethod
    def test_datefmt_respected() -> None:
        """Custom datefmt is used in timestamp."""
        fmt = CsvFormatter(datefmt="%Y", csv={"fields": ["timestamp"]})
        record = _make_record()
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        assert len(parts[0]) == 4
        assert parts[0].isdigit()

    @staticmethod
    def test_message_with_percent_args() -> None:
        """%-style args are interpolated in message."""
        fmt = CsvFormatter(csv={"fields": ["message"]})
        record = _make_record(msg="count=%d", args=(5,))
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        assert parts[0] == "count=5"

    @staticmethod
    def test_known_field_module() -> None:
        """Module field is extracted correctly."""
        fmt = CsvFormatter(csv={"fields": ["module"]})
        record = _make_record()
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        assert len(parts[0]) > 0

    @staticmethod
    def test_known_field_func_name() -> None:
        """FuncName field is extracted correctly."""
        fmt = CsvFormatter(csv={"fields": ["funcName"]})
        record = _make_record()
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        assert len(parts) >= 1

    @staticmethod
    def test_known_field_lineno() -> None:
        """Lineno field is extracted correctly."""
        fmt = CsvFormatter(csv={"fields": ["lineno"]})
        record = _make_record()
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        assert parts[0] == "42"

    @staticmethod
    def test_known_field_pathname() -> None:
        """Pathname field is extracted correctly."""
        fmt = CsvFormatter(csv={"fields": ["pathname"]})
        record = _make_record()
        result = fmt.format(record)
        parts = next(csv.reader([result]))
        assert parts[0] == "test_csv.py"

    @staticmethod
    def test_no_side_effects_across_calls() -> None:
        """Formatting same record twice gives same result."""
        fmt = CsvFormatter(csv=True)
        record = _make_record()
        r1 = fmt.format(record)
        r2 = fmt.format(record)
        assert r1 == r2


class TestCsvIntegration:
    """Tests for CSV integration with functional API."""

    @staticmethod
    def test_get_formatter_csv_true_returns_csv() -> None:
        """`get_formatter(csv=True)` returns CsvFormatter."""
        fmt = get_formatter(csv=True)
        assert isinstance(fmt, CsvFormatter)

    @staticmethod
    def test_get_formatter_csv_overrides_json() -> None:
        """CSV wins over JSON silently."""
        fmt = get_formatter(csv=True, json=True)
        assert isinstance(fmt, CsvFormatter)

    @staticmethod
    def test_get_formatter_csv_overrides_color() -> None:
        """CSV wins over color silently."""
        fmt = get_formatter(csv=True, color="full")
        assert isinstance(fmt, CsvFormatter)

    @staticmethod
    def test_get_formatter_csv_false_uses_json() -> None:
        """`csv=False` falls back to JSON if set."""
        fmt = get_formatter(csv=False, json=True)
        assert isinstance(fmt, JsonFormatter)

    @staticmethod
    def test_get_formatter_csv_false_uses_color() -> None:
        """`csv=False, json=False` falls back to color."""
        fmt = get_formatter(csv=False, json=False)
        assert isinstance(fmt, ColorFormatter)

    @staticmethod
    def test_get_formatter_csv_spec_dict() -> None:
        """Dict spec creates CsvFormatter with config."""
        fmt = get_formatter(
            csv={"fields": ["level", "message"], "delimiter": "\t"}
        )
        assert isinstance(fmt, CsvFormatter)

    @staticmethod
    def test_get_logger_csv_true() -> None:
        """get_logger(csv=True) adds CsvFormatter."""
        logger = get_logger(name="test_csv_gl", handlers="null", csv=True)
        assert len(logger.handlers) >= 1
        assert isinstance(logger.handlers[-1].formatter, CsvFormatter)

    @staticmethod
    def test_scribe_csv_true() -> None:
        """Scribe(csv=True) adds CsvFormatter."""
        scribe = Scribe(name="test_csv_sl", csv=True)
        assert len(scribe.handlers) >= 1
        assert isinstance(scribe.handlers[-1].formatter, CsvFormatter)

    @staticmethod
    def test_configure_default_logger_csv_true() -> None:
        """configure_default_logger(csv=True) uses CSV."""
        configure_default_logger(csv=True)
        logger = _one_step_module._default_logger
        assert logger is not None
        assert len(logger.handlers) >= 1
        assert isinstance(logger.handlers[-1].formatter, CsvFormatter)

    @staticmethod
    def test_csv_formatter_exported() -> None:
        """CsvFormatter is accessible from sefkhet."""
        import sefkhet

        assert hasattr(sefkhet, "CsvFormatter")
        assert sefkhet.CsvFormatter is CsvFormatter


class TestCsvFormatterEndToEnd:
    """End-to-end tests with actual logging."""

    @staticmethod
    def test_log_output_is_csv() -> None:
        """Logged output through a handler is valid CSV."""
        import io

        stream = io.StringIO()
        scribe = Scribe(
            name="test_csv_e2e",
            level=logging.DEBUG,
            handlers=(
                logging.StreamHandler(stream),
                HandlerOpts({"level": logging.DEBUG}),
            ),
            formatter="%(message)s",
            csv=True,
        )
        scribe.info("hello csv")
        output = stream.getvalue().strip()
        rows = list(csv.reader([output]))
        assert len(rows) == 1
        parts = rows[0]
        # message field should be present
        assert "hello csv" in parts

    @staticmethod
    def test_log_output_with_comma_in_msg() -> None:
        """Message containing comma is properly quoted."""
        import io

        stream = io.StringIO()
        scribe = Scribe(
            name="test_csv_comma",
            level=logging.DEBUG,
            handlers=(
                logging.StreamHandler(stream),
                HandlerOpts({"level": logging.DEBUG}),
            ),
            formatter="%(message)s",
            csv={"fields": ["message"]},
        )
        scribe.info("hello, world")
        output = stream.getvalue().strip()
        parts = next(csv.reader([output]))
        assert parts[0] == "hello, world"
