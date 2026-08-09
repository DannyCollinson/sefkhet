"""Tests for `sefkhet._object_oriented`."""

import io
import logging
import logging.handlers
import threading
from pathlib import Path

import pytest

from sefkhet._color import ColorFormatter
from sefkhet._object_oriented import Scribe
from sefkhet._typing import _HandlerKwargs


class TestScribeInit:
    """Tests for `Scribe.__init__`."""

    @staticmethod
    def test_auto_name_nodefault() -> None:
        """
        _NoDefault name produces 'log0' when counter is reset to 0.
        """  # noqa: D200
        scribe = Scribe()
        assert scribe.name == "log0"

    @staticmethod
    def test_auto_name_counter_increments() -> None:
        """
        Each _NoDefault-named instance gets the next counter value.
        """  # noqa: D200
        scribe0 = Scribe()
        scribe1 = Scribe()
        assert scribe0.name == "log0"
        assert scribe1.name == "log1"

    @staticmethod
    def test_explicit_name() -> None:
        """An explicit name string is used."""
        scribe = Scribe(name="myapp")
        assert scribe.name == "myapp"

    @staticmethod
    def test_none_name_uses_root() -> None:
        """name=None uses the root logger."""
        scribe = Scribe(name=None)
        assert scribe.logger is logging.root

    @staticmethod
    def test_level_set() -> None:
        """The level is applied to the internal logger."""
        scribe = Scribe(name="test_oo_level", level=logging.DEBUG)
        assert scribe.level == logging.DEBUG

    @staticmethod
    def test_handlers_none_creates_default_stderr() -> None:
        """handlers=None (default) adds a default StreamHandler."""
        scribe = Scribe(name="test_oo_hdlr_none")
        assert len(scribe.handlers) >= 1

    @staticmethod
    def test_formatter_nodefault_is_none() -> None:
        """
        formatter=_NoDefault (default) leaves self.formatter as None.
        """  # noqa: D200
        scribe = Scribe(name="test_oo_fmt_none")
        assert scribe.formatter is None

    @staticmethod
    def test_formatter_spec_stored() -> None:
        """A formatter spec is stored on self.formatter."""
        scribe = Scribe(name="test_oo_fmt_stored", formatter="%(message)s")
        assert scribe.formatter is not None
        assert isinstance(scribe.formatter, logging.Formatter)

    @staticmethod
    def test_attributes_synced_after_init() -> None:
        """All eight standard attributes mirror the internal logger."""
        scribe = Scribe(name="test_oo_attr_sync")
        assert scribe.name == scribe.logger.name
        assert scribe.level == scribe.logger.level
        assert scribe.handlers is scribe.logger.handlers
        assert scribe.filters is scribe.logger.filters
        assert scribe.disabled == scribe.logger.disabled
        assert scribe.propagate == scribe.logger.propagate
        assert scribe.parent is scribe.logger.parent
        assert scribe.manager is scribe.logger.manager


class TestUpdateLoggerAttributesHook:
    """Tests for the `_update_logger_attributes_hook` decorator."""

    @staticmethod
    def test_sync_after_add_handlers() -> None:
        """
        Adding a handler syncs scribe.handlers to the internal logger.
        """  # noqa: D200
        scribe = Scribe(name="test_oo_hook_add_hdlr", handlers=())
        scribe.add_handlers("null")
        assert scribe.handlers is scribe.logger.handlers
        assert len(scribe.handlers) >= 1

    @staticmethod
    def test_sync_after_set_level() -> None:
        """Calling setLevel syncs scribe.level to the internal logger."""
        scribe = Scribe(name="test_oo_hook_set_level")
        scribe.setLevel(logging.ERROR)
        assert scribe.level == logging.ERROR
        assert scribe.level == scribe.logger.level

    @staticmethod
    def test_sync_after_remove_handler(
        null_handler: logging.NullHandler,
    ) -> None:
        """Calling removeHandler syncs scribe.handlers."""
        scribe = Scribe(name="test_oo_hook_rm_hdlr", handlers=())
        scribe.add_handlers("null")
        hdlr = scribe.handlers[-1]
        scribe.removeHandler(hdlr)
        assert hdlr not in scribe.handlers
        assert scribe.handlers is scribe.logger.handlers


