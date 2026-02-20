"""Tests for `snaplog._one_step`."""

import io
import logging
from typing import cast

import snaplog._one_step as _one_step_module
from snaplog._color import ColorFormatter
from snaplog._one_step import configure_default_logger, log


class TestConfigureDefaultLogger:
    """Tests for `configure_default_logger`."""

    @staticmethod
    def test_default_call_creates_snaplogger() -> None:
        """
        Calling with all defaults creates a logger named 'snaplogger'.
        """  # noqa: D200
        configure_default_logger()
        assert _one_step_module._default_logger is not None
        assert _one_step_module._default_logger.name == "snaplogger"

    @staticmethod
    def test_explicit_name() -> None:
        """Passing name= uses that name instead of 'snaplogger'."""
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
        (not all params are NoDefault) and spec is ignored.
        """
        configure_default_logger(name="explicit_name", spec="ignored_spec")
        logger = _one_step_module._default_logger
        assert logger is not None
        assert logger.name == "explicit_name"


class TestLog:
    """Tests for `log`."""

    @staticmethod
    def test_logger_nodefault_creates_default() -> None:
        """First call with no logger creates the default logger."""
        log("msg")
        assert _one_step_module._default_logger is not None

    @staticmethod
    def test_logger_nodefault_reuses_default() -> None:
        """Subsequent calls reuse the same default logger."""
        log("first")
        first_logger = _one_step_module._default_logger
        log("second")
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

        log("explicit msg", logger=explicit)

        assert "explicit msg" in stream.getvalue()

    @staticmethod
    def test_spec_with_no_default_logger() -> None:
        """
        When no default logger exists and a spec is passed,
        configure_default_logger(spec=...) is called.
        """
        assert _one_step_module._default_logger is None
        _one_step_module.log("spec msg", logger="test_os_spec_no_default")
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

        log("separate msg", logger="null")

        # Default logger is unchanged
        assert _one_step_module._default_logger is existing

    @staticmethod
    def test_quiet_mode() -> None:
        """quiet=True logs at DEBUG without error."""
        log("quiet msg", level="critical", quiet=True)

    @staticmethod
    def test_int_level() -> None:
        """An integer level is accepted without error."""
        log("int level msg", level=logging.WARNING)


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
