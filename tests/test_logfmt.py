"""Tests for `snaplog._logfmt`."""

import logging

import snaplog._one_step as _one_step_module
from snaplog._color import ColorFormatter
from snaplog._csv import CsvFormatter
from snaplog._functional import get_formatter, get_logger
from snaplog._json import JsonFormatter
from snaplog._logfmt import (
    _DEFAULT_LOGFMT_FIELDS,
    LogfmtFormatter,
    _format_logfmt_value,
    _parse_logfmt_spec,
)
from snaplog._object_oriented import SnapLogger
from snaplog._one_step import configure_default_logger
from snaplog._typing import _HandlerKwargs


def _make_record(
    msg: str = "hello",
    level: int = logging.INFO,
    args: tuple[object, ...] | None = None,
    name: str = "test",
) -> logging.LogRecord:
    """
    Create a minimal LogRecord for testing.

    Args:
        msg (str, optional): Log message.
            Defaults to `"hello"`.
        level (int, optional): Log level.
            Defaults to `logging.INFO`.
        args (tuple[object, ...] | None, optional): Format
            args. Defaults to `None`.
        name (str, optional): Logger name.
            Defaults to `"test"`.

    Returns:
        logging.LogRecord: A minimal log record for testing
    """
    return logging.LogRecord(
        name=name,
        level=level,
        pathname="test_logfmt.py",
        lineno=42,
        msg=msg,
        args=args,
        exc_info=None,
    )


class TestParseLogfmtSpec:
    """Tests for `_parse_logfmt_spec`."""

    @staticmethod
    def test_true_returns_defaults() -> None:
        """Passing `True` returns default config."""
        fields, sort_keys = _parse_logfmt_spec(spec=True)
        assert fields == _DEFAULT_LOGFMT_FIELDS
        assert sort_keys is False

    @staticmethod
    def test_custom_fields() -> None:
        """Custom fields are returned as a tuple."""
        fields, _ = _parse_logfmt_spec({"fields": ["level", "message"]})
        assert fields == ("level", "message")

    @staticmethod
    def test_sort_keys() -> None:
        """Custom sort_keys is returned."""
        _, sort_keys = _parse_logfmt_spec({"sort_keys": True})
        assert sort_keys is True

    @staticmethod
    def test_empty_dict_returns_defaults() -> None:
        """An empty dict returns defaults."""
        fields, sort_keys = _parse_logfmt_spec({})
        assert fields == _DEFAULT_LOGFMT_FIELDS
        assert sort_keys is False


class TestFormatLogfmtValue:
    """Tests for `_format_logfmt_value`."""

    @staticmethod
    def test_plain_string() -> None:
        """Plain string without special chars."""
        assert _format_logfmt_value("hello") == "hello"

    @staticmethod
    def test_spaces_trigger_quoting() -> None:
        """Spaces trigger quoting."""
        result = _format_logfmt_value("hello world")
        assert result == '"hello world"'

    @staticmethod
    def test_equals_sign_triggers_quoting() -> None:
        """Equals sign triggers quoting."""
        result = _format_logfmt_value("a=b")
        assert result == '"a=b"'

    @staticmethod
    def test_quotes_are_escaped() -> None:
        """Double quotes inside value are escaped."""
        result = _format_logfmt_value('say "hi"')
        assert result == '"say \\"hi\\""'

    @staticmethod
    def test_newlines_escaped() -> None:
        """Newlines are escaped."""
        result = _format_logfmt_value("line1\nline2")
        assert result == '"line1\\nline2"'

    @staticmethod
    def test_none_handling() -> None:
        """None is converted to string."""
        assert _format_logfmt_value(None) == "None"

    @staticmethod
    def test_numeric_values() -> None:
        """Numeric values are stringified."""
        assert _format_logfmt_value(42) == "42"
        assert _format_logfmt_value(2.72) == "2.72"

    @staticmethod
    def test_empty_string() -> None:
        """Empty string is represented as double quotes."""
        assert _format_logfmt_value("") == '""'


