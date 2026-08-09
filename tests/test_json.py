"""Tests for `sefkhet._json`."""

import json
import logging

import sefkhet._one_step as _one_step_module
from sefkhet._color import ColorFormatter
from sefkhet._functional import get_formatter, get_logger
from sefkhet._json import _DEFAULT_JSON_FIELDS, JsonFormatter, _parse_json_spec
from sefkhet._object_oriented import Scribe
from sefkhet._one_step import configure_default_logger
from sefkhet._typing import _HandlerKwargs


def _make_record(
    msg: str = "hello",
    level: int = logging.INFO,
    args: tuple[object, ...] | None = None,
    name: str = "test",
) -> logging.LogRecord:
    """
    Create a minimal LogRecord for testing.

    Args:
        msg (str, optional): Log message. Defaults to `"hello"`.
        level (int, optional): Log level.
            Defaults to `logging.INFO`.
        args (tuple[object, ...] | None, optional): Format args.
            Defaults to `None`.
        name (str, optional): Logger name.
            Defaults to `"test"`.

    Returns:
        logging.LogRecord: A minimal log record for testing
    """
    return logging.LogRecord(
        name=name,
        level=level,
        pathname="test_json.py",
        lineno=42,
        msg=msg,
        args=args,
        exc_info=None,
    )


class TestParseJsonSpec:
    """Tests for `_parse_json_spec`."""

    @staticmethod
    def test_true_returns_defaults() -> None:
        """Passing `True` returns default config."""
        fields, indent, ensure_ascii, sort_keys = _parse_json_spec(spec=True)
        assert fields == _DEFAULT_JSON_FIELDS
        assert indent is None
        assert ensure_ascii is False
        assert sort_keys is False

    @staticmethod
    def test_custom_fields() -> None:
        """Custom fields are returned as a tuple."""
        fields, _, _, _ = _parse_json_spec({"fields": ["level", "message"]})
        assert fields == ("level", "message")

    @staticmethod
    def test_custom_indent() -> None:
        """Custom indent is returned."""
        _, indent, _, _ = _parse_json_spec({"indent": 2})
        assert indent == 2

    @staticmethod
    def test_custom_ensure_ascii() -> None:
        """Custom ensure_ascii is returned."""
        _, _, ensure_ascii, _ = _parse_json_spec({"ensure_ascii": True})
        assert ensure_ascii is True

    @staticmethod
    def test_custom_sort_keys() -> None:
        """Custom sort_keys is returned."""
        _, _, _, sort_keys = _parse_json_spec({"sort_keys": True})
        assert sort_keys is True

    @staticmethod
    def test_empty_dict_returns_defaults() -> None:
        """An empty dict returns defaults."""
        fields, indent, ensure_ascii, sort_keys = _parse_json_spec({})
        assert fields == _DEFAULT_JSON_FIELDS
        assert indent is None
        assert ensure_ascii is False
        assert sort_keys is False


