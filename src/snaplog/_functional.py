"""Functional interface for `snaplog`."""

import logging
import os
import sys
from collections.abc import Mapping, Sequence
from copy import deepcopy
from io import TextIOBase
from pathlib import Path
from typing import Any, TextIO

from snaplog._color import (  # pyright: ignore[reportPrivateUsage]
    ColorFormatter,
)
from snaplog._typing import (
    NoDefault,
    _ColorMode,  # pyright: ignore[reportPrivateUsage]
    _FileHandlerKwargs,
    _FilterSpec,
    _FormatStyle,
    _FormatterSpec,
    _HandlerSpec,
    _LoggerKwargs,
    _LoggerSpec,
    _NoDefaultType,
    _StrOrPathLike,
    _SupportsFilter,
    _TextIOLike,
)


########################################################################
# Constants and helpers
########################################################################


# Define log level mapping for log functions
LOG_LEVEL_STR_TO_INT: dict[str, int] = {
    "debug": logging.DEBUG,
    "d": logging.DEBUG,
    "info": logging.INFO,
    "i": logging.INFO,
    "warning": logging.WARNING,
    "warn": logging.WARNING,
    "w": logging.WARNING,
    "error": logging.ERROR,
    "e": logging.ERROR,
    "exception": logging.ERROR,
    "x": logging.ERROR,
    "critical": logging.CRITICAL,
    "c": logging.CRITICAL,
    "fatal": logging.FATAL,
    "f": logging.FATAL,
    "notset": logging.NOTSET,
    "not_set": logging.NOTSET,
    "n": logging.NOTSET,
    "DEBUG": logging.DEBUG,
    "D": logging.DEBUG,
    "INFO": logging.INFO,
    "I": logging.INFO,
    "WARNING": logging.WARNING,
    "WARN": logging.WARNING,
    "W": logging.WARNING,
    "ERROR": logging.ERROR,
    "E": logging.ERROR,
    "EXCEPTION": logging.ERROR,
    "X": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
    "C": logging.CRITICAL,
    "FATAL": logging.FATAL,
    "F": logging.FATAL,
    "NOTSET": logging.NOTSET,
    "NOT_SET": logging.NOTSET,
    "N": logging.NOTSET,
}


def get_log_level_map() -> dict[str, int]:
    """
    Returns a mapping of all valid log level strings to
    associated integer log levels, including custom log
    levels registered with the `logging` library.

    Returns:
        dict[str, int]: Mapping of all valid log level
            strings to their associated integer log levels
    """
    # Start with snaplog defaults
    valid_levels_map = LOG_LEVEL_STR_TO_INT
    # Add user customizations
    valid_levels_map.update(logging.getLevelNamesMapping())
    return valid_levels_map


def get_log_levels() -> set[str]:
    """
    Returns the set of valid log level strings, including custom
    log levels registered with the `logging` library.

    Returns:
        set[str]: List of valid log level strings
    """
    return set(get_log_level_map())


def _parse_log_level(  # pyright: ignore[reportUnusedFunction]
    level: str | int, *, quiet: bool = False
) -> int:
    """
    Returns the `int` representation of the log level
    specified by `level` and `quiet`.

    Args:
        level (str | int): Logging level to use if `quiet` is `False`.
            Valid log levels include a log level string from the options
            provided by `snaplog.get_log_levels()`, the `int`
            equivalents of those log levels as defined by the `logging`
            library, or any other `int`.
        quiet (bool, optional): If `True`, forces the log level to
            `logging.DEBUG`; otherwise, the `level` argument
            determines the log level. Defaults to `False`.

    Raises:
        ValueError: Raised if `level` is invalid

    Returns:
        int: The `int` representation of the log level specified by
            `level` and `quiet`
    """
    # Get valid log levels mapping
    valid_levels_map = get_log_level_map()

    # Force level to debug if quiet override is true
    level = logging.DEBUG if quiet else level

    # Set log level as integer if not already
    if not isinstance(level, int):
        # Make sure non-integer level is valid
        if level not in valid_levels_map:
            msg = f"Got invalid value for 'level': {level}"
            raise ValueError(msg)
        level = valid_levels_map[level]

    return level


########################################################################
# Functional-style interface
########################################################################