class TestLogfmtFormatter:
    """Tests for `LogfmtFormatter`."""

    @staticmethod
    def test_default_fields_present() -> None:
        """Default fields are present in output."""
        fmt = LogfmtFormatter(logfmt=True)
        record = _make_record()
        result = fmt.format(record)
        for field in _DEFAULT_LOGFMT_FIELDS:
            assert f"{field}=" in result

    @staticmethod
    def test_output_format_validation() -> None:
        """Output matches key=value key=value pattern."""
        import re

        fmt = LogfmtFormatter(logfmt=True)
        record = _make_record()
        result = fmt.format(record)
        # Should match key=value pairs (values may be quoted)
        pattern = r'\w+=(?:"[^"]*"|[^ ]*)'
        matches = re.findall(pattern, result)
        assert len(matches) >= len(_DEFAULT_LOGFMT_FIELDS)

    @staticmethod
    def test_message_field_value() -> None:
        """Message field contains the log message."""
        fmt = LogfmtFormatter(logfmt={"fields": ["message"]})
        record = _make_record(msg="simple")
        result = fmt.format(record)
        assert result == "message=simple"

    @staticmethod
    def test_level_field_value() -> None:
        """Level field contains the level name."""
        fmt = LogfmtFormatter(logfmt={"fields": ["level"]})
        record = _make_record(level=logging.WARNING)
        result = fmt.format(record)
        assert result == "level=WARNING"

    @staticmethod
    def test_levelno_field_value() -> None:
        """Levelno field contains the integer level."""
        fmt = LogfmtFormatter(logfmt={"fields": ["levelno"]})
        record = _make_record(level=logging.ERROR)
        result = fmt.format(record)
        assert result == f"levelno={logging.ERROR}"

    @staticmethod
    def test_logger_field_value() -> None:
        """Logger field contains the logger name."""
        fmt = LogfmtFormatter(logfmt={"fields": ["logger"]})
        record = _make_record(name="mylogger")
        result = fmt.format(record)
        assert result == "logger=mylogger"

    @staticmethod
    def test_timestamp_field_present() -> None:
        """Timestamp field is a non-empty string."""
        fmt = LogfmtFormatter(logfmt={"fields": ["timestamp"]})
        record = _make_record()
        result = fmt.format(record)
        assert result.startswith("timestamp=")
        assert len(result) > len("timestamp=")

    @staticmethod
    def test_custom_fields_selection() -> None:
        """Custom fields selection only includes chosen."""
        fmt = LogfmtFormatter(logfmt={"fields": ["level", "message"]})
        record = _make_record()
        result = fmt.format(record)
        assert "level=" in result
        assert "message=" in result
        assert "timestamp=" not in result
        assert "logger=" not in result

    @staticmethod
    def test_extra_fields_included() -> None:
        """Extra fields via extra={} are included."""
        fmt = LogfmtFormatter(logfmt={"fields": ["message"]})
        record = _make_record()
        record.user = "alice"
        result = fmt.format(record)
        assert "user=alice" in result

    @staticmethod
    def test_exc_info_serialized() -> None:
        """exc_info is serialized when present."""  # noqa: DOC501
        fmt = LogfmtFormatter(logfmt={"fields": ["message"]})
        try:
            msg = "boom"
            raise ValueError(msg)  # noqa: TRY301
        except ValueError:
            import sys

            record = _make_record()
            record.exc_info = sys.exc_info()
        result = fmt.format(record)
        assert "exc_info=" in result
        assert "ValueError" in result

    @staticmethod
    def test_stack_info_serialized() -> None:
        """stack_info is serialized when present."""
        fmt = LogfmtFormatter(logfmt={"fields": ["message"]})
        record = _make_record()
        record.stack_info = "Stack trace here"
        result = fmt.format(record)
        assert "stack_info=" in result

    @staticmethod
    def test_unknown_field_getattr_fallback() -> None:
        """Unknown field name falls back to getattr."""
        fmt = LogfmtFormatter(logfmt={"fields": ["nonexistent_field"]})
        record = _make_record()
        result = fmt.format(record)
        assert result == "nonexistent_field=None"

    @staticmethod
    def test_datefmt_respected() -> None:
        """Custom datefmt is used in timestamp."""
        fmt = LogfmtFormatter(datefmt="%Y", logfmt={"fields": ["timestamp"]})
        record = _make_record()
        result = fmt.format(record)
        # Should be timestamp=YYYY
        val = result.split("=", 1)[1]
        assert len(val) == 4
        assert val.isdigit()

    @staticmethod
    def test_message_with_percent_args() -> None:
        """%-style args are interpolated in message."""
        fmt = LogfmtFormatter(logfmt={"fields": ["message"]})
        record = _make_record(msg="count=%d", args=(5,))
        result = fmt.format(record)
        assert "count=5" in result

    @staticmethod
    def test_known_field_module() -> None:
        """Module field is extracted correctly."""
        fmt = LogfmtFormatter(logfmt={"fields": ["module"]})
        record = _make_record()
        result = fmt.format(record)
        assert "module=" in result

    @staticmethod
    def test_known_field_func_name() -> None:
        """FuncName field is extracted correctly."""
        fmt = LogfmtFormatter(logfmt={"fields": ["funcName"]})
        record = _make_record()
        result = fmt.format(record)
        assert "funcName=" in result

    @staticmethod
    def test_known_field_lineno() -> None:
        """Lineno field is extracted correctly."""
        fmt = LogfmtFormatter(logfmt={"fields": ["lineno"]})
        record = _make_record()
        result = fmt.format(record)
        assert result == "lineno=42"

    @staticmethod
    def test_known_field_pathname() -> None:
        """Pathname field is extracted correctly."""
        fmt = LogfmtFormatter(logfmt={"fields": ["pathname"]})
        record = _make_record()
        result = fmt.format(record)
        assert result == "pathname=test_logfmt.py"

    @staticmethod
    def test_sort_keys_option() -> None:
        """sort_keys sorts extra keys alphabetically."""
        fmt = LogfmtFormatter(logfmt={"fields": ["message"], "sort_keys": True})
        record = _make_record(msg="hi")
        record.zebra = "z"
        record.alpha = "a"
        result = fmt.format(record)
        parts = result.split(" ")
        # First part is message=hi, then extras
        extra_keys = [p.split("=")[0] for p in parts[1:]]
        assert extra_keys == sorted(extra_keys)

    @staticmethod
    def test_no_side_effects_across_calls() -> None:
        """Formatting same record twice gives same result."""
        fmt = LogfmtFormatter(logfmt=True)
        record = _make_record()
        r1 = fmt.format(record)
        r2 = fmt.format(record)
        assert r1 == r2