class TestScribeAddHandlers:
    """Tests for `Scribe.add_handlers`."""

    @staticmethod
    def test_add_single_handler() -> None:
        """A single handler spec adds one handler."""
        scribe = Scribe(name="test_oo_add_hdlr_single", handlers=())
        scribe.add_handlers("null")
        assert len(scribe.handlers) == 1

    @staticmethod
    def test_add_multiple_handlers() -> None:
        """A list of handler specs adds multiple handlers."""
        scribe = Scribe(name="test_oo_add_hdlr_multi", handlers=())
        scribe.add_handlers(["null", "stderr"])
        assert len(scribe.handlers) == 2


class TestScribeSetFormatter:
    """Tests for `Scribe.set_formatter`."""

    @staticmethod
    def test_sets_formatter_with_string() -> None:
        """A string fmt sets self.formatter and updates handlers."""
        scribe = Scribe(name="test_oo_sf_str", handlers="null")
        scribe.set_formatter("%(message)s")
        assert scribe.formatter is not None

    @staticmethod
    def test_sets_formatter_copy_true(
        simple_formatter: logging.Formatter,
    ) -> None:
        """copy=True stores a deepcopy of the provided Formatter."""
        scribe = Scribe(name="test_oo_sf_copy", handlers="null")
        scribe.set_formatter(simple_formatter, copy=True)
        assert scribe.formatter is not None
        assert scribe.formatter is not simple_formatter

    @staticmethod
    def test_force_true_replaces_existing() -> None:
        """force=True replaces a handler's existing formatter."""
        scribe = Scribe(
            name="test_oo_sf_force",
            handlers=("null", _HandlerKwargs({"formatter": "%(message)s"})),
        )
        original_fmt = scribe.handlers[-1].formatter
        scribe.set_formatter("%(levelname)s %(message)s", force=True)
        assert scribe.handlers[-1].formatter is not original_fmt

    @staticmethod
    def test_force_false_preserves_existing() -> None:
        """
        force=False (default) does not replace a handler's formatter.
        """  # noqa: D200
        scribe = Scribe(
            name="test_oo_sf_no_force",
            handlers=("null", _HandlerKwargs({"formatter": "%(message)s"})),
        )
        original_fmt = scribe.handlers[-1].formatter
        scribe.set_formatter("%(levelname)s %(message)s", force=False)
        assert scribe.handlers[-1].formatter is original_fmt


class TestScribeAddFilters:
    """Tests for `Scribe.add_filters`."""

    @staticmethod
    def test_add_string_filter() -> None:
        """A string filter spec adds a filter."""
        scribe = Scribe(name="test_oo_af_str")
        scribe.add_filters("myapp")
        assert len(scribe.filters) == 1

    @staticmethod
    def test_add_filter_instance(simple_filter: logging.Filter) -> None:
        """A Filter instance is added."""
        scribe = Scribe(name="test_oo_af_inst")
        scribe.add_filters(simple_filter)
        assert len(scribe.filters) == 1


class TestScribeLog:
    """Tests for `Scribe.log` (standard `logging` API)."""

    @staticmethod
    def test_int_level(string_io_stream: io.StringIO) -> None:
        """log(int_level, msg) logs the message."""
        scribe = Scribe(
            name="test_oo_log_int",
            level=logging.DEBUG,
            handlers=(
                logging.StreamHandler(string_io_stream),
                _HandlerKwargs({"level": logging.DEBUG}),
            ),
            formatter="%(message)s",
        )
        scribe.log(logging.DEBUG, "hello debug")
        assert "hello debug" in string_io_stream.getvalue()

    @staticmethod
    def test_str_level(string_io_stream: io.StringIO) -> None:
        """log(str_level, msg) logs the message."""
        scribe = Scribe(
            name="test_oo_log_str",
            level=logging.DEBUG,
            handlers=(
                logging.StreamHandler(string_io_stream),
                _HandlerKwargs({"level": logging.DEBUG}),
            ),
            formatter="%(message)s",
        )
        scribe.log("info", "hello info")
        assert "hello info" in string_io_stream.getvalue()


