"""One-step logging interface for `snaplog`."""

import logging
import threading
from collections.abc import Sequence
from typing import Any

from snaplog._functional import (
    _parse_log_level,  # pyright: ignore[reportPrivateUsage]
    get_formatter,
    get_handler,
    get_logger,
    get_logger_from_spec,
)
from snaplog._typing import (
    NoDefault,
    _FilterSpec,  # pyright: ignore[reportPrivateUsage]
    _FormatterSpec,  # pyright: ignore[reportPrivateUsage]
    _HandlerSpec,  # pyright: ignore[reportPrivateUsage]
    _LoggerSpec,  # pyright: ignore[reportPrivateUsage]
    _NoDefaultType,  # pyright: ignore[reportPrivateUsage]
)


# Define a default logger instance that we can use
# for log function calls if a logger is not provided
_default_logger: logging.Logger | None = None

# Create thread lock to use when instantiating default logger
_lock = threading.Lock()


def configure_default_logger(  # noqa: PLR0913
    name: str | _NoDefaultType | None = NoDefault,
    level: int | _NoDefaultType = NoDefault,
    *,
    handlers: _HandlerSpec
    | Sequence[_HandlerSpec]
    | _NoDefaultType = NoDefault,
    formatter: _FormatterSpec | _NoDefaultType = NoDefault,
    filters: _FilterSpec | Sequence[_FilterSpec] | _NoDefaultType = NoDefault,
    spec: _LoggerSpec | _NoDefaultType = NoDefault,
    force: bool = False,
) -> None:
    """
    Configures the default logger used by `snaplog`.

    Args:
        name (str | _NoDefaultType|  None, optional): Name to assign to
            default logger. If `NoDefault`, uses `"snaplogger"`.
            Defaults to `NoDefault`.
        level (int | _NoDefaultType, optional): Logging level to assign
            to default logger and/or handler. If `NoDefault`, uses `20`.
            Defaults to `NoDefault`.
        handlers (_HandlerSpec | Sequence[_HandlerSpec] | _NoDefaultType, optional):
            Specification of any `logging.Handler`s to add to the
            default logger. Multiple handlers can be specified by
            providing a sequence of handler specifications.
            Specification of each handler is similar to when using the
            `snaplog.get_handler` interface, except if using keyword
            arguments, they must be wrapped into a `dict` and provided
            as the second item of a `tuple`, where the first item is the
            argument for `core`. If `NoDefault`, then
            `snaplog.get_handler` is called and its result used as
            `handlers`. Defaults to `NoDefault`.
        formatter (_FormatterSpec | _NoDefaultType, optional):
            Specification of a `logging.Formatter` to add to all
            handlers created for the logger that do not have an
            alternative formatter specified. If `NoDefault`, then
            `snaplog.get_formatter` is called and its result used as
            `formatter`. Defaults to `NoDefault`.
        filters (_FilterSpec | Sequence[_FilterSpec] | _NoDefaultType, optional):
            Specification of any `logging.Filter`s to add to the logger.
            Multiple filters can be specified by providing a sequence of
            filter specifications. Specification of each filter is the
            same as when using the `snaplog.get_handler` inteface. If
            `NoDefault`, then `snaplog.get_filter` is called and its
            result used as `filters`. Defaults to `NoDefault`.
        spec (_LoggerSpec | _NoDefaultType, optional): If not
            `NoDefault` and all other arguments are `NoDefault`, then
            the logger is created according to `spec`; otherwise, this
            parameter is ignored. Defaults to `NoDefault`.
        force (bool, optional): If `True`, the default logger will be
            reconfigured if it has already been configured; otherwise,
            the default logger will not be reconfigured. Ignored if the
            default logger has not already been configured.
            Defaults to `False`.
    """  # noqa: E501,W505
    # Make sure function operates on the module-level default logger
    global _default_logger  # noqa: PLW0603

    # Skip if default logger is already configured and force is false
    if _default_logger is not None and not force:
        return

    # If all but spec are defaults, use spec
    if all(
        isinstance(param, _NoDefaultType)
        for param in (name, level, handlers, formatter, filters)
    ) and not isinstance(spec, _NoDefaultType):
        # Use thread lock to ensure only one default logger gets made
        with _lock:
            _default_logger = get_logger_from_spec(spec=spec)

    # Set arguments to snaplog defaults if not given
    name = "snaplogger" if isinstance(name, _NoDefaultType) else name
    level = 20 if isinstance(level, _NoDefaultType) else level
    handlers = (
        get_handler(level=level)
        if isinstance(handlers, _NoDefaultType)
        else handlers
    )
    formatter = (
        get_formatter() if isinstance(formatter, _NoDefaultType) else formatter
    )
    filters = () if isinstance(filters, _NoDefaultType) else filters

    # Configure default logger,
    # and use thread lock to ensure only one default logger gets made
    with _lock:
        _default_logger = get_logger(
            name=name,
            level=level,
            handlers=handlers,
            formatter=formatter,
            filters=filters,
        )


