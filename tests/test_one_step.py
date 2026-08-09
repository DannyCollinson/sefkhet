"""Tests for `sefkhet._one_step`."""

import io
import logging
import threading
from typing import cast

import sefkhet._one_step as _one_step_module
from sefkhet._color import ColorFormatter
from sefkhet._one_step import configure_default_logger, log, rec, record


class TestConfigureDefaultLogger:
    """Tests for `configure_default_logger`."""

    @staticmethod
    def test_default_call_creates_scribe() -> None:
        """Calling with all defaults creates a logger named 'scribe'."""
        configure_default_logger()
        assert _one_step_module._default_logger is not None
        assert _one_step_module._default_logger.name == "scribe"

    @staticmethod
    def test_explicit_name() -> None:
        """Passing name= uses that name instead of 'scribe'."""
        configure_default_logger(name="mylogger")
        assert _one_step_module._default_logger is not None
        assert _one_step_module._default_logger.name == "mylogger"

    @staticmethod
    def test_explicit_level() -> None:
        """Passing level= applies that level to the default logger."""
        configure_default_logger(level=logging.DEBUG)
        assert _one_step_module._default_logger is not None
        assert _one_step_module._default_logger.level == logging.DEBUG

    @staticmethod
    def test_explicit_handlers() -> None:
        """Passing handlers= uses provided handlers."""
        configure_default_logger(handlers="null")
        logger = _one_step_module._default_logger
        assert logger is not None
        assert len(logger.handlers) >= 1

    @staticmethod
    def test_explicit_formatter() -> None:
        """Passing formatter= does not raise and creates a logger."""
        configure_default_logger(formatter="%(message)s")
        assert _one_step_module._default_logger is not None

    @staticmethod
    def test_explicit_filters() -> None:
        """Passing filters= adds filters to the default logger."""
        configure_default_logger(filters="myapp")
        logger = _one_step_module._default_logger
        assert logger is not None
        assert len(logger.filters) == 1

    @staticmethod
    def test_already_configured_no_force_returns_early() -> None:
        """A second call without force=True does nothing."""
        configure_default_logger(name="first")
        first = _one_step_module._default_logger
        configure_default_logger(name="second")
        assert _one_step_module._default_logger is first

    @staticmethod
    def test_force_true_reconfigures() -> None:
        """force=True replaces the existing default logger."""
        configure_default_logger(name="original")
        first = _one_step_module._default_logger
        configure_default_logger(name="replacement", force=True)
        assert _one_step_module._default_logger is not first
        assert _one_step_module._default_logger is not None
        assert _one_step_module._default_logger.name == "replacement"

    @staticmethod
    def test_spec_only_creates_spec_logger() -> None:
        """
        When spec= is given and all other
        args are defaults, spec is used.
        """
        configure_default_logger(spec="test_os_spec_logger")
        logger = _one_step_module._default_logger
        assert logger is not None
        assert logger.name == "test_os_spec_logger"

    @staticmethod
    def test_spec_ignored_when_other_arg_provided() -> None:
        """
        When name= is also given, the spec= condition is False
        (not all params are _NoDefault) and spec is ignored.
        """
        configure_default_logger(name="explicit_name", spec="ignored_spec")
        logger = _one_step_module._default_logger
        assert logger is not None
        assert logger.name == "explicit_name"

    @staticmethod
    def test_custom_name_includes_name_in_fmt() -> None:
        """
        Custom name includes %(name)s in the auto-created
        formatter.
        """
        configure_default_logger(name="myapp")
        logger = _one_step_module._default_logger
        assert logger is not None
        assert len(logger.handlers) >= 1
        fmt = logger.handlers[-1].formatter
        assert fmt is not None
        assert "%(name)s" in fmt._fmt  # type: ignore[operator] # pyright: ignore[reportOperatorIssue]

    @staticmethod
    def test_default_name_excludes_name_in_fmt() -> None:
        """
        Default name 'scribe' excludes %(name)s from the
        auto-created formatter.
        """
        configure_default_logger()
        logger = _one_step_module._default_logger
        assert logger is not None
        assert len(logger.handlers) >= 1
        fmt = logger.handlers[-1].formatter
        assert fmt is not None
        assert "%(name)s" not in fmt._fmt  # type: ignore[operator] # pyright: ignore[reportOperatorIssue]