def get_formatter(  # noqa: PLR0913
    fmt: str
    | logging.Formatter
    | None = "%(asctime)s | %(levelname)s | %(message)s",
    *,
    datefmt: str | None = None,
    style: _FormatStyle = "%",
    validate: bool = True,
    defaults: Mapping[str, Any] | None = None,
    copy: bool = False,
    color: _ColorMode | None = None,
) -> logging.Formatter:
    """
    Returns a `logging.Formatter` configured
    according to the provided specifications.

    If `fmt` is a `logging.Formatter` already, a deep copy is returned
    if `copy` is `True` and otherwise the original formatter; if a `str`
    or `None`, a new `logging.Formatter` is constructed, configured
    according to `fmt` and the keyword arguments.

    This function follows the defaults of the `logging.Formatter`
    constructor except for the `fmt` string, which defaults to `None`
    in the `logging.Formatter` constructor but is set to a custom
    string here (`"%(asctime)s | %(levelname)s | %(message)s"`).
    See the `logging.Formatter` class for details about the arguments.

    Args:
        fmt (str | logging.Formatter | None, optional): If a
            `logging.Formatter`, then the formatter to return a copy of;
            otherwise, the format string to pass to the
            `logging.Formatter` constructor.
            Defaults to `"%(asctime)s | %(levelname)s | %(message)s"`.
        datefmt (str | None, optional): Date format string to pass to
            `logging.Formatter` constructor. Ignored if `fmt` is a
            `logging.Formatter`. Defaults to `None`.
        style (_FormatStyle, optional): Style format used by the format
            string. Ignored if `fmt` is a `logging.Formatter`.
            Defaults to `"%"`.
        validate (bool, optional): If `True`, the configuration is
            validated upon creation; otherwise, no validation occurs.
            Ignored if `fmt` is a `logging.Formatter`.
            Defaults to `True`.
        defaults (Mapping[str, Any] | None, optional): Default values
            for string variable interpolation. Ignored if `fmt` is a
            `logging.Formatter`. Defaults to `None`.
        copy (bool, optional): If `True`, returns a deep copy of the
            original instance of `fmt`; otherwise, returns the original
            instance. Ignored if `fmt` is not a `logging.Formatter`.
            Defaults to `False`.
        color (_ColorMode | None, optional): Color mode for the
            formatter. If not `None` and not `"off"`, a
            `ColorFormatter` is returned instead of a plain
            `logging.Formatter`. Ignored if `fmt` is a
            `logging.Formatter`. Defaults to `None`.

    Returns:
        logging.Formatter: The specified `logging.Formatter`
    """
    # Return original or copy of existing formatter if one is passed
    if isinstance(fmt, logging.Formatter):
        return deepcopy(fmt) if copy else fmt
    # Return a ColorFormatter if color mode is active
    if color is not None and color != "off":
        return ColorFormatter(
            fmt=fmt,
            datefmt=datefmt,
            style=style,
            validate=validate,
            defaults=defaults,
            color=color,
        )
    # Otherwise create a new formatter with specified configuration
    return logging.Formatter(
        fmt=fmt,
        datefmt=datefmt,
        style=style,
        validate=validate,
        defaults=defaults,
    )


def get_formatter_from_spec(
    spec: _FormatterSpec,
    *,
    color: _ColorMode | None = None,
) -> logging.Formatter:
    """
    Returns a `logging.Formatter` configured using a `_FormatterSpec`.

    Args:
        spec (_FormatterSpec): Specification of formatter
        color (_ColorMode | None, optional): Color mode for the
            formatter. Passed through to `get_formatter` when the
            dict spec does not already contain a ``"color"`` key.
            Defaults to `None`.

    Returns:
        logging.Formatter: The specified formatter
    """
    # If a dict, specify as keyword arguments
    if isinstance(spec, dict):
        # Dict's own color key takes precedence; only inject if absent
        if "color" not in spec and color is not None:
            return get_formatter(**spec, color=color)  # type: ignore[misc]
        return get_formatter(**spec)
    # If here, just pass spec as main argument
    return get_formatter(fmt=spec, color=color)


def get_filter(
    filt: str | logging.Filter = "", *, copy: bool = False
) -> logging.Filter:
    """
    Returns a `logging.Filter` configured
    according to the provided specifications.

    If `filt` is a `logging.Filter` already, a deep copy is returned if
    `copy` is `True` and otherwise the original filter; otherwise, a
    filter created with the argument `filt` is returned.

    Args:
        filt (str | logging.Filter, optional): Specification of
            the filter
        copy (bool, optional): If `True`, returns a deep copy of the
            original instance of `filt`; otherwise, the original
            instance is returned. Ignored if `fmt` is not a
            `logging.Formatter`. Defaults to `False`.

    Returns:
        logging.Filter: The specified `logging.Filter`
    """
    # Return copy or original if the filter one is passed
    if isinstance(filt, logging.Filter):
        return deepcopy(filt) if copy else filt
    # Otherwise, return a fresh filter
    return logging.Filter(filt)