class TestJsonFormatter:  # ruff: ignore[too-many-public-methods]
    """Tests for `JsonFormatter`."""

    @staticmethod
    def test_default_fields_present() -> None:
        """Default fields are present in output."""
        fmt = JsonFormatter(json=True)
        record = _make_record()
        result = json.loads(fmt.format(record))
        for field in _DEFAULT_JSON_FIELDS:
            assert field in result

    @staticmethod
    def test_output_is_valid_json() -> None:
        """Output is valid JSON."""
        fmt = JsonFormatter(json=True)
        record = _make_record()
        data = json.loads(fmt.format(record))
        assert isinstance(data, dict)

    @staticmethod
    def test_message_field_value() -> None:
        """Message field contains the log message."""
        fmt = JsonFormatter(json=True)
        record = _make_record(msg="test message")
        data = json.loads(fmt.format(record))
        assert data["message"] == "test message"

    @staticmethod
    def test_level_field_value() -> None:
        """Level field contains the level name."""
        fmt = JsonFormatter(json=True)
        record = _make_record(level=logging.WARNING)
        data = json.loads(fmt.format(record))
        assert data["level"] == "WARNING"

    @staticmethod
    def test_levelno_field_value() -> None:
        """Levelno field contains the integer level."""
        fmt = JsonFormatter(json=True)
        record = _make_record(level=logging.ERROR)
        data = json.loads(fmt.format(record))
        assert data["levelno"] == logging.ERROR

    @staticmethod
    def test_logger_field_value() -> None:
        """Logger field contains the logger name."""
        fmt = JsonFormatter(json=True)
        record = _make_record(name="mylogger")
        data = json.loads(fmt.format(record))
        assert data["logger"] == "mylogger"

    @staticmethod
    def test_timestamp_field_present() -> None:
        """Timestamp field is a non-empty string."""
        fmt = JsonFormatter(json=True)
        record = _make_record()
        data = json.loads(fmt.format(record))
        assert isinstance(data["timestamp"], str)
        assert len(data["timestamp"]) > 0

    @staticmethod
    def test_custom_fields_selection() -> None:
        """Custom fields selection only includes chosen fields."""
        fmt = JsonFormatter(json={"fields": ["level", "message"]})
        record = _make_record()
        data = json.loads(fmt.format(record))
        assert "level" in data
        assert "message" in data
        assert "timestamp" not in data
        assert "logger" not in data

    @staticmethod
    def test_indent_option() -> None:
        """Indent option produces indented output."""
        fmt = JsonFormatter(json={"indent": 2})
        record = _make_record()
        result = fmt.format(record)
        assert "\n" in result

    @staticmethod
    def test_sort_keys_option() -> None:
        """Sort keys produces alphabetically sorted keys."""
        fmt = JsonFormatter(json={"sort_keys": True})
        record = _make_record()
        data = json.loads(fmt.format(record))
        keys = list(data.keys())
        assert keys == sorted(keys)

    @staticmethod
    def test_ensure_ascii_true() -> None:
        """ensure_ascii=True escapes non-ASCII chars."""
        fmt = JsonFormatter(json={"ensure_ascii": True})
        record = _make_record(msg="\u00e9")
        result = fmt.format(record)
        assert "\\u00e9" in result

    @staticmethod
    def test_ensure_ascii_false() -> None:
        """ensure_ascii=False preserves non-ASCII chars."""
        fmt = JsonFormatter(json={"ensure_ascii": False})
        record = _make_record(msg="\u00e9")
        result = fmt.format(record)
        assert "\u00e9" in result

    @staticmethod
    def test_extra_fields_included() -> None:
        """Extra fields via extra={} are included."""
        fmt = JsonFormatter(json=True)
        record = _make_record()
        record.user = "alice"
        data = json.loads(fmt.format(record))
        assert data["user"] == "alice"

    @staticmethod
    def test_exc_info_serialized() -> None:
        """exc_info is serialized when present."""  # ruff: ignore[docstring-missing-exception]
        fmt = JsonFormatter(json=True)
        try:
            msg = "boom"
            raise ValueError(msg)  # ruff: ignore[raise-within-try]
        except ValueError:
            import sys

            record = _make_record()
            record.exc_info = sys.exc_info()
        data = json.loads(fmt.format(record))
        assert "exc_info" in data
        assert "ValueError" in data["exc_info"]

    @staticmethod
    def test_exc_info_absent_when_none() -> None:
        """exc_info key absent when no exception."""
        fmt = JsonFormatter(json=True)
        record = _make_record()
        data = json.loads(fmt.format(record))
        assert "exc_info" not in data

    @staticmethod
    def test_stack_info_serialized() -> None:
        """stack_info is serialized when present."""
        fmt = JsonFormatter(json=True)
        record = _make_record()
        record.stack_info = "Stack trace here"
        data = json.loads(fmt.format(record))
        assert data["stack_info"] == "Stack trace here"

    @staticmethod
    def test_stack_info_absent_when_none() -> None:
        """stack_info key absent when not set."""
        fmt = JsonFormatter(json=True)
        record = _make_record()
        data = json.loads(fmt.format(record))
        assert "stack_info" not in data

    @staticmethod
    def test_unknown_field_getattr_fallback() -> None:
        """Unknown field name falls back to getattr."""
        fmt = JsonFormatter(json={"fields": ["nonexistent_field"]})
        record = _make_record()
        data = json.loads(fmt.format(record))
        assert data["nonexistent_field"] is None

    @staticmethod
    def test_non_serializable_uses_default_str() -> None:
        """Non-serializable values use default=str."""
        fmt = JsonFormatter(json=True)
        record = _make_record()
        record.custom_obj = object()
        result = fmt.format(record)
        data = json.loads(result)
        assert isinstance(data["custom_obj"], str)

    @staticmethod
    def test_datefmt_respected() -> None:
        """Custom datefmt is used in timestamp."""
        fmt = JsonFormatter(datefmt="%Y", json=True)
        record = _make_record()
        data = json.loads(fmt.format(record))
        # Should be a 4-digit year
        assert len(data["timestamp"]) == 4
        assert data["timestamp"].isdigit()

    @staticmethod
    def test_message_with_percent_args() -> None:
        """%-style args are interpolated in message."""
        fmt = JsonFormatter(json=True)
        record = _make_record(msg="count=%d", args=(5,))
        data = json.loads(fmt.format(record))
        assert data["message"] == "count=5"

    @staticmethod
    def test_known_field_module() -> None:
        """Module field is extracted correctly."""
        fmt = JsonFormatter(json={"fields": ["module"]})
        record = _make_record()
        data = json.loads(fmt.format(record))
        assert "module" in data

    @staticmethod
    def test_known_field_func_name() -> None:
        """FuncName field is extracted correctly."""
        fmt = JsonFormatter(json={"fields": ["funcName"]})
        record = _make_record()
        data = json.loads(fmt.format(record))
        assert "funcName" in data

    @staticmethod
    def test_known_field_lineno() -> None:
        """Lineno field is extracted correctly."""
        fmt = JsonFormatter(json={"fields": ["lineno"]})
        record = _make_record()
        data = json.loads(fmt.format(record))
        assert data["lineno"] == 42

    @staticmethod
    def test_known_field_pathname() -> None:
        """Pathname field is extracted correctly."""
        fmt = JsonFormatter(json={"fields": ["pathname"]})
        record = _make_record()
        data = json.loads(fmt.format(record))
        assert data["pathname"] == "test_json.py"

    @staticmethod
    def test_no_side_effects_across_calls() -> None:
        """Formatting same record twice gives same result."""
        fmt = JsonFormatter(json=True)
        record = _make_record()
        r1 = fmt.format(record)
        r2 = fmt.format(record)
        assert r1 == r2