class TestScribeRecord:
    """Tests for `Scribe.record` (scribe-style API)."""

    @staticmethod
    def test_default_level_debug(string_io_stream: io.StringIO) -> None:
        """record() without level defaults to debug."""
        scribe = Scribe(
            name="test_oo_rec_debug",
            level=logging.DEBUG,
            handlers=(
                logging.StreamHandler(string_io_stream),
                _HandlerKwargs({"level": logging.DEBUG}),
            ),
            formatter="%(message)s",
        )
        scribe.record("hello debug")
        assert "hello debug" in string_io_stream.getvalue()

    @staticmethod
    def test_explicit_level(string_io_stream: io.StringIO) -> None:
        """record() with an explicit level logs at that level."""
        scribe = Scribe(
            name="test_oo_rec_info",
            level=logging.DEBUG,
            handlers=(
                logging.StreamHandler(string_io_stream),
                _HandlerKwargs({"level": logging.DEBUG}),
            ),
            formatter="%(message)s",
        )
        scribe.record("hello info", level="info")
        assert "hello info" in string_io_stream.getvalue()

    @staticmethod
    def test_quiet_overrides_level() -> None:
        """quiet=True forces the record level to DEBUG."""
        captured: list[logging.LogRecord] = []

        class _CaptureHandler(logging.Handler):
            def emit(  # noqa: PLR6301
                self, record: logging.LogRecord
            ) -> None:
                captured.append(record)

        handler = _CaptureHandler()
        scribe = Scribe(
            name="test_oo_rec_quiet",
            level=logging.DEBUG,
            handlers=(handler, _HandlerKwargs({"level": logging.DEBUG})),
            formatter="%(message)s",
        )
        scribe.record("quiet msg", level="critical", quiet=True)
        assert len(captured) == 1
        assert captured[0].levelno == logging.DEBUG


class TestScribeRec:  # pylint: disable=too-few-public-methods
    """Tests for `Scribe.rec` (alias for `record`)."""

    @staticmethod
    def test_rec_is_alias(string_io_stream: io.StringIO) -> None:
        """rec() delegates to record() without error."""
        scribe = Scribe(
            name="test_oo_rec_alias",
            level=logging.DEBUG,
            handlers=(
                logging.StreamHandler(string_io_stream),
                _HandlerKwargs({"level": logging.DEBUG}),
            ),
            formatter="%(message)s",
        )
        scribe.rec("msg")