class TestLog:
    """Tests for `log` (standard `logging.Logger.log` API)."""

    @staticmethod
    def test_logger_nodefault_creates_default() -> None:
        """First call with no logger creates the default logger."""
        log("debug", "msg")
        assert _one_step_module._default_logger is not None

    @staticmethod
    def test_logger_nodefault_reuses_default() -> None:
        """Subsequent calls reuse the same default logger."""
        log("debug", "first")
        first_logger = _one_step_module._default_logger
        log("debug", "second")
        assert _one_step_module._default_logger is first_logger

    @staticmethod
    def test_explicit_logger_instance() -> None:
        """Passing a Logger instance uses that logger directly."""
        stream = io.StringIO()
        explicit = logging.getLogger("test_os_explicit_inst")
        explicit.setLevel(logging.DEBUG)
        handler: logging.StreamHandler[io.StringIO] = logging.StreamHandler(
            stream
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        explicit.addHandler(handler)

        log("debug", "explicit msg", logger=explicit)

        assert "explicit msg" in stream.getvalue()

    @staticmethod
    def test_spec_with_no_default_logger() -> None:
        """
        When no default logger exists and a spec is passed,
        configure_default_logger(spec=...) is called.
        """
        assert _one_step_module._default_logger is None
        _one_step_module.log(
            "debug", "spec msg", logger="test_os_spec_no_default"
        )
        # MyPy cannot track that configure_default_logger assigns
        # a non-None value to the module-level _default_logger,
        # so cast it to logging.Logger for the type checker.
        logger = cast("logging.Logger", _one_step_module._default_logger)
        assert logger.name == "test_os_spec_no_default"

    @staticmethod
    def test_spec_with_existing_default_logger() -> None:
        """
        When a default logger already exists and a spec is passed,
        a separate logger is created and the default is unchanged.
        """
        configure_default_logger(name="existing_default")
        existing = _one_step_module._default_logger

        log("debug", "separate msg", logger="null")

        # Default logger is unchanged
        assert _one_step_module._default_logger is existing

    @staticmethod
    def test_int_level() -> None:
        """An integer level is accepted without error."""
        log(logging.WARNING, "int level msg")


class TestRecord:
    """Tests for `record` (`sefkhet`-style API)."""

    @staticmethod
    def test_creates_default_logger() -> None:
        """First call creates the default logger."""
        record("msg")
        assert _one_step_module._default_logger is not None

    @staticmethod
    def test_reuses_default_logger() -> None:
        """Subsequent calls reuse the same default logger."""
        record("first")
        first_logger = _one_step_module._default_logger
        record("second")
        assert _one_step_module._default_logger is first_logger

    @staticmethod
    def test_explicit_logger_instance() -> None:
        """Passing a Logger instance uses that logger directly."""
        stream = io.StringIO()
        explicit = logging.getLogger("test_os_rec_explicit_inst")
        explicit.setLevel(logging.DEBUG)
        handler: logging.StreamHandler[io.StringIO] = logging.StreamHandler(
            stream
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        explicit.addHandler(handler)

        record("explicit msg", logger=explicit)

        assert "explicit msg" in stream.getvalue()

    @staticmethod
    def test_spec_with_no_default_logger() -> None:
        """
        When no default logger exists and a spec is passed,
        configure_default_logger(spec=...) is called.
        """
        assert _one_step_module._default_logger is None
        _one_step_module.record("spec msg", logger="test_os_spec_r")
        logger = cast("logging.Logger", _one_step_module._default_logger)
        assert logger.name == "test_os_spec_r"

    @staticmethod
    def test_spec_with_existing_default_logger() -> None:
        """
        When a default logger already exists and a spec is passed,
        a separate logger is created and the default is unchanged.
        """
        configure_default_logger(name="existing_default_r")
        existing = _one_step_module._default_logger

        record("separate msg", logger="null")

        # Default logger is unchanged
        assert _one_step_module._default_logger is existing

    @staticmethod
    def test_quiet_mode_asserts_debug_level() -> None:
        """quiet=True forces the record level to DEBUG."""
        captured: list[logging.LogRecord] = []

        class _CaptureHandler(logging.Handler):
            def emit(  # ruff: ignore[no-self-use]
                self, record: logging.LogRecord
            ) -> None:
                captured.append(record)

        handler = _CaptureHandler()
        handler.setLevel(logging.DEBUG)
        logger = logging.getLogger("test_os_quiet_level")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        record("quiet msg", level="critical", quiet=True, logger=logger)
        assert len(captured) == 1
        assert captured[0].levelno == logging.DEBUG

    @staticmethod
    def test_explicit_level() -> None:
        """An explicit level kwarg is accepted without error."""
        record("info msg", level="info")

    @staticmethod
    def test_args_interpolation() -> None:
        """record() passes *args through for message formatting."""
        stream = io.StringIO()
        logger = logging.getLogger("test_os_args_interp")
        logger.setLevel(logging.DEBUG)
        handler: logging.StreamHandler[io.StringIO] = logging.StreamHandler(
            stream
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        record("count=%d", 5, logger=logger)
        assert "count=5" in stream.getvalue()


class TestRec:  # pylint: disable=too-few-public-methods
    """Tests for `rec` (alias for `record`)."""

    @staticmethod
    def test_rec_is_alias() -> None:
        """rec() delegates to record() without error."""
        rec("msg")


class TestConfigureDefaultLoggerColor:
    """Tests for the `color` parameter of `configure_default_logger`."""

    @staticmethod
    def test_color_full_uses_color_formatter() -> None:
        """color='full' creates a ColorFormatter on the handler."""
        configure_default_logger(color="full")
        logger = _one_step_module._default_logger
        assert logger is not None
        assert len(logger.handlers) >= 1
        assert isinstance(logger.handlers[-1].formatter, ColorFormatter)

    @staticmethod
    def test_tuple_color_creates_color_formatter() -> None:
        """Tuple color with callable creates a ColorFormatter."""
        configure_default_logger(color=("full", lambda _: "\033[99m"))
        logger = _one_step_module._default_logger
        assert logger is not None
        assert len(logger.handlers) >= 1
        assert isinstance(logger.handlers[-1].formatter, ColorFormatter)


class TestConcurrentRecord:  # pylint: disable=too-few-public-methods
    """Tests for concurrent record() when _default_logger is None."""

    @staticmethod
    def test_concurrent_record_no_exceptions() -> None:
        """Concurrent record() calls do not raise exceptions."""
        errors: list[Exception] = []

        def _log(i: int) -> None:
            try:
                record(f"concurrent msg {i}")
            except Exception as exc:  # ruff: ignore[blind-except] # pragma: no cover
                errors.append(exc)

        threads = [threading.Thread(target=_log, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert _one_step_module._default_logger is not None


class TestConcurrentConfigureDefaultLogger:
    """Tests for concurrent configure_default_logger."""

    @staticmethod
    def test_concurrent_configure_force() -> None:
        """20 threads calling configure with force=True."""
        errors: list[Exception] = []

        def _configure(i: int) -> None:
            try:
                configure_default_logger(name=f"concurrent_{i}", force=True)
            except Exception as exc:  # ruff: ignore[blind-except] # pragma: no cover
                errors.append(exc)

        threads = [
            threading.Thread(target=_configure, args=(i,)) for i in range(20)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert _one_step_module._default_logger is not None

    @staticmethod
    def test_concurrent_configure_and_record() -> None:
        """Mixed threads: some configure, others record."""
        errors: list[Exception] = []

        def _configure() -> None:
            try:
                configure_default_logger()
            except Exception as exc:  # ruff: ignore[blind-except] # pragma: no cover
                errors.append(exc)

        def _rec(i: int) -> None:
            try:
                record(f"msg {i}")
            except Exception as exc:  # ruff: ignore[blind-except] # pragma: no cover
                errors.append(exc)

        threads: list[threading.Thread] = []
        for i in range(20):
            if i % 2 == 0:
                threads.append(threading.Thread(target=_configure))
            else:
                threads.append(threading.Thread(target=_rec, args=(i,)))
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert _one_step_module._default_logger is not None

    @staticmethod
    def test_concurrent_record_interleaved() -> None:
        """20 threads each call record() 50 times."""
        errors: list[Exception] = []

        def _rec(tid: int) -> None:
            try:
                for j in range(50):
                    record(f"t{tid}-m{j}")
            except Exception as exc:  # ruff: ignore[blind-except] # pragma: no cover
                errors.append(exc)

        threads = [threading.Thread(target=_rec, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert _one_step_module._default_logger is not None


class TestConfigureDefaultLoggerIdempotency:
    """Tests for configure_default_logger idempotency."""

    @staticmethod
    def test_second_call_without_force_is_noop() -> None:
        """Second call without force keeps the first logger."""
        configure_default_logger(level=logging.DEBUG)
        logger = _one_step_module._default_logger
        assert logger is not None
        assert logger.level == logging.DEBUG

        configure_default_logger(level=logging.ERROR)
        assert _one_step_module._default_logger is logger
        assert logger.level == logging.DEBUG

    @staticmethod
    def test_second_call_with_force_replaces() -> None:
        """force=True replaces the logger with new config."""
        configure_default_logger(level=logging.DEBUG)
        configure_default_logger(level=logging.ERROR, force=True)
        logger = _one_step_module._default_logger
        assert logger is not None
        assert logger.level == logging.ERROR

    @staticmethod
    def test_force_with_different_name_creates_new_logger() -> None:
        """force=True with a new name creates a separate logger."""
        configure_default_logger(name="idem_first")
        configure_default_logger(name="idem_second", force=True)
        logger = _one_step_module._default_logger
        assert logger is not None
        assert logger.name == "idem_second"
        assert len(logger.handlers) == 1
