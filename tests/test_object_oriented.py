"""Tests for `snaplog._object_oriented`."""

import io
import logging

import pytest

from snaplog._color import ColorFormatter
from snaplog._object_oriented import SnapLogger
from snaplog._typing import _HandlerKwargs


class TestSnapLoggerInit:
    """Tests for `SnapLogger.__init__`."""

    @staticmethod
    def test_auto_name_nodefault() -> None:
        """NoDefault name produces 'log0' when counter is reset to 0."""
        snap = SnapLogger()
        assert snap.name == "log0"

    @staticmethod
    def test_auto_name_counter_increments() -> None:
        """Each NoDefault-named instance gets the next counter value."""
        snap0 = SnapLogger()
        snap1 = SnapLogger()
        assert snap0.name == "log0"
        assert snap1.name == "log1"

    @staticmethod
    def test_explicit_name() -> None:
        """An explicit name string is used."""
        snap = SnapLogger(name="myapp")
        assert snap.name == "myapp"

    @staticmethod
    def test_none_name_uses_root() -> None:
        """name=None uses the root logger."""
        snap = SnapLogger(name=None)
        assert snap.logger is logging.root

    @staticmethod
    def test_level_set() -> None:
        """The level is applied to the internal logger."""
        snap = SnapLogger(name="test_oo_level", level=logging.DEBUG)
        assert snap.level == logging.DEBUG

    @staticmethod
    def test_handlers_none_creates_default_stderr() -> None:
        """handlers=None (default) adds a default StreamHandler."""
        snap = SnapLogger(name="test_oo_hdlr_none")
        assert len(snap.handlers) >= 1

    @staticmethod
    def test_formatter_nodefault_is_none() -> None:
        """
        formatter=NoDefault (default) leaves self.formatter as None.
        """  # noqa: D200
        snap = SnapLogger(name="test_oo_fmt_none")
        assert snap.formatter is None

    @staticmethod
    def test_formatter_spec_stored() -> None:
        """A formatter spec is stored on self.formatter."""
        snap = SnapLogger(name="test_oo_fmt_stored", formatter="%(message)s")
        assert snap.formatter is not None
        assert isinstance(snap.formatter, logging.Formatter)

    @staticmethod
    def test_attributes_synced_after_init() -> None:
        """All eight standard attributes mirror the internal logger."""
        snap = SnapLogger(name="test_oo_attr_sync")
        assert snap.name == snap.logger.name
        assert snap.level == snap.logger.level
        assert snap.handlers is snap.logger.handlers
        assert snap.filters is snap.logger.filters
        assert snap.disabled == snap.logger.disabled
        assert snap.propagate == snap.logger.propagate
        assert snap.parent is snap.logger.parent
        assert snap.manager is snap.logger.manager


class TestUpdateLoggerAttributesHook:
    """Tests for the `_update_logger_attributes_hook` decorator."""

    @staticmethod
    def test_sync_after_add_handlers() -> None:
        """
        Adding a handler syncs snap.handlers to the internal logger.
        """  # noqa: D200
        snap = SnapLogger(name="test_oo_hook_add_hdlr", handlers=())
        snap.add_handlers("null")
        assert snap.handlers is snap.logger.handlers
        assert len(snap.handlers) >= 1

    @staticmethod
    def test_sync_after_set_level() -> None:
        """Calling setLevel syncs snap.level to the internal logger."""
        snap = SnapLogger(name="test_oo_hook_set_level")
        snap.setLevel(logging.ERROR)
        assert snap.level == logging.ERROR
        assert snap.level == snap.logger.level

    @staticmethod
    def test_sync_after_remove_handler(
        null_handler: logging.NullHandler,
    ) -> None:
        """Calling removeHandler syncs snap.handlers."""
        snap = SnapLogger(name="test_oo_hook_rm_hdlr", handlers=())
        snap.add_handlers("null")
        hdlr = snap.handlers[-1]
        snap.removeHandler(hdlr)
        assert hdlr not in snap.handlers
        assert snap.handlers is snap.logger.handlers