class TestScribeLoggingMethods:
    """Tests for the standard logging-level shortcut methods."""

    @pytest.fixture
    @staticmethod
    def scribe_with_capture(string_io_stream: io.StringIO) -> Scribe:
        """
        Return a `Scribe` capturing output into `string_io_stream`.

        Args:
            string_io_stream (io.StringIO): Stream to log to

        Returns:
            Scribe: A `Scribe` that logs to `string_io_stream`
        """
        return Scribe(
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
        scribe_with_capture: Scribe, string_io_stream: io.StringIO
    ) -> None:
        """critical() logs at CRITICAL level."""
        scribe_with_capture.critical("crit msg")
        assert "crit msg" in string_io_stream.getvalue()

    @staticmethod
    def test_debug(
        scribe_with_capture: Scribe, string_io_stream: io.StringIO
    ) -> None:
        """debug() logs at DEBUG level."""
        scribe_with_capture.debug("debug msg")
        assert "debug msg" in string_io_stream.getvalue()

    @staticmethod
    def test_error(
        scribe_with_capture: Scribe, string_io_stream: io.StringIO
    ) -> None:
        """error() logs at ERROR level."""
        scribe_with_capture.error("error msg")
        assert "error msg" in string_io_stream.getvalue()

    @staticmethod
    def test_exception(
        scribe_with_capture: Scribe, string_io_stream: io.StringIO
    ) -> None:
        """exception() logs at ERROR level."""
        scribe_with_capture.exception("exc msg")
        assert "exc msg" in string_io_stream.getvalue()

    @staticmethod
    def test_fatal(
        scribe_with_capture: Scribe, string_io_stream: io.StringIO
    ) -> None:
        """fatal() logs at FATAL level."""
        scribe_with_capture.fatal("fatal msg")
        assert "fatal msg" in string_io_stream.getvalue()

    @staticmethod
    def test_info(
        scribe_with_capture: Scribe, string_io_stream: io.StringIO
    ) -> None:
        """info() logs at INFO level."""
        scribe_with_capture.info("info msg")
        assert "info msg" in string_io_stream.getvalue()

    @staticmethod
    def test_warn(
        scribe_with_capture: Scribe, string_io_stream: io.StringIO
    ) -> None:
        """warn() logs at WARNING level."""
        scribe_with_capture.warn("warn msg")
        assert "warn msg" in string_io_stream.getvalue()

    @staticmethod
    def test_warning(
        scribe_with_capture: Scribe, string_io_stream: io.StringIO
    ) -> None:
        """warning() logs at WARNING level."""
        scribe_with_capture.warning("warning msg")
        assert "warning msg" in string_io_stream.getvalue()