def get_filter_from_spec(spec: _FilterSpec) -> logging.Filter:
    """
    Returns a `logging.Filter` configured according to `spec`.

    Args:
        spec (_FilterSpec): Specification of filter

    Raises:
        TypeError: Raised if a specification doesn't specify a
            valid `logging.Filter`

    Returns:
        logging.Filter: The specified filter
    """
    # Handle case of single string
    if isinstance(spec, str):
        return get_filter(filt=spec)

    # Handle case of lone filter, adding copy=False as default
    if isinstance(spec, logging.Filter):
        return get_filter(filt=spec, copy=False)

    # Handle case of (filter + copy) tuple
    if (
        isinstance(spec, tuple)
        and len(
            spec  # pyright: ignore[reportUnknownArgumentType]
        )
        == 2  # noqa: PLR2004
        and isinstance(spec[0], logging.Filter)
        and isinstance(spec[1], bool)
    ):
        return get_filter(filt=spec[0], copy=spec[1])

    # If here, couldn't create a valid filter
    msg = (
        "Can't create 'logging.Filter' from provided specification. "
        "Callables and other classes that implement a valid filter "
        f"must be added as a filter directly. Got '{spec}'."
    )
    raise TypeError(msg)


def _maybe_create_special_string_handler(
    core: str, *, copy: bool
) -> logging.Handler | None:
    """
    Returns the `logging.Handler` associated with the
    special string matched by `core`; if `core` does
    not match a special string, returns `None`.

    The special strings and their associated
    `logging.Handler`s are as follows:
      - `"stdout": logging.StreamHandler(stream=sys.stdout)`
      - `"stderr": logging.StreamHandler(stream=sys.stderr)`
      - `"null": logging.NullHandler()`
      - A string matching the name of an existing `logging.Handler`,
        as checked by `logging.getHandlerByName(core)`

    *Note that capitalization variants of the first*
    *three special strings in the list above will*
    *also match the corresponding special string.*

    Args:
        core (str): String to check for matches against special strings
        copy (bool): If `True`, returns a deep copy of the existing
            `logging.Handler` that was matched; otherwise, the original
            instance is returned. Ignored if an existing handler name is
            not matched

    Returns:
        logging.Handler | None: If `core` matches a special string, then
            the associated `logging.Handler`; otherwise, `None`
    """
    # Create placeholder to track if a handler is created
    handler = None

    # Check for existing handler with given name
    existing_handler = logging.getHandlerByName(core)
    if existing_handler is not None:
        handler = deepcopy(existing_handler) if copy else existing_handler

    # Check for StdOut, StdErr, or Null
    elif core.lower() == "stdout":
        handler = logging.StreamHandler(sys.stdout)
    elif core.lower() == "stderr":
        handler = logging.StreamHandler(sys.stderr)
    elif core.lower() == "null":
        handler = logging.NullHandler()

    # Still None if nothing created; otherwise, the created handler
    return handler


def _maybe_create_handler(
    core: _StrOrPathLike | _TextIOLike | logging.Handler | None,
    *,
    file_handler_kwargs: _FileHandlerKwargs,
    copy: bool,
) -> logging.Handler | None:
    """
    Returns a `logging.Handler` if a valid handler is specified;
    otherwise, returns `None`. See `get_handler` for details
    about what makes a valid handler specification.

    Args:
        core (_StrOrPathLike | _TextIOLike | logging.Handler | None):
            Specification of the handler
        file_handler_kwargs (_FileHandlerKwargs): Keyword arguments to
            pass to the `logging.FileHandler` constructor. Ignored if
            not creating a new `logging.FileHandler`.
        copy (bool): If `True`, returns a deep copy of the
            original instance of `core`; otherwise, the original
            instance is returned. Ignored if `core` is not a
            `logging.Handler`. Defaults to `False`.

    Returns:
        logging.Handler | None: If a valid handler was specified, then a
            `logging.Handler`; otherwise, `None`
    """
    # Create placeholder to track if handler is created
    handler: logging.Handler | None = None

    # Handle case when a handler is provided
    if isinstance(core, logging.Handler):
        handler = deepcopy(core) if copy else core

    # Handle default case of None using default stderr stream handler
    if core is None:
        handler = logging.StreamHandler(stream=sys.stderr)

    # Handle cases of special strings
    if isinstance(core, str):
        handler = _maybe_create_special_string_handler(core=core, copy=copy)

    # Handle case of pathlike
    if handler is None and isinstance(core, (str, os.PathLike)):
        handler = logging.FileHandler(  # pylint: disable=R0204
            filename=Path(os.fsdecode(core)).resolve(), **file_handler_kwargs
        )

    # Handle case of TextIO-like
    if isinstance(core, (TextIO, TextIOBase)):
        handler = logging.StreamHandler(stream=core)

    # Still None if nothing created; otherwise, the created handler
    return handler