class TestSnapLoggerAddHandlers:
    """Tests for `SnapLogger.add_handlers`."""

    @staticmethod
    def test_add_single_handler() -> None:
        """A single handler spec adds one handler."""
        snap = SnapLogger(name="test_oo_add_hdlr_single", handlers=())
        snap.add_handlers("null")
        assert len(snap.handlers) == 1

    @staticmethod
    def test_add_multiple_handlers() -> None:
        """A list of handler specs adds multiple handlers."""
        snap = SnapLogger(name="test_oo_add_hdlr_multi", handlers=())
        snap.add_handlers(["null", "stderr"])
        assert len(snap.handlers) == 2


class TestSnapLoggerSetFormatter:
    """Tests for `SnapLogger.set_formatter`."""

    @staticmethod
    def test_sets_formatter_with_string() -> None:
        """A string fmt sets self.formatter and updates handlers."""
        snap = SnapLogger(name="test_oo_sf_str", handlers="null")
        snap.set_formatter("%(message)s")
        assert snap.formatter is not None

    @staticmethod
    def test_sets_formatter_copy_true(
        simple_formatter: logging.Formatter,
    ) -> None:
        """copy=True stores a deepcopy of the provided Formatter."""
        snap = SnapLogger(name="test_oo_sf_copy", handlers="null")
        snap.set_formatter(simple_formatter, copy=True)
        assert snap.formatter is not None
        assert snap.formatter is not simple_formatter

    @staticmethod
    def test_force_true_replaces_existing() -> None:
        """force=True replaces a handler's existing formatter."""
        snap = SnapLogger(
            name="test_oo_sf_force",
            handlers=("null", _HandlerKwargs({"formatter": "%(message)s"})),
        )
        original_fmt = snap.handlers[-1].formatter
        snap.set_formatter("%(levelname)s %(message)s", force=True)
        assert snap.handlers[-1].formatter is not original_fmt

    @staticmethod
    def test_force_false_preserves_existing() -> None:
        """
        force=False (default) does not replace a handler's formatter.
        """  # noqa: D200
        snap = SnapLogger(
            name="test_oo_sf_no_force",
            handlers=("null", _HandlerKwargs({"formatter": "%(message)s"})),
        )
        original_fmt = snap.handlers[-1].formatter
        snap.set_formatter("%(levelname)s %(message)s", force=False)
        assert snap.handlers[-1].formatter is original_fmt


class TestSnapLoggerAddFilters:
    """Tests for `SnapLogger.add_filters`."""

    @staticmethod
    def test_add_string_filter() -> None:
        """A string filter spec adds a filter."""
        snap = SnapLogger(name="test_oo_af_str")
        snap.add_filters("myapp")
        assert len(snap.filters) == 1

    @staticmethod
    def test_add_filter_instance(simple_filter: logging.Filter) -> None:
        """A Filter instance is added."""
        snap = SnapLogger(name="test_oo_af_inst")
        snap.add_filters(simple_filter)
        assert len(snap.filters) == 1


class TestSnapLoggerLog:
    """Tests for `SnapLogger.log`."""

    @staticmethod
    def test_default_level_debug(string_io_stream: io.StringIO) -> None:
        """log() without level defaults to debug."""
        snap = SnapLogger(
            name="test_oo_log_debug",
            level=logging.DEBUG,
            # Pass tuple spec so get_handler sets level=DEBUG on handler
            handlers=(
                logging.StreamHandler(string_io_stream),
                _HandlerKwargs({"level": logging.DEBUG}),
            ),
            formatter="%(message)s",
        )
        snap.log("hello debug")
        assert "hello debug" in string_io_stream.getvalue()

    @staticmethod
    def test_explicit_level(string_io_stream: io.StringIO) -> None:
        """log() with an explicit level logs at that level."""
        snap = SnapLogger(
            name="test_oo_log_info",
            level=logging.DEBUG,
            handlers=logging.StreamHandler(string_io_stream),
            formatter="%(message)s",
        )
        snap.log("hello info", level="info")
        assert "hello info" in string_io_stream.getvalue()

    @staticmethod
    def test_quiet_overrides_level(string_io_stream: io.StringIO) -> None:
        """quiet=True logs at DEBUG regardless of level arg."""
        snap = SnapLogger(
            name="test_oo_log_quiet",
            level=logging.DEBUG,
            handlers=(
                logging.StreamHandler(string_io_stream),
                _HandlerKwargs({"level": logging.DEBUG}),
            ),
            formatter="%(message)s",
        )
        snap.log("quiet msg", level="critical", quiet=True)
        assert "quiet msg" in string_io_stream.getvalue()