class TestScribeDelegateMethods:
    """Tests for the delegated `logging.Logger`-compatible methods."""

    @pytest.fixture
    @staticmethod
    def scribe() -> Scribe:
        """
        Return a basic `Scribe` with a `NullHandler`.

        Returns:
            `Scribe`: A `Scribe` with a `logging.NullHandler`
        """
        return Scribe(name="test_oo_delegate", handlers="null")

    @pytest.fixture
    @staticmethod
    def record(scribe: Scribe) -> logging.LogRecord:
        """
        Return a simple `LogRecord` for the `Scribe`.

        Args:
            scribe (Scribe): The `Scribe` to use to generate
                the `LogRecord`

        Returns:
            logging.LogRecord: The `logging.LogRecord` generated by
                the `Scribe`
        """
        return scribe.logger.makeRecord(
            name=scribe.name,
            level=logging.DEBUG,
            fn="test_file.py",
            lno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )

    @staticmethod
    def test_filter(scribe: Scribe, record: logging.LogRecord) -> None:
        """filter() delegates to the internal logger."""
        result = scribe.filter(record)
        assert isinstance(result, (bool, logging.LogRecord))

    @staticmethod
    def test_handle(scribe: Scribe, record: logging.LogRecord) -> None:
        """handle() delegates to the internal logger without error."""
        scribe.handle(record)

    @staticmethod
    def test_addFilter(scribe: Scribe, simple_filter: logging.Filter) -> None:
        """addFilter() adds a filter and syncs scribe.filters."""
        scribe.addFilter(simple_filter)
        assert simple_filter in scribe.filters
        assert scribe.filters is scribe.logger.filters

    @staticmethod
    def test_addHandler(
        scribe: Scribe, null_handler: logging.NullHandler
    ) -> None:
        """addHandler() adds a handler and syncs scribe.handlers."""
        scribe.addHandler(null_handler)
        assert null_handler in scribe.handlers
        assert scribe.handlers is scribe.logger.handlers

    @staticmethod
    def test_callHandlers(scribe: Scribe, record: logging.LogRecord) -> None:
        """callHandlers() delegates without error."""
        scribe.callHandlers(record)

    @staticmethod
    def test_findCaller(scribe: Scribe) -> None:
        """findCaller() returns a 4-tuple."""
        result = scribe.findCaller()
        assert isinstance(result, tuple)
        assert len(result) == 4

    @staticmethod
    def test_getChild(scribe: Scribe) -> None:
        """getChild() returns a Logger."""
        child = scribe.getChild("child")
        assert isinstance(child, logging.Logger)

    @staticmethod
    def test_getChildren(scribe: Scribe) -> None:
        """getChildren() returns a set."""
        result = scribe.getChildren()
        assert isinstance(result, set)

    @staticmethod
    def test_getEffectiveLevel(scribe: Scribe) -> None:
        """getEffectiveLevel() returns an int."""
        result = scribe.getEffectiveLevel()
        assert isinstance(result, int)

    @staticmethod
    def test_hasHandlers(scribe: Scribe) -> None:
        """hasHandlers() returns True when a handler is present."""
        assert scribe.hasHandlers()

    @staticmethod
    def test_isEnabledFor(scribe: Scribe) -> None:
        """isEnabledFor() returns a bool."""
        result = scribe.isEnabledFor(logging.DEBUG)
        assert isinstance(result, bool)

    @staticmethod
    def test_makeRecord(scribe: Scribe) -> None:
        """makeRecord() returns a LogRecord."""
        record = scribe.makeRecord(
            name=scribe.name,
            level=logging.DEBUG,
            fn="test.py",
            lno=1,
            msg="msg",
            args=(),
            exc_info=None,
        )
        assert isinstance(record, logging.LogRecord)

    @staticmethod
    def test_removeFilter(scribe: Scribe, simple_filter: logging.Filter) -> None:
        """removeFilter() removes a filter and syncs scribe.filters."""
        scribe.addFilter(simple_filter)
        assert simple_filter in scribe.filters
        scribe.removeFilter(simple_filter)
        assert simple_filter not in scribe.filters
        assert scribe.filters is scribe.logger.filters

    @staticmethod
    def test_removeHandler(
        scribe: Scribe, null_handler: logging.NullHandler
    ) -> None:
        """removeHandler() removes a handler and syncs scribe.handlers."""
        scribe.addHandler(null_handler)
        assert null_handler in scribe.handlers
        scribe.removeHandler(null_handler)
        assert null_handler not in scribe.handlers
        assert scribe.handlers is scribe.logger.handlers

    @staticmethod
    def test_setLevel(scribe: Scribe) -> None:
        """setLevel() updates the level on internal logger and syncs."""
        scribe.setLevel(logging.ERROR)
        assert scribe.level == logging.ERROR
        assert scribe.level == scribe.logger.level

    @staticmethod
    def test_setLevel_with_string_shorthand(scribe: Scribe) -> None:
        """setLevel('d') sets level to DEBUG via _parse_log_level."""
        scribe.setLevel("d")
        assert scribe.level == logging.DEBUG
        assert scribe.level == scribe.logger.level


class TestScribeColor:
    """Tests for the `color` parameter of `Scribe.__init__`."""

    @staticmethod
    def test_color_full_creates_color_formatter() -> None:
        """color='full' gives the handler a ColorFormatter."""
        scribe = Scribe(name="test_oo_color_full", color="full")
        assert len(scribe.handlers) >= 1
        assert isinstance(scribe.handlers[-1].formatter, ColorFormatter)

    @staticmethod
    def test_tuple_color_creates_color_formatter() -> None:
        """Tuple color with callable gives handler a ColorFormatter."""
        scribe = Scribe(
            name="test_oo_color_tuple", color=("full", lambda _: "\033[99m")
        )
        assert len(scribe.handlers) >= 1
        assert isinstance(scribe.handlers[-1].formatter, ColorFormatter)