def set_formatter_for_handler(  # noqa: PLR0913
    handler: logging.Handler,
    fmt: str
    | logging.Formatter
    | None = "%(asctime)s | %(levelname)s | %(message)s",
    *,
    datefmt: str | None = None,
    style: _FormatStyle = "%",
    validate: bool = True,
    defaults: Mapping[str, Any] | None = None,
    copy: bool = False,
) -> None:
    """
    Sets the formatter for `handler` to the specified formatter.

    If `fmt` is a `logging.Formatter` already, a deep copy is used
    if `copy` is `True` and otherwise the original formatter; if a
    `str` or `None`, a new `logging.Formatter` is constructed
    configured according to `fmt` and the keyword arguments.

    This function follows the defaults of the `logging.Formatter`
    constructor except for the `fmt` string, which defaults to
    `None` in the `logging.Formatter` constructor but is set to a
    custom string here (
    `"%(asctime)s | %(levelname)s | %(message)s"`). See the
    `logging.Formatter` class for details about the arguments.

    Args:
        handler (logging.Handler): Handler to set formatter for
        fmt (str | logging.Formatter | None, optional): If a
            `logging.Formatter`, then the formatter to use a copy
            of; otherwise, the format string to pass to the
            `logging.Formatter` constructor. Defaults to
            `"%(asctime)s | %(levelname)s | %(message)s"`.
        datefmt (str | None, optional): Date format string to pass
            to `logging.Formatter` constructor. Ignored if `fmt` is
            a `logging.Formatter`. Defaults to `None`.
        style (_FormatStyle, optional): Style format used by the
            format string. Ignored if `fmt` is a
            `logging.Formatter`. Defaults to `"%"`.
        validate (bool, optional): If `True`, the configuration is
            validated upon creation; otherwise, no validation
            occurs. Ignored if `fmt` is a `logging.Formatter`.
            Defaults to `True`.
        defaults (Mapping[str, Any] | None, optional): Default
            values for string variable interpolation. Ignored if
            `fmt` is a `logging.Formatter`. Defaults to `None`.
        copy (bool, optional): If `True`, uses a deep copy of the
            original instance of `fmt`; otherwise, uses the
            original instance. Ignored if `fmt` is not a
            `logging.Formatter`. Defaults to `False`.
    """
    handler.setFormatter(
        get_formatter(
            fmt=fmt,
            datefmt=datefmt,
            style=style,
            validate=validate,
            defaults=defaults,
            copy=copy,
        )
    )


def _parse_filters_arg(
    filters: _FilterSpec | Sequence[_FilterSpec],
) -> tuple[_FilterSpec, ...]:
    """
    Returns the raw `filters` argument as a
    `tuple` of filter specs to apply.

    Args:
        filters (_FilterSpec | Sequence[_FilterSpec]): Raw `filters`
            argument to parse

    Returns:
        tuple[_FilterSpec, ...]: Tuple of filter specs
    """
    # Handle case of single string
    if isinstance(filters, str):
        return (filters,)

    # Handle case of lone filter, adding copy=False as default
    if isinstance(filters, logging.Filter):
        return ((filters, False),)

    # Handle case of single filter-like
    if callable(filters) or isinstance(filters, _SupportsFilter):
        return (filters,)

    if (
        isinstance(filters, tuple)
        and len(filters) == 2  # noqa: PLR2004
        and isinstance(filters[0], logging.Filter)
        and isinstance(filters[1], bool)
    ):
        return (filters,)  # pyright: ignore[reportReturnType]

    # If here, have a sequence of filters, so make sure it's a tuple
    return tuple(filters)  # pyright: ignore[reportReturnType]


