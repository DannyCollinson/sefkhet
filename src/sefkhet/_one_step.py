"""One-step logging interface for `sefkhet`."""

import logging as _logging
import threading as _threading
from typing import TYPE_CHECKING as _TYPE_CHECKING

from sefkhet._typing import NoDefault


if _TYPE_CHECKING:  # pragma: no cover
    import logging
    from collections.abc import Mapping, Sequence
    from typing import Any

    from sefkhet._typing import (
        ColorSpec,
        CsvSpec,
        ExcInfoType,
        FilterSpec,
        FormatterSpec,
        HandlerSpec,
        JsonSpec,
        LogfmtSpec,
        LoggerSpec,
        NoDefaultType,
    )


type _HandlersArgType = HandlerSpec | Sequence[HandlerSpec] | NoDefaultType
type _FiltersArgType = FilterSpec | Sequence[FilterSpec] | NoDefaultType

# Define a default logger instance that we can use
# for log function calls if a logger is not provided
_default_logger: _logging.Logger | None = None

# Create thread lock to use when instantiating default logger
_lock = _threading.Lock()


def configure_default_logger(  # ruff: ignore[too-many-arguments]
    name: "str | NoDefaultType | None" = NoDefault,
    level: "int | NoDefaultType" = NoDefault,
    *,
    handlers: "_HandlersArgType" = NoDefault,
    formatter: "FormatterSpec | NoDefaultType" = NoDefault,
    filters: "_FiltersArgType" = NoDefault,
    spec: "LoggerSpec | NoDefaultType" = NoDefault,
    force: bool = False,
    color: "ColorSpec" = "level",
    json: "bool | JsonSpec" = False,
    csv: "bool | CsvSpec" = False,
    logfmt: "bool | LogfmtSpec" = False,
) -> None:
    """
    Configures the default logger used by `sefkhet`.

    Args:
        name (str | NoDefaultType | None, optional): Name to
            assign to default logger. If `NoDefault`, uses
            `"scribe"`. Defaults to `NoDefault`.
        level (int | NoDefaultType, optional): Logging level
            to assign to default logger and/or handler. If
            `NoDefault`, uses `20`.
            Defaults to `NoDefault`.
        handlers (_HandlersArgType, optional): Specification of any
            `logging.Handler`s to add to the default logger. Multiple
            handlers can be specified by providing a sequence of handler
            specifications. Specification of each handler is similar to
            when using the `sefkhet.get_handler` interface, except if
            using keyword arguments, they must be wrapped into a `dict`
            and provided as the second item of a `tuple`, where the
            first item is the argument for `core`. If `NoDefault`, then
            `sefkhet.get_handler` is called and its result used
            as `handlers`. Defaults to `NoDefault`.
        formatter (FormatterSpec | NoDefaultType, optional):
            Specification of a `logging.Formatter` to add to
            all handlers created for the logger that do not
            have an alternative formatter specified. If
            `NoDefault`, then `sefkhet.get_formatter` is
            called and its result used as `formatter`.
            Defaults to `NoDefault`.
        filters (_FiltersArgType, default=NoDefault): Specification of
            any `logging.Filter`s to add to the logger. Multiple filters
            can be specified by providing a sequence of filter
            specifications. Specification of each filter is the same as
            when using the `sefkhet.get_handler` inteface. If
            `NoDefault`, then `sefkhet.get_filter` is called and its
            result used as `filters`. Defaults to `NoDefault`.
        spec (LoggerSpec | NoDefaultType, optional): If not
            `NoDefault` and all other arguments are
            `NoDefault`, then the logger is created according
            to `spec`; otherwise, this parameter is ignored.
            Defaults to `NoDefault`.
        force (bool, optional): If `True`, the default logger
            will be reconfigured if it has already been
            configured; otherwise, the default logger will not
            be reconfigured. Ignored if the default logger has
            not already been configured. Defaults to `False`.
        color (ColorSpec, optional): Color mode for the
            formatter. Either a bare `ColorMode` string or a
            tuple of `(ColorMode, colormap)` for per-level
            color overrides. Passed through to `get_logger` in
            the non-spec path. Ignored if `csv`, `json`, or
            `logfmt` is not `False`. Defaults to `"level"`.
        json (bool | JsonSpec, optional): JSON output mode.
            If not `False`, a `JsonFormatter` is used and
            `color` is ignored. Passed through to `get_logger`
            in the non-spec path. Ignored if `csv` is not
            `False`. Defaults to `False`.
        csv (bool | CsvSpec, optional): CSV output mode. If
            not `False`, a `CsvFormatter` is used and `json`,
            `logfmt`, and `color` are ignored. Passed through
            to `get_logger` in the non-spec path.
            Defaults to `False`.
        logfmt (bool | LogfmtSpec, optional): Logfmt output
            mode. If not `False`, a `LogfmtFormatter` is used
            and `color` is ignored. Passed through to
            `get_logger` in the non-spec path. Ignored if
            `csv` or `json` is not `False`.
            Defaults to `False`.
    """
    from sefkhet._functional import (
        _get_default_fmt,
        get_formatter,
        get_handler,
        get_logger,
        get_logger_from_spec,
    )
    from sefkhet._typing import NoDefaultType

    # Make sure function operates on the module-level default logger
    global _default_logger  # ruff: ignore[global-statement]

    # Fast-path: skip if default logger is already configured and
    # force is false.
    if _default_logger is not None and not force:
        return

    # If all but spec are defaults, use spec
    if all(
        isinstance(param, NoDefaultType)
        for param in (name, level, handlers, formatter, filters)
    ) and not isinstance(spec, NoDefaultType):
        # Use thread lock to ensure only one default logger gets made
        with _lock:
            # Double-check inside the lock to avoid redundant creation
            if _default_logger is not None and not force:  # pragma: no cover
                return
            _default_logger = get_logger_from_spec(spec=spec)
        return

    # Set arguments to sefkhet defaults if not given
    name = "scribe" if isinstance(name, NoDefaultType) else name
    level = 20 if isinstance(level, NoDefaultType) else level
    handlers = (
        get_handler(level=level)
        if isinstance(handlers, NoDefaultType)
        else handlers
    )
    formatter = (
        get_formatter(
            fmt=_get_default_fmt(name),
            color=color,
            json=json,
            csv=csv,
            logfmt=logfmt,
        )
        if isinstance(formatter, NoDefaultType)
        else formatter
    )
    filters = () if isinstance(filters, NoDefaultType) else filters

    # Configure default logger,
    # and use thread lock to ensure only one default logger gets made
    with _lock:
        # Double-check inside the lock to avoid redundant creation
        if _default_logger is not None and not force:  # pragma: no cover
            return
        _default_logger = get_logger(
            name=name,
            level=level,
            handlers=handlers,
            formatter=formatter,
            filters=filters,
            color=color,
            json=json,
            csv=csv,
            logfmt=logfmt,
        )