class TestSnapLoggerLoggingMethods:
    """Tests for the standard logging-level shortcut methods."""

    @pytest.fixture
    @staticmethod
    def snap_with_capture(string_io_stream: io.StringIO) -> SnapLogger:
        """
        Return a `SnapLogger` capturing output into `string_io_stream`.

        Args:
            string_io_stream (io.StringIO): Stream to log to

        Returns:
            SnapLogger: A `SnapLogger` that logs to `string_io_stream`
        """
        return SnapLogger(
            name="test_oo_methods",
            level=logging.DEBUG,
            # Pass tuple spec so get_handler sets level=DEBUG on handler
            handlers=(
                logging.StreamHandler(string_io_stream),
                _HandlerKwargs({"level": logging.DEBUG}),
            ),
            formatter="%(message)s",
        )

    @staticmethod
    def test_critical(
        snap_with_capture: SnapLogger, string_io_stream: io.StringIO
    ) -> None:
        """critical() logs at CRITICAL level."""
        snap_with_capture.critical("crit msg")
        assert "crit msg" in string_io_stream.getvalue()

    @staticmethod
    def test_debug(
        snap_with_capture: SnapLogger, string_io_stream: io.StringIO
    ) -> None:
        """debug() logs at DEBUG level."""
        snap_with_capture.debug("debug msg")
        assert "debug msg" in string_io_stream.getvalue()

    @staticmethod
    def test_error(
        snap_with_capture: SnapLogger, string_io_stream: io.StringIO
    ) -> None:
        """error() logs at ERROR level."""
        snap_with_capture.error("error msg")
        assert "error msg" in string_io_stream.getvalue()

    @staticmethod
    def test_exception(
        snap_with_capture: SnapLogger, string_io_stream: io.StringIO
    ) -> None:
        """exception() logs at ERROR level."""
        snap_with_capture.exception("exc msg")
        assert "exc msg" in string_io_stream.getvalue()

    @staticmethod
    def test_fatal(
        snap_with_capture: SnapLogger, string_io_stream: io.StringIO
    ) -> None:
        """fatal() logs at FATAL level."""
        snap_with_capture.fatal("fatal msg")
        assert "fatal msg" in string_io_stream.getvalue()

    @staticmethod
    def test_info(
        snap_with_capture: SnapLogger, string_io_stream: io.StringIO
    ) -> None:
        """info() logs at INFO level."""
        snap_with_capture.info("info msg")
        assert "info msg" in string_io_stream.getvalue()

    @staticmethod
    def test_warn(
        snap_with_capture: SnapLogger, string_io_stream: io.StringIO
    ) -> None:
        """warn() logs at WARNING level."""
        snap_with_capture.warn("warn msg")
        assert "warn msg" in string_io_stream.getvalue()

    @staticmethod
    def test_warning(
        snap_with_capture: SnapLogger, string_io_stream: io.StringIO
    ) -> None:
        """warning() logs at WARNING level."""
        snap_with_capture.warning("warning msg")
        assert "warning msg" in string_io_stream.getvalue()