class TestScribeNameAwareFmt:
    """Tests for name-aware default format strings in Scribe."""

    @staticmethod
    def test_custom_name_includes_name_in_fmt() -> None:
        """Scribe with custom name has %(name)s in fmt."""
        scribe = Scribe(name="test_oo_nafmt_custom")
        assert len(scribe.handlers) >= 1
        fmt = scribe.handlers[-1].formatter
        assert fmt is not None
        assert "%(name)s" in fmt._fmt  # type: ignore[operator] # pyright: ignore[reportOperatorIssue]

    @staticmethod
    def test_auto_numbered_name_includes_name_in_fmt() -> None:
        """Scribe with auto-numbered name has %(name)s."""
        scribe = Scribe()
        assert scribe.name == "log0"
        assert len(scribe.handlers) >= 1
        fmt = scribe.handlers[-1].formatter
        assert fmt is not None
        assert "%(name)s" in fmt._fmt  # type: ignore[operator] # pyright: ignore[reportOperatorIssue]

    @staticmethod
    def test_explicit_formatter_not_overridden() -> None:
        """Explicit formatter is not overridden by name logic."""
        scribe = Scribe(name="test_oo_nafmt_explicit", formatter="%(message)s")
        assert len(scribe.handlers) >= 1
        fmt = scribe.handlers[-1].formatter
        assert fmt is not None
        assert fmt._fmt == "%(message)s"