def log(  # ruff: ignore[too-many-arguments]
    level: int | str,
    msg: object,
    *args: "Any",
    exc_info: "ExcInfoType" = None,
    stack_info: bool = False,
    stacklevel: int = 1,
    extra: "Mapping[str, object] | None" = None,
    logger: "logging.Logger | LoggerSpec | NoDefaultType" = NoDefault,
) -> None:
    """
    Log a message according to the `logging.log` API
    using the default or a provided logger.

    *A logger to use can also be specified using either a
    `logging.Logger` instance or a logger specification.*

    Args:
        level (int | str): Logging level to log message at. Valid log
            levels include a log level string from the options provided
            by `sefkhet.get_log_levels()`, the `int` equivalents of
            those log levels as defined by the `logging`library, or any
            other `int`.
        msg (object): Message to log
        *args (Any): Arguments other than `msg` to pass to the
            `loggingLogger`'s `log` method. This might be used to
            provide variables to interpolate into `msg`.
        exc_info (ExcInfoType, optional): See `logging.Logger`'s
            method `log` for details. Defaults to `None`.
        stack_info (bool, optional): See `logging.Logger`'s
            method `log` for details. Defaults to `False`.
        stacklevel (int, optional): See `logging.Logger`'s
            method `log` for details. Defaults to `1`.
        extra (Mapping[str, object] | None, optional): See
            `logging.Logger`'s method `log` for details.
            Defaults to `None`.
        logger (_LoggerArgType, default=NoDefault): Specification of
            the `logging.Logger` to use to log the message. If a
            `logging.Logger`, then that logger will be used; if the
            `sefkhet` default logger is still `None` at the time of
            calling, the default logger will be instantiated using
            `logger` as the `spec` argument to
            `configure_default_logger`, which uses the default
            configuration if `logger` is `NoDefault`; if `NoDefault`,
            the default logger will be used, and it will be instantiated
            with the defaults if it has not been already; and if the
            default logger has already been instantiated but `logger`
            is a `LoggerSpec`, a separate logger will be created
            according to the specification and used to log the message.
            Defaults to `NoDefault`.
    """
    from sefkhet._functional import _parse_log_level, get_logger_from_spec
    from sefkhet._typing import NoDefaultType

    # Decide which logger to use if none given
    if not isinstance(logger, _logging.Logger):
        # Use default logger if no spec provided
        if isinstance(logger, NoDefaultType):
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
    level = _parse_log_level(level=level, quiet=False)

    # Log to indicated level
    logger.log(  # type: ignore[union-attr] # pyright: ignore[reportOptionalMemberAccess]
        level,
        msg,
        *args,
        exc_info=exc_info,
        stack_info=stack_info,
        stacklevel=stacklevel,
        extra=extra,
    )