class TestSnapLoggerDelegateMethods:
    """Tests for the delegated `logging.Logger`-compatible methods."""

    @pytest.fixture
    @staticmethod
    def snap() -> SnapLogger:
        """
        Return a basic `SnapLogger` with a `NullHandler`.

        Returns:
            `SnapLogger`: A `SnapLogger` with a `logging.NullHandler`
        """
        return SnapLogger(name="test_oo_delegate", handlers="null")

    @pytest.fixture
    @staticmethod
    def record(snap: SnapLogger) -> logging.LogRecord:
        """
        Return a simple `LogRecord` for the `SnapLogger`.

        Args:
            snap (SnapLogger): The `SnapLogger` to use to generate
                the `LogRecord`

        Returns:
            logging.LogRecord: The `logging.LogRecord` generated by
                the `SnapLogger`
        """
        return snap.logger.makeRecord(
            name=snap.name,
            level=logging.DEBUG,
            fn="test_file.py",
            lno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )

    @staticmethod
    def test_filter(snap: SnapLogger, record: logging.LogRecord) -> None:
        """filter() delegates to the internal logger."""
        result = snap.filter(record)
        assert isinstance(result, (bool, logging.LogRecord))

    @staticmethod
    def test_handle(snap: SnapLogger, record: logging.LogRecord) -> None:
        """handle() delegates to the internal logger without error."""
        snap.handle(record)

    @staticmethod
    def test_addFilter(snap: SnapLogger, simple_filter: logging.Filter) -> None:
        """addFilter() adds a filter and syncs snap.filters."""
        snap.addFilter(simple_filter)
        assert simple_filter in snap.filters
        assert snap.filters is snap.logger.filters

    @staticmethod
    def test_addHandler(
        snap: SnapLogger, null_handler: logging.NullHandler
    ) -> None:
        """addHandler() adds a handler and syncs snap.handlers."""
        snap.addHandler(null_handler)
        assert null_handler in snap.handlers
        assert snap.handlers is snap.logger.handlers

    @staticmethod
    def test_callHandlers(snap: SnapLogger, record: logging.LogRecord) -> None:
        """callHandlers() delegates without error."""
        snap.callHandlers(record)

    @staticmethod
    def test_findCaller(snap: SnapLogger) -> None:
        """findCaller() returns a 4-tuple."""
        result = snap.findCaller()
        assert isinstance(result, tuple)
        assert len(result) == 4

    @staticmethod
    def test_getChild(snap: SnapLogger) -> None:
        """getChild() returns a Logger."""
        child = snap.getChild("child")
        assert isinstance(child, logging.Logger)

    @staticmethod
    def test_getChildren(snap: SnapLogger) -> None:
        """getChildren() returns a set."""
        result = snap.getChildren()
        assert isinstance(result, set)

    @staticmethod
    def test_getEffectiveLevel(snap: SnapLogger) -> None:
        """getEffectiveLevel() returns an int."""
        result = snap.getEffectiveLevel()
        assert isinstance(result, int)

    @staticmethod
    def test_hasHandlers(snap: SnapLogger) -> None:
        """hasHandlers() returns True when a handler is present."""
        assert snap.hasHandlers()

    @staticmethod
    def test_isEnabledFor(snap: SnapLogger) -> None:
        """isEnabledFor() returns a bool."""
        result = snap.isEnabledFor(logging.DEBUG)
        assert isinstance(result, bool)

    @staticmethod
    def test_makeRecord(snap: SnapLogger) -> None:
        """makeRecord() returns a LogRecord."""
        record = snap.makeRecord(
            name=snap.name,
            level=logging.DEBUG,
            fn="test.py",
            lno=1,
            msg="msg",
            args=(),
            exc_info=None,
        )
        assert isinstance(record, logging.LogRecord)

    @staticmethod
    def test_removeFilter(
        snap: SnapLogger, simple_filter: logging.Filter
    ) -> None:
        """removeFilter() removes a filter and syncs snap.filters."""
        snap.addFilter(simple_filter)
        assert simple_filter in snap.filters
        snap.removeFilter(simple_filter)
        assert simple_filter not in snap.filters
        assert snap.filters is snap.logger.filters

    @staticmethod
    def test_removeHandler(
        snap: SnapLogger, null_handler: logging.NullHandler
    ) -> None:
        """removeHandler() removes a handler and syncs snap.handlers."""
        snap.addHandler(null_handler)
        assert null_handler in snap.handlers
        snap.removeHandler(null_handler)
        assert null_handler not in snap.handlers
        assert snap.handlers is snap.logger.handlers

    @staticmethod
    def test_setLevel(snap: SnapLogger) -> None:
        """setLevel() updates the level on internal logger and syncs."""
        snap.setLevel(logging.ERROR)
        assert snap.level == logging.ERROR
        assert snap.level == snap.logger.level


class TestSnapLoggerColor:  # pylint: disable=too-few-public-methods
    """Tests for the `color` parameter of `SnapLogger.__init__`."""

    @staticmethod
    def test_color_full_creates_color_formatter() -> None:
        """color='full' gives the handler a ColorFormatter."""
        snap = SnapLogger(name="test_oo_color_full", color="full")
        assert len(snap.handlers) >= 1
        assert isinstance(snap.handlers[-1].formatter, ColorFormatter)

    @staticmethod
    def test_tuple_color_creates_color_formatter() -> None:
        """Tuple color with callable gives handler a ColorFormatter."""
        snap = SnapLogger(
            name="test_oo_color_tuple",
            color=("full", lambda _: "\033[99m"),
        )
        assert len(snap.handlers) >= 1
        assert isinstance(snap.handlers[-1].formatter, ColorFormatter)
