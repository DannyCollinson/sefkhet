"""Shared fixtures for `snaplog` tests."""

import io
import logging
from collections.abc import Generator
from typing import Any

import pytest

import snaplog._one_step as _one_step_module
from snaplog._object_oriented import SnapLogger
from snaplog._typing import _SupportsFilter


# Global-state isolation (autouse)


@pytest.fixture(autouse=True)
def isolated_logging() -> Generator[None]:
    """
    Snapshot and restore the logging manager's logger
    registry around each test.

    Closes all handlers, clears filters, and removes any
    loggers added during the test. Also cleans up any
    root-logger handlers added during the test.
    """
    # Snapshot existing logger names and root handler count
    pre_names: set[str] = set(logging.Logger.manager.loggerDict.keys())
    pre_root_handlers = list(logging.root.handlers)

    yield

    # Remove loggers created during the test
    post_names: set[str] = set(logging.Logger.manager.loggerDict.keys())
    for name in post_names - pre_names:
        entry = logging.Logger.manager.loggerDict.get(name)
        if isinstance(entry, logging.Logger):  # pragma: no branch
            for hdlr in entry.handlers[:]:
                hdlr.close()
                entry.removeHandler(hdlr)
            entry.filters.clear()
        logging.Logger.manager.loggerDict.pop(name, None)

    # Restore root-logger handlers
    for hdlr in logging.root.handlers[:]:
        if hdlr not in pre_root_handlers:
            hdlr.close()
            logging.root.removeHandler(hdlr)
    logging.root.filters.clear()


@pytest.fixture(autouse=True)
def reset_default_logger() -> Generator[None]:
    """Reset `_one_step._default_logger` to `None` around each test."""
    original = _one_step_module._default_logger
    _one_step_module._default_logger = None
    yield
    _one_step_module._default_logger = original


@pytest.fixture(autouse=True)
def reset_snap_counter() -> Generator[None]:
    """Reset `SnapLogger._counter` to `0` around each test."""
    original = SnapLogger._counter
    SnapLogger._counter = 0
    yield
    SnapLogger._counter = original


# Helper fixtures


@pytest.fixture
def null_handler() -> logging.NullHandler:
    """
    Returns a fresh `logging.NullHandler`.

    Returns:
        logging.NullHandler: A fresh `logging.NullHandler`
    """
    return logging.NullHandler()


@pytest.fixture
def string_io_stream() -> io.StringIO:
    """
    Returns a fresh `io.StringIO` stream.

    Returns:
        io.StringIO: A fresh `io.StringIO` stream
    """
    return io.StringIO()


@pytest.fixture
def capturing_handler(  # pragma: no cover
    string_io_stream: io.StringIO,
) -> logging.StreamHandler[Any]:
    """
    Returns a `StreamHandler` pointed at a `StringIO`, level DEBUG.

    Args:
        string_io_stream (io.StringIO): Stream to log to

    Returns:
        logging.StreamHandler[Any]: A `StreamHandler` pointed at a
            `StringIO`, level DEBUG
    """
    handler: logging.StreamHandler[io.StringIO] = logging.StreamHandler(
        string_io_stream
    )
    handler.setLevel(logging.DEBUG)
    return handler


@pytest.fixture
def simple_formatter() -> logging.Formatter:
    """
    Returns a `logging.Formatter` with format `%(message)s`.

    Returns:
        logging.Formatter: A `logging.Formatter` with
            format `%(message)s`
    """
    return logging.Formatter("%(message)s")


@pytest.fixture
def simple_filter() -> logging.Filter:
    """
    Returns a `logging.Filter` with name `"test"`.

    Returns:
        logging.Filter: A `logging.Filter` with name `"test"`
    """
    return logging.Filter("test")


@pytest.fixture
def named_handler() -> Generator[tuple[logging.NullHandler, str]]:
    """
    Yield a `(NullHandler, name)` pair.

    The handler is registered by name so that
    `logging.getHandlerByName` can find it.
    The generator frame keeps the handler alive in the
    `WeakValueDictionary` used by `logging`.

    Yields:
        Generator[tuple[logging.NullHandler, str]]: A
            `(NullHandler, name)` pair
    """
    name = "test_named_handler_fixture"
    hdlr = logging.NullHandler()
    hdlr.set_name(name)
    yield hdlr, name  # noqa: PT022


@pytest.fixture
def callable_filter() -> logging.Filterer:  # pragma: no cover
    """
    Return a plain callable that acts as a filter.

    `callable(result)` is `True`; it is NOT a `logging.Filter`.
    Used to exercise the `callable(filters)` branch of
    `_parse_filters_arg`.

    Returns:
        logging.Filterer: A `Callable` that always returns `True`
    """

    # Return as Any so callers can pass it where _FilterSpec is expected
    def _filt(record: logging.LogRecord) -> bool:
        return True

    return _filt  # type: ignore[return-value]  # pyright: ignore[reportReturnType]


@pytest.fixture
def protocol_filter() -> _SupportsFilter:
    """
    Return an object satisfying `_SupportsFilter` that is NOT callable.

    `callable(result)` is `False`; `isinstance(result, _SupportsFilter)`
    is `True`. Used to exercise the `isinstance(_, _SupportsFilter)`
    branch of `_parse_filters_arg` when `callable()` is `False`.

    Returns:
        _SupportsFilter: A class instance satisfying `_SupportsFilter`
            that is NOT callable
    """

    class _ProtocolOnlyFilter:  # pylint: disable=too-few-public-methods
        def filter(  # noqa: PLR6301
            self, record: logging.LogRecord, /
        ) -> bool | logging.LogRecord:
            return True  # pragma: no cover

    return _ProtocolOnlyFilter()


@pytest.fixture
def log_file(tmp_path: pytest.TempPathFactory) -> str:
    """
    Return a path string for a temp log file.

    Args:
        tmp_path (pytest.TempPathFactory): Pytest fixture

    Returns:
        str: Path string for temporary log file
    """
    return str(
        tmp_path / "test.log"  # type: ignore[operator] # pyright: ignore[reportOperatorIssue,reportUnknownArgumentType]
    )