def record(  # ruff: ignore[too-many-arguments]
    msg: object,
    *args: "Any",
    level: str | int = "debug",
    quiet: bool = False,
    logger: "logging.Logger | LoggerSpec | NoDefaultType" = NoDefault,
    exc_info: "ExcInfoType" = None,
    stack_info: bool = False,
    stacklevel: int = 1,
    extra: "Mapping[str, object] | None" = None,
) -> None:
    """
    Log a message according to the `sefkhet` API
    using the default or a provided logger.

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
            provided by `sefkhet.get_log_levels()`, the `int`
            equivalents of those log levels as defined by the `logging`
            library, or any other `int`. Overriden by the `quiet`
            argument if it is `True`. Defaults to `"debug"`.
        quiet (bool, optional): If `True`, forces the log to the
            `logging.DEBUG` level; otherwise, the `level` argument sets
            the log level. Defaults to `False`.
        logger (_LoggerArgType, default=NoDefault): Specification of
            the `logging.Logger` to use to log the message. If a
            `logging.Logger`, then that logger will be used; if the
            `sefkhet` default logger is still `None` at the time of
            calling, the default logger will be instantiated using
            `logger` as the `spec` argument to
            `configure_default_logger`, which uses the default
            configuration if `logger` is `NoDefault`; if `NoDefault`,
            the default logger will be used, and it will be instantiated
            with the defaults if it has not been already; and if the
            default logger has already been instantiated but `logger`
            is a `LoggerSpec`, a separate logger will be created
            according to the specification and used to log the message.
            Defaults to `NoDefault`.
        exc_info (ExcInfoType, optional): See `logging.Logger`'s
            method `log` for details. Defaults to `None`.
        stack_info (bool, optional): See `logging.Logger`'s
            method `log` for details. Defaults to `False`.
        stacklevel (int, optional): See `logging.Logger`'s
            method `log` for details. Defaults to `1`.
        extra (Mapping[str, object] | None, optional): See
            `logging.Logger`'s method `log` for details.
            Defaults to `None`.
    """
    from sefkhet._functional import _parse_log_level

    # Parse provided level
    level = _parse_log_level(level=level, quiet=quiet)
    # Delegate to log function
    log(
        level,
        msg,
        *args,
        exc_info=exc_info,
        stack_info=stack_info,
        stacklevel=stacklevel,
        extra=extra,
        logger=logger,
    )


def rec(  # ruff: ignore[too-many-arguments]
    msg: object,
    *args: "Any",
    level: str | int = "debug",
    quiet: bool = False,
    exc_info: "ExcInfoType" = None,
    stack_info: bool = False,
    stacklevel: int = 1,
    extra: "Mapping[str, object] | None" = None,
    logger: "logging.Logger | LoggerSpec | NoDefaultType" = NoDefault,
) -> None:
    """
    Log a message according to the `sefkhet` API
    using the default or a provided logger.

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
            provided by `sefkhet.get_log_levels()`, the `int`
            equivalents of those log levels as defined by the `logging`
            library, or any other `int`. Overriden by the `quiet`
            argument if it is `True`. Defaults to `"debug"`.
        quiet (bool, optional): If `True`, forces the log to the
            `logging.DEBUG` level; otherwise, the `level` argument sets
            the log level. Defaults to `False`.
        exc_info (ExcInfoType, optional): See `logging.Logger`'s
            method `log` for details. Defaults to `None`.
        stack_info (bool, optional): See `logging.Logger`'s
            method `log` for details. Defaults to `False`.
        stacklevel (int, optional): See `logging.Logger`'s
            method `log` for details. Defaults to `1`.
        extra (Mapping[str, object] | None, optional): See
            `logging.Logger`'s method `log` for details.
            Defaults to `None`.
        logger (_LoggerArgType, default=NoDefault): Specification of
            the `logging.Logger` to use to log the message. If a
            `logging.Logger`, then that logger will be used; if the
            `sefkhet` default logger is still `None` at the time of
            calling, the default logger will be instantiated using
            `logger` as the `spec` argument to
            `configure_default_logger`, which uses the default
            configuration if `logger` is `NoDefault`; if `NoDefault`,
            the default logger will be used, and it will be instantiated
            with the defaults if it has not been already; and if the
            default logger has already been instantiated but `logger`
            is a `LoggerSpec`, a separate logger will be created
            according to the specification and used to log the message.
            Defaults to `NoDefault`.
    """
    record(
        msg,
        *args,
        level=level,
        quiet=quiet,
        exc_info=exc_info,
        stack_info=stack_info,
        stacklevel=stacklevel,
        extra=extra,
        logger=logger,
    )