class TestScribeConcurrency:
    """Tests for concurrent Scribe creation."""

    @staticmethod
    def test_concurrent_creation_unique_names() -> None:
        """Concurrent creation produces unique sequential names."""
        results: list[str] = []
        errors: list[Exception] = []

        def _create() -> None:
            try:
                scribe = Scribe()
                results.append(scribe.name)
            except Exception as exc:  # noqa: BLE001 # pragma: no cover
                errors.append(exc)

        threads = [threading.Thread(target=_create) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert len(results) == 20
        assert len(set(results)) == 20


class TestScribeMixedHandlers:
    """Tests for Scribe with mixed handler specs."""

    @staticmethod
    def test_mixed_handler_specs() -> None:
        """Mixed handler list (str + tuple) creates all handlers."""
        scribe = Scribe(
            name="test_oo_mixed_hdlr",
            handlers=[
                "null",
                ("stderr", _HandlerKwargs({"level": logging.ERROR})),
            ],
        )
        assert len(scribe.handlers) == 2
        assert scribe.handlers[1].level == logging.ERROR


class TestUpdateLoggerAttributesHookException:
    """Tests for hook behaviour when the wrapped method raises."""

    @staticmethod
    def test_hook_reraises_original_exception(
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The original RuntimeError propagates unchanged."""
        scribe = Scribe(name="test_oo_hook_exc_reraise", handlers="null")
        msg = "boom"

        def _raise(**_kwargs: object) -> None:
            raise RuntimeError(msg)

        monkeypatch.setattr(scribe.logger, "addHandler", _raise)
        with pytest.raises(RuntimeError, match="boom"):
            scribe.addHandler(logging.NullHandler())

    @staticmethod
    def test_hook_syncs_attributes_after_exception(
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Attributes stay consistent after an exception."""
        scribe = Scribe(name="test_oo_hook_exc_sync", handlers="null")
        pre_attrs = {
            a: getattr(scribe, a)
            for a in (
                "name",
                "level",
                "handlers",
                "filters",
                "disabled",
                "propagate",
                "parent",
                "manager",
            )
        }
        msg = "boom"

        def _raise(**_kwargs: object) -> None:
            raise RuntimeError(msg)

        monkeypatch.setattr(scribe.logger, "addHandler", _raise)
        with pytest.raises(RuntimeError, match="boom"):
            scribe.addHandler(logging.NullHandler())

        for attr, old_val in pre_attrs.items():
            scribe_val = getattr(scribe, attr)
            logger_val = getattr(scribe.logger, attr)
            assert scribe_val == logger_val, (
                f"{attr}: scribe={scribe_val!r}, logger={logger_val!r}"
            )
            assert scribe_val == old_val, (
                f"{attr} changed: {old_val!r} -> {scribe_val!r}"
            )


class TestScribeExceptionExcInfo:
    """Tests for Scribe.exception() exc_info default."""

    @staticmethod
    def test_exception_captures_exc_info_by_default(
        string_io_stream: io.StringIO,
    ) -> None:
        """exception() captures traceback by default."""  # noqa: DOC501
        scribe = Scribe(
            name="test_oo_exc_info_default",
            level=logging.DEBUG,
            handlers=(
                logging.StreamHandler(string_io_stream),
                _HandlerKwargs({"level": logging.DEBUG}),
            ),
            formatter="%(message)s",
        )
        msg = "boom"
        try:
            raise ValueError(msg)  # noqa: TRY301
        except ValueError:
            scribe.exception("caught it")
        output = string_io_stream.getvalue()
        assert "caught it" in output
        assert "ValueError" in output
        assert "boom" in output
        assert "Traceback" in output

    @staticmethod
    def test_exception_exc_info_false_suppresses_traceback(
        string_io_stream: io.StringIO,
    ) -> None:
        """exception(exc_info=False) suppresses traceback."""  # noqa: DOC501
        scribe = Scribe(
            name="test_oo_exc_info_false",
            level=logging.DEBUG,
            handlers=(
                logging.StreamHandler(string_io_stream),
                _HandlerKwargs({"level": logging.DEBUG}),
            ),
            formatter="%(message)s",
        )
        msg = "boom"
        try:
            raise ValueError(msg)  # noqa: TRY301
        except ValueError:
            scribe.exception("caught it", exc_info=False)
        output = string_io_stream.getvalue()
        assert "caught it" in output
        assert "Traceback" not in output


class TestScribeLogEdgeCases:
    """Edge-case tests for Scribe.log."""

    @staticmethod
    def test_log_with_exc_info_exception_instance(
        string_io_stream: io.StringIO,
    ) -> None:
        """exc_info=ValueError(...) includes exception info."""
        scribe = Scribe(
            name="test_oo_exc_info_inst",
            level=logging.DEBUG,
            handlers=(
                logging.StreamHandler(string_io_stream),
                _HandlerKwargs({"level": logging.DEBUG}),
            ),
            formatter="%(message)s",
        )
        scribe.log("error", "bad", exc_info=ValueError("test"))
        output = string_io_stream.getvalue()
        assert "bad" in output
        assert "ValueError" in output

    @staticmethod
    def test_log_with_extra_kwargs(string_io_stream: io.StringIO) -> None:
        """Extra dict is available in the format string."""
        scribe = Scribe(
            name="test_oo_extra_kw",
            level=logging.DEBUG,
            handlers=(
                logging.StreamHandler(string_io_stream),
                _HandlerKwargs({"level": logging.DEBUG}),
            ),
            formatter="%(user)s: %(message)s",
        )
        scribe.log("info", "hi", extra={"user": "alice"})
        assert "alice" in string_io_stream.getvalue()

    @staticmethod
    def test_log_with_non_string_message(string_io_stream: io.StringIO) -> None:
        """Non-string message (int) is accepted."""
        scribe = Scribe(
            name="test_oo_nonstr_msg",
            level=logging.DEBUG,
            handlers=(
                logging.StreamHandler(string_io_stream),
                _HandlerKwargs({"level": logging.DEBUG}),
            ),
            formatter="%(message)s",
        )
        scribe.log("info", 42)
        assert "42" in string_io_stream.getvalue()


class TestScribeIntegration:  # pylint: disable=too-few-public-methods
    """Integration tests combining Scribe with handlers."""

    @staticmethod
    def test_scribe_with_queued_handler(tmp_path: Path) -> None:
        """Scribe with queued file handler delivers msg."""
        log_file = str(tmp_path / "queued.log")
        scribe = Scribe(
            name="test_oo_queued_int",
            level=logging.DEBUG,
            handlers=(
                log_file,
                _HandlerKwargs(
                    {
                        "queued": True,
                        "level": logging.DEBUG,
                        "formatter": "%(message)s",
                    }
                ),
            ),
        )
        scribe.info("queued msg")
        # Stop the listener to flush
        for h in scribe.handlers:
            if (  # pragma: no branch
                isinstance(h, logging.handlers.QueueHandler)
                and h.listener is not None
            ):
                h.listener.stop()
        assert "queued msg" in Path(log_file).read_text(encoding="utf-8")