def add_filters_to_target(
    target: logging.Handler | logging.Logger,
    filters: _FilterSpec | Sequence[_FilterSpec],
) -> None:
    """
    Adds the filters in `filters` to the `logging.Handler`
    or `logging.Logger` specified by `target,`.

    Args:
        target (logging.Handler | logging.Logger): Handler or logger to
            add filters to
        filters (_FilterSpec | Sequence[_FilterSpec]): Filters to add
            to target
    """
    # Standardize filters
    filters = _parse_filters_arg(filters)
    # Add each filter
    for filt in filters:
        # Create and add single-string filter
        if isinstance(filt, str):
            target.addFilter(filter=get_filter(filt=filt, copy=False))
        # Add existing filter without copying
        elif isinstance(filt, logging.Filter):
            target.addFilter(filter=get_filter(filt, copy=False))
        # Add existing filter with optional copying
        elif isinstance(filt, tuple):
            target.addFilter(
                filter=get_filter(
                    filt=filt[0],  # pyright: ignore[reportUnknownArgumentType]
                    copy=filt[1],  # pyright: ignore[reportUnknownArgumentType]
                )
            )
        # Add callable or object that has a valid filter method directly
        else:
            target.addFilter(filter=filt)


def get_handler(  # noqa: PLR0913
    core: _StrOrPathLike | _TextIOLike | logging.Handler | None = None,
    *,
    name: str | None = None,
    level: int | None = 20,
    formatter: _FormatterSpec | _NoDefaultType = NoDefault,
    filters: _FilterSpec | Sequence[_FilterSpec] = (),
    mode: str = "a",
    encoding: str | None = "utf-8",
    delay: bool = False,
    errors: str | None = None,
    copy: bool = False,
) -> logging.Handler:
    """
    Returns a `logging.Handler` configured
    according to the provided specifications.

    The configuration is done in two parts. First, a handler of the type
    specified by `core` is created. Then, that handler is configured
    according to any remaining arguments.

    The type of handler created is determined by the first item
    below that `core` matches:
    1.  If `core` is a `logging.Handler` already, a deep copy is
        created if `copy` is `True` and otherwise the original handler
        is used, in which case the handler is of the same type as `core`
    2.  If `core` is `None`, a default `logging.StreamHandler` is
        created, which logs to `sys.stderr`
    3.  If `core` matches an existing `logging.Handler` by name, as
        checked by `logging.getHandlerByName(core)`, a deep copy is
        created if `copy` is `True` and otherwise the original handler
        is used, in which case the handler is of the same type as the
        matched handler
    4.  If `core` is the string `"stdout"`, a default
        `logging.StreamHandler` is created, which logs to `sys.stdout`
    5.  If `core` is the string `"stderr"`, a default
        `logging.StreamHandler` is created, which logs to `sys.stderr`
    6.  If `core` is the string `"null"`, a default
        `logging.NullHandler` is created, which silences logging
    7.  If `core` is a `_StrOrPathLike`, then the handler
        `logging.FileHandler(filename=core)` is created, which logs to
        the file `core`
    8.  If `core` is a `_TextIOLike`, then
        `logging.StreamHandler(stream=core)` is created, which logs to
        the stream `core`
    9.  At this point, `core` should have matched one of the options
        above, so if it hasn't, a `ValueError` is raised

    *Note that capitalization variants of the strings in items 4-6
    will also match the corresponding special string.*

    *Special strings include the following: `"stdout"`, `"stderr"`,
    `"null"`, and the name of any existing `logging.Handler`*

    Args:
        core (_StrOrPathLike | _TextIOLike | logging.Handler | None, optional):
            Specifies the core logger configuration, including type and
            required arguments for that type, as applicable. The type of
            handler created can be determined by the process defined
            above. Defaults to `None`.
        name (str | None, optional): Name to assign to the created
            `logging.Handler`. If `None`, no name is assigned.
            Defaults to `None`.
        level (int | None, optional): Log level to assign to the created
            `logging.Handler`. If `None`, no level is assigned.
            Defaults to `20`.
        formatter (_FormatterSpec | _NoDefaultType, optional):
            Specification of a `logging.Formatter` to attach to the
            created handler. The specification is similar to using the
            `snaplog.get_formatter` interface. If the value is a `str`
            or `None`, then a `logging.Formatter` is created with
            `formatter` as its format string; if a `logging.Formatter`,
            a deep copy of the provided formatter is created if `copy`
            is `True` and otherwise the original handler is used; and if
            a `dict`, it must contain entries for all desired
            non-default arguments to `snaplog.get_formatter`. If
            `NoDefault`, then no formatter is attached to the handler.
            Defaults to `NoDefault`.
        filters (_FilterSpec | Sequence[_FilterSpec], optional):
            Specification of `logging.Filter`s to attach to the created
            handler. If more than one filter is specified, then they are
            all added to the handler in order. Specification of each
            filter is similar to using the `snaplog.get_filter`
            interface, except this version supports passing either a
            `Callable` that takes a `logging.LogRecord` and returns
            either a `bool` or another `logging.LogRecord` or a class
            that implements a compatible `filter` method. If the value
            is a `str`, then a `logging.Filter` is created with the
            value as the argument; if a `logging.Filter`, a deep copy of
            the provided filter is created; if a
            `tuple[logging.Filter, bool]`, a deep copy of the provided
            filter is created if the `bool` is `True` and otherwise the
            original filter is used; if a compatible `Callable` or class
            with `filter` method, it will be added as a filter directly.
            Defaults to `()` (no filters).
        mode (str, optional): Mode used to open the log file. Ignored if
            not creating a `logging.FileHandler`. Defaults to `"a"`.
        encoding (str | None, optional): Encoding for the log file.
            Ignored if not creating a `logging.FileHandler`. Note that
            the default here does not match the `logging` default of
            `None`. Defaults to `"utf-8"`.
        delay (bool, optional): If `True`, the log file is not opened
            until a message is emitted; otherwise, the file is opened
            immediately upon handler creation. Ignored if not creating a
            `logging.FileHandler`. Defaults to `False`.
        errors (str | None, optional): Determines how encoding errors
            are handled. Ignored if not creating a
            `logging.FileHandler`. Defaults to `None`.
        copy (bool, optional): If `True`, returns a deep copy of the
            original instance of `core`; otherwise, the original
            instance is returned. Ignored if `core` is not a
            `logging.Handler`. Defaults to `False`.

    Raises:
        ValueError: Raised if `core` fails to specify a valid handler

    Returns:
        logging.Handler: The specified `logging.Handler`
    """  # noqa: W505
    # Create the handler based on core
    handler = _maybe_create_handler(
        core=core,
        file_handler_kwargs={
            "mode": mode,
            "encoding": encoding,
            "delay": delay,
            "errors": errors,
        },
        copy=copy,
    )

    # Raise an error if no handler was created
    if handler is None:
        msg = (
            "No handler was created. Argument 'core' may not be valid; "
            f"got '{core}'."
        )
        raise ValueError(msg)

    # Set name and level if specified
    if name is not None:
        handler.set_name(name=name)
    if level is not None:
        handler.setLevel(level=level)

    # Add formatter if specified
    if not isinstance(formatter, _NoDefaultType):
        handler.setFormatter(fmt=get_formatter_from_spec(spec=formatter))

    # Add filters if specified
    add_filters_to_target(target=handler, filters=filters)

    return handler