def log(
    msg: object,
    *args: Any,
    level: str | int = "debug",
    quiet: bool = False,
    logger: logging.Logger | _LoggerSpec | _NoDefaultType = NoDefault,
    **kwargs: Any,
) -> None:
    """
    Log a message using the default or a provided logger.

    *Note that this function's API differs from that of the
    `logging.Logger`'s `log` method: this function requires that
    `level` be provided as a keyword argument instead of as the
    first positional argument, and the `quiet` keyword argument
    is added. A logger to use can also be specified using either a
    `logging.Logger` instance or a logger specification.*

    Args:
        msg (object): Message to log
        *args (Any): Arguments other than `msg` to pass to the
            `loggingLogger`'s `log` method. This might be used to
            provide variables to interpolate into `msg`.
        level (str | int, optional): Logging level to log message at.
            Valid log levels include a log level string from the options
            provided by `snaplog.get_log_levels()`, the `int`
            equivalents of those log levels as defined by the `logging`
            library, or any other `int`. Overriden by the `quiet`
            argument if it is `True`. Defaults to `"debug"`.
        quiet (bool, optional): If `True`, forces the log to the
            `logging.DEBUG` level; otherwise, the `level` argument sets
            the log level. Defaults to `False`.
        logger (logging.Logger | _LoggerSpec | _NoDefaultType, optional):
            Specification of the `logging.Logger` to use to log the
            message. If a `logging.Logger`, then that logger will be
            used; if the `snaplog` default logger is still `None` at the
            time of calling, the default logger will be instantiated
            using `logger` as the `spec` argument to
            `configure_default_logger`, which uses the default
            configuration if `logger` is `NoDefault`; if `NoDefault`,
            the default logger will be used, and it will be instantiated
            with the defaults if it has not been already; and if the
            default logger has already been instantiated but `logger`
            is a `_LoggerSpec`, a separate logger will be created
            according to the specification and used to log the message.
            Defaults to `NoDefault`.
        **kwargs (Any): Keyword arguments to pass to the
            `logging.Logger`'s `log` method. This might be used to pass
            exception information.
    """  # noqa: W505
    # Decide which logger to use if none given
    if not isinstance(logger, logging.Logger):
        # Use default logger if no spec provided
        if isinstance(logger, _NoDefaultType):
            # Make sure default logger is instantiated
            configure_default_logger()
            logger = _default_logger
        # If no logger given and default logger is still None,
        # configure default logger using provided spec
        elif _default_logger is None:
            configure_default_logger(spec=logger)
            logger = _default_logger
        # Otherwise, create separate logger using spec
        else:
            logger = get_logger_from_spec(logger)

    # Parse provided level
    level = _parse_log_level(level=level, quiet=quiet)

    # Log to indicated level
    logger.log(  # pyright: ignore[reportOptionalMemberAccess]
        level, msg, *args, **kwargs
    )