class TestLogfmtIntegration:
    """Tests for logfmt integration with functional API."""

    @staticmethod
    def test_get_formatter_logfmt_true_returns_logfmt() -> None:
        """`get_formatter(logfmt=True)` returns LogfmtFormatter."""
        fmt = get_formatter(logfmt=True)
        assert isinstance(fmt, LogfmtFormatter)

    @staticmethod
    def test_logfmt_overrides_color() -> None:
        """Logfmt wins over color silently."""
        fmt = get_formatter(logfmt=True, color="full")
        assert isinstance(fmt, LogfmtFormatter)

    @staticmethod
    def test_json_overrides_logfmt() -> None:
        """JSON wins over logfmt."""
        fmt = get_formatter(json=True, logfmt=True)
        assert isinstance(fmt, JsonFormatter)

    @staticmethod
    def test_csv_overrides_logfmt() -> None:
        """CSV wins over logfmt."""
        fmt = get_formatter(csv=True, logfmt=True)
        assert isinstance(fmt, CsvFormatter)

    @staticmethod
    def test_logfmt_false_falls_through() -> None:
        """`logfmt=False` falls back to color."""
        fmt = get_formatter(logfmt=False)
        assert isinstance(fmt, ColorFormatter)

    @staticmethod
    def test_logfmt_spec_dict() -> None:
        """Dict spec creates LogfmtFormatter."""
        fmt = get_formatter(logfmt={"fields": ["level", "message"]})
        assert isinstance(fmt, LogfmtFormatter)

    @staticmethod
    def test_get_logger_logfmt_true() -> None:
        """get_logger(logfmt=True) adds LogfmtFormatter."""
        logger = get_logger(name="test_logfmt_gl", handlers="null", logfmt=True)
        assert len(logger.handlers) >= 1
        assert isinstance(logger.handlers[-1].formatter, LogfmtFormatter)

    @staticmethod
    def test_snap_logger_logfmt_true() -> None:
        """SnapLogger(logfmt=True) adds LogfmtFormatter."""
        snap = SnapLogger(name="test_logfmt_sl", logfmt=True)
        assert len(snap.handlers) >= 1
        assert isinstance(snap.handlers[-1].formatter, LogfmtFormatter)

    @staticmethod
    def test_configure_default_logger_logfmt_true() -> None:
        """configure_default_logger(logfmt=True) uses logfmt."""
        configure_default_logger(logfmt=True)
        logger = _one_step_module._default_logger
        assert logger is not None
        assert len(logger.handlers) >= 1
        assert isinstance(logger.handlers[-1].formatter, LogfmtFormatter)

    @staticmethod
    def test_logfmt_formatter_exported() -> None:
        """LogfmtFormatter is accessible from snaplog."""
        import snaplog

        assert hasattr(snaplog, "LogfmtFormatter")
        assert snaplog.LogfmtFormatter is LogfmtFormatter


class TestLogfmtFormatterEndToEnd:
    """End-to-end tests with actual logging."""

    @staticmethod
    def test_log_output_is_logfmt() -> None:
        """Logged output through handler is logfmt."""
        import io

        stream = io.StringIO()
        snap = SnapLogger(
            name="test_logfmt_e2e",
            level=logging.DEBUG,
            handlers=(
                logging.StreamHandler(stream),
                _HandlerKwargs({"level": logging.DEBUG}),
            ),
            formatter="%(message)s",
            logfmt=True,
        )
        snap.info("hello logfmt")
        output = stream.getvalue().strip()
        assert "message=" in output
        assert "level=INFO" in output

    @staticmethod
    def test_message_with_spaces_properly_quoted() -> None:
        """Message with spaces is properly quoted."""
        fmt = LogfmtFormatter(logfmt={"fields": ["message"]})
        record = _make_record(msg="hello world")
        result = fmt.format(record)
        assert result == 'message="hello world"'