def get_handler_from_spec(spec: _HandlerSpec) -> logging.Handler:
    """
    Returns a `logging.Handler` configured according to `spec`.

    Args:
        spec (_HandlerSpec): Specification of handler

    Returns:
        logging.Handler: The specified handler
    """
    # Create using keyword arguments if present, otherwise just core
    if isinstance(spec, tuple):
        return get_handler(core=spec[0], **spec[1])
    return get_handler(core=spec)


def _parse_handlers_arg(
    handlers: _HandlerSpec | Sequence[_HandlerSpec],
) -> tuple[_HandlerSpec, ...]:
    """
    Returns the raw `handlers` argument as a
    `tuple` of handler specs to apply.

    Args:
        handlers (_HandlerSpec | Sequence[_HandlerSpec]): Raw `handlers`
            argument to parse

    Returns:
        tuple[_HandlerSpec, ...]: Tuple of handler specs
    """
    # Handle case of single handler with only core specifier
    # by adding empty kwargs
    if handlers is None or isinstance(
        handlers, (str, os.PathLike, TextIO, TextIOBase, logging.Handler)
    ):
        return (handlers,)

    # Otherwise, check if multiple handlers specified
    # or just one with kwargs
    if (
        isinstance(handlers, tuple)
        and len(handlers) == 2  # noqa: PLR2004
        and isinstance(handlers[1], dict)
    ):
        return (handlers,)  # pyright: ignore[reportReturnType]

    # Finally, we must have multiple handlers, so make sure it's a tuple
    return tuple(handlers)  # pyright: ignore[reportReturnType]