class TestJsonIntegration:
    """Tests for JSON integration with functional API."""

    @staticmethod
    def test_get_formatter_json_true_returns_json() -> None:
        """`get_formatter(json=True)` returns JsonFormatter."""
        fmt = get_formatter(json=True)
        assert isinstance(fmt, JsonFormatter)

    @staticmethod
    def test_get_formatter_json_overrides_color() -> None:
        """JSON wins over color silently."""
        fmt = get_formatter(json=True, color="full")
        assert isinstance(fmt, JsonFormatter)

    @staticmethod
    def test_get_formatter_json_false_uses_color() -> None:
        """`json=False` falls back to ColorFormatter."""
        fmt = get_formatter(json=False)
        assert isinstance(fmt, ColorFormatter)

    @staticmethod
    def test_get_formatter_json_spec_dict() -> None:
        """Dict spec creates JsonFormatter with config."""
        fmt = get_formatter(json={"fields": ["level", "message"], "indent": 2})
        assert isinstance(fmt, JsonFormatter)

    @staticmethod
    def test_get_logger_json_true() -> None:
        """get_logger(json=True) adds JsonFormatter."""
        logger = get_logger(name="test_json_gl", handlers="null", json=True)
        assert len(logger.handlers) >= 1
        assert isinstance(logger.handlers[-1].formatter, JsonFormatter)

    @staticmethod
    def test_scribe_json_true() -> None:
        """Scribe(json=True) adds JsonFormatter."""
        scribe = Scribe(name="test_json_sl", json=True)
        assert len(scribe.handlers) >= 1
        assert isinstance(scribe.handlers[-1].formatter, JsonFormatter)

    @staticmethod
    def test_configure_default_logger_json_true() -> None:
        """configure_default_logger(json=True) uses JSON."""
        configure_default_logger(json=True)
        logger = _one_step_module._default_logger
        assert logger is not None
        assert len(logger.handlers) >= 1
        assert isinstance(logger.handlers[-1].formatter, JsonFormatter)

    @staticmethod
    def test_json_formatter_exported() -> None:
        """JsonFormatter is accessible from `sefkhet` package."""
        import sefkhet

        assert hasattr(sefkhet, "JsonFormatter")
        assert sefkhet.JsonFormatter is JsonFormatter


class TestJsonFormatterEndToEnd:  # pylint: disable=too-few-public-methods
    """End-to-end tests with actual logging."""

    @staticmethod
    def test_log_output_is_json() -> None:
        """Logged output through a handler is valid JSON."""
        import io

        stream = io.StringIO()
        scribe = Scribe(
            name="test_json_e2e",
            level=logging.DEBUG,
            handlers=(
                logging.StreamHandler(stream),
                _HandlerKwargs({"level": logging.DEBUG}),
            ),
            formatter="%(message)s",
            json=True,
        )
        scribe.info("hello json")
        output = stream.getvalue().strip()
        data = json.loads(output)
        assert data["message"] == "hello json"
        assert data["level"] == "INFO"