def add_handlers_to_logger(
    logger: logging.Logger, handlers: _HandlerSpec | Sequence[_HandlerSpec]
) -> None:
    """
    Adds the handlers in `handlers` to the specified `logging.Logger`.

    Args:
        logger (logging.Logger): Logger to add handlers to
        handlers (_HandlerSpec | Sequence[_HandlerSpec]): Handlers to
            add to logger
    """
    # Standardize the handlers argument
    handlers = _parse_handlers_arg(handlers=handlers)
    # Add each handler
    for handler in handlers:
        logger.addHandler(hdlr=get_handler_from_spec(spec=handler))


def set_formatter_for_logger(  # noqa: PLR0913
    logger: logging.Logger,
    fmt: str
    | logging.Formatter
    | None = "%(asctime)s | %(levelname)s | %(message)s",
    *,
    datefmt: str | None = None,
    style: _FormatStyle = "%",
    validate: bool = True,
    defaults: Mapping[str, Any] | None = None,
    copy: bool = False,
    force: bool = False,
) -> None:
    """
    Sets the formatter for `logger` to the specified formatter.

    If `fmt` is a `logging.Formatter` already, a deep copy is used
    if `copy` is `True` and otherwise the original formatter; if a
    `str` or `None`, a new `logging.Formatter` is constructed
    configured according to `fmt` and the keyword arguments.

    This function follows the defaults of the `logging.Formatter`
    constructor except for the `fmt` string, which defaults to
    `None` in the `logging.Formatter` constructor but is set to a
    custom string here (
    `"%(asctime)s | %(levelname)s | %(message)s"`). See the
    `logging.Formatter` class for details about the arguments.

    Args:
        logger (logging.Logger): Logger to set formatter for
        fmt (str | logging.Formatter | None, optional): If a
            `logging.Formatter`, then the formatter to use a copy
            of; otherwise, the format string to pass to the
            `logging.Formatter` constructor. Defaults to
            `"%(asctime)s | %(levelname)s | %(message)s"`.
        datefmt (str | None, optional): Date format string to pass
            to `logging.Formatter` constructor. Ignored if `fmt` is
            a `logging.Formatter`. Defaults to `None`.
        style (_FormatStyle, optional): Style format used by the
            format string. Ignored if `fmt` is a
            `logging.Formatter`. Defaults to `"%"`.
        validate (bool, optional): If `True`, the configuration is
            validated upon creation; otherwise, no validation
            occurs. Ignored if `fmt` is a `logging.Formatter`.
            Defaults to `True`.
        defaults (Mapping[str, Any] | None, optional): Default
            values for string variable interpolation. Ignored if
            `fmt` is a `logging.Formatter`. Defaults to `None`.
        copy (bool, optional): If `True`, uses a deep copy of the
            original instance of `fmt`; otherwise, uses the
            original instance. Ignored if `fmt` is not a
            `logging.Formatter`. Defaults to `False`.
        force (bool, optional): If `True`, sets the formatter for
            handlers that already have a formatter configured;
            otherwise, only handlers without a formatter already set
            will have their formatter set. Defaults to `False`.
    """
    # Get new formatter for logger
    formatter = get_formatter(
        fmt=fmt,
        datefmt=datefmt,
        style=style,
        validate=validate,
        defaults=defaults,
        copy=copy,
    )

    # Set formatter for handlers as applicable
    for handler in logger.handlers:
        if handler.formatter is None or force:
            handler.setFormatter(formatter)


def get_logger(  # noqa: PLR0913
    name: str | None = "log",
    level: str | int = 20,
    *,
    handlers: _HandlerSpec | Sequence[_HandlerSpec] = (),
    formatter: _FormatterSpec | _NoDefaultType = NoDefault,
    filters: _FilterSpec | Sequence[_FilterSpec] = (),
    color: _ColorMode | None = None,
) -> logging.Logger:
    """
    Returns a `logging.Logger` configured according
    to the provided specifications.

    Note that the `snaplog` defaults for `name` (`"log"`) and `level`
    (`20`) differ from those of `logging.getLogger` (`None` and `30`,
    respectively).

    Args:
        name (str | None, optional): Name to apply to the logger. If
            `None`, uses the root logger. Defaults to `"log"`.
        level (str | int, optional): Logging level to use if `quiet` is
            `False`. Valid log levels include a log level string from
            the options provided by `snaplog.get_log_levels()`, the
            `int` equivalents of those log levels as defined by the
            `logging` library, or any other `int`. Defaults to `20`.
        handlers (_HandlerSpec | Sequence[_HandlerSpec], optional):
            Specification of any `logging.Handler`s to add to the
            logger. Multiple handlers can be specified by providing a
            sequence of handler specifications. Specification of each
            handler is similar to when using the `snaplog.get_handler`
            interface, except if using keyword arguments, they must be
            wrapped into a `dict` and provided as the second item of a
            `tuple`, where the first item is the argument for `core`.
            Defaults to `()` (no handlers).
        formatter (_FormatterSpec | _NoDefaultType, optional):
            Specification of a `logging.Formatter` to add to all
            handlers created for the logger that do not have an
            alternative formatter specified. If `NoDefault`, no
            formatters are added. Defaults to `NoDefault`.
        filters (_FilterSpec | Sequence[_FilterSpec], optional):
            Specification of any `logging.Filter`s to add to the logger.
            Multiple filters can be specified by providing a sequence of
            filter specifications. Specification of each filter is the
            same as when using the `snaplog.get_handler` inteface.
            Defaults to `()` (no filters).
        color (_ColorMode | None, optional): Color mode to apply to
            the formatter. When `formatter` is `NoDefault` and `color`
            is not `None` and not `"off"`, a `ColorFormatter` is
            automatically created and attached. When `formatter` is a
            spec, `color` is passed through to
            `get_formatter_from_spec`. Defaults to `None`.

    Returns:
        logging.Logger: The speficied `logging.Logger`
    """
    # Get logger with specified name, replacing default with "log"
    logger = logging.getLogger(
        "log" if isinstance(name, _NoDefaultType) else name
    )

    # Set logger level
    level = _parse_log_level(level=level, quiet=False)
    logger.setLevel(level=level)

    # Add handlers and filters if applicable
    add_handlers_to_logger(logger=logger, handlers=handlers)
    add_filters_to_target(target=logger, filters=filters)

    # Get formatter if applicable
    resolved_formatter: logging.Formatter | None
    if isinstance(formatter, _NoDefaultType):
        # Only auto-create a formatter when color mode is active
        if color is not None and color != "off":
            resolved_formatter = get_formatter(color=color)
        else:
            resolved_formatter = None
    else:
        resolved_formatter = get_formatter_from_spec(
            spec=formatter, color=color
        )

    # Set formatter for handlers as applicable
    if resolved_formatter is not None:
        for handler in logger.handlers:
            # Only add formatter to handlers without one already
            if handler.formatter is None:
                handler.setFormatter(fmt=resolved_formatter)

    return logger


def get_logger_from_spec(spec: _LoggerSpec) -> logging.Logger:
    """
    Returns a `logging.Logger` configured according to `spec`.

    Args:
        spec (_LoggerSpec): Specification of logger

    Returns:
        logging.Logger: The specified logger
    """
    # Handle case of name only
    if spec is None or isinstance(spec, str):
        return get_logger(name=spec)

    # Handle case of level only
    if isinstance(spec, int):
        return get_logger(level=spec)

    # Handle case of keyword args only
    if isinstance(spec, dict):
        return get_logger(**spec)

    # If here, have tuple of name, level, and/or keyword args
    # Check if first item is name or level
    if spec[0] is None or isinstance(spec[0], str):
        name = spec[0]
        level = None
    else:
        name = NoDefault
        level = spec[0]
    # Check if second item is level or keyword args
    if isinstance(spec[1], int):
        level = spec[1]
        kwargs: _LoggerKwargs = (
            spec[2] if len(spec) == 3 else {}  # noqa: PLR2004
        )
    else:
        kwargs = spec[1]

    # Return based on tuple items
    if isinstance(name, _NoDefaultType):
        return get_logger(
            level=level,  # pyright: ignore[reportArgumentType]
            **kwargs,
        )
    if level is None:
        return get_logger(name=name, **kwargs)
    return get_logger(name=name, level=level, **kwargs)
