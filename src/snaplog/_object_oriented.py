"""Object-oriented interface for `snaplog`."""

import logging as _logging
from typing import TYPE_CHECKING as _TYPE_CHECKING
from typing import ParamSpec as _ParamSpec
from typing import TypeVar as _TypeVar

from snaplog._typing import _NoDefault


if _TYPE_CHECKING:  # pragma: no cover
    import logging
    from collections.abc import Callable, Mapping, Sequence
    from typing import Any, Concatenate

    from snaplog._typing import (
        _ArgsType,
        _ColorSpec,
        _ExcInfoType,
        _FilterSpec,
        _FilterType,
        _FormatStyle,
        _FormatterSpec,
        _HandlerSpec,
        _NoDefaultType,
        _SysExcInfoType,
    )


# Define generic type variables for hook
P = _ParamSpec("P")
R = _TypeVar("R")


class SnapLogger(_logging.Logger):  # noqa: PLR0904  # pylint: disable=R0902
    """
    The base logger class for `snaplog`.

    A `SnapLogger` adds an intuitive interface to the `logging`
    library and makes logging a snap. It includes helpful default
    configurations and implements the standard `logging.Logger`
    interface for compatibility.
    """

    import threading

    # Create class attributes to make assigning default log names easier
    _lock = threading.Lock()
    _counter = 0

    def __init__(  # noqa: PLR0913
        self,
        name: "str | _NoDefaultType | None" = _NoDefault,
        level: str | int = 20,
        *,
        handlers: "_HandlerSpec | Sequence[_HandlerSpec]" = None,
        formatter: "_FormatterSpec | _NoDefaultType" = _NoDefault,
        filters: "_FilterSpec | Sequence[_FilterSpec]" = (),
        color: "_ColorSpec" = "level",
    ) -> None:
        """
        The base logger class for `snaplog`.

        A `SnapLogger` adds an intuitive interface to the `logging`
        library and makes logging a snap. It includes helpful default
        configurations and implements the standard `logging.Logger`
        interface for compatibility.

        Note that the `snaplog` defaults for `name` (`"logX"`, where `X`
        is the cumulative number of `SnapLogger` instances created with
        a default name) and `level` (`20`) differ from those of
        `logging.getLogger` (`None` and `30`, respectively).

        Args:
            name (str | _NoDefaultType | None, optional): Name to apply
                to the logger. If `None`, uses the root logger. If
                `_NoDefault`, uses `"logX"`, where `X` is the cumulative
                number of `SnapLogger` instances created with a default
                name. Defaults to `_NoDefault`.
            level (str | int, optional): Logging level to apply to the
                logger. Valid log levels include a log level string from
                the options provided by `snaplog.get_log_levels()`, the
                `int` equivalents of those log levels as defined by the
                `logging` library, or any other `int`. Defaults to `20`.
            handlers (_HandlerSpec | Sequence[_HandlerSpec], optional):
                Specification of any `logging.Handler`s to add to the
                logger. Multiple handlers can be specified by providing
                a sequence of handler specifications. Specification of
                each handler is similar to when using the
                `snaplog.get_handler` interface, except if using
                keyword arguments, they must be wrapped into a `dict`
                and provided as the second item of a `tuple`, where the
                first item is the argument for `core`. Note that if
                `None`, a default `logging.StreamHandler` that logs to
                `sys.stderr` is created. Defaults to `None`.
            formatter (_FormatterSpec | _NoDefaultType, optional):
                Specification of a `logging.Formatter` to add to all
                handlers created for the logger that do not have an
                alternative formatter specified. If `_NoDefault`, no
                formatters are added. Defaults to `_NoDefault`.
            filters (_FilterSpec | Sequence[_FilterSpec], optional):
                Specification of any `logging.Filter`s to add to the
                logger. Multiple filters can be specified by providing a
                sequence of filter specifications. Specification of each
                filter is the same as when using the
                `snaplog.get_handler` inteface.
                Defaults to `()` (no filters).
            color (_ColorSpec, optional): Color mode for the formatter.
                Either a bare `_ColorMode` string or a tuple of
                `(_ColorMode, colormap)` for per-level color overrides.
                Passed through to `get_logger`. If mode is not `"off"`,
                a `ColorFormatter` is used. Defaults to `"level"`.
        """
        from snaplog._functional import get_formatter_from_spec, get_logger
        from snaplog._typing import _NoDefaultType

        # Call super init and create root logger
        super().__init__("root", level=0)

        # Set default name if none provided
        if isinstance(name, _NoDefaultType):
            # Use thread lock to ensure that only
            # one of each number can be created
            with SnapLogger._lock:
                name = f"log{SnapLogger._counter}"
                SnapLogger._counter += 1

        # Create logger
        self.logger = get_logger(
            name=name,
            level=level,
            handlers=handlers,
            formatter=formatter,
            filters=filters,
            color=color,
        )

        # Save standard logging.Logger attributes
        self.name = self.logger.name
        self.level = self.logger.level
        self.handlers = self.logger.handlers
        self.filters = self.logger.filters
        self.disabled = self.logger.disabled
        self.propagate = self.logger.propagate
        self.parent = self.logger.parent
        self.manager = self.logger.manager

        # Save custom attributes
        self.formatter = (
            None
            if isinstance(formatter, _NoDefaultType)
            else get_formatter_from_spec(spec=formatter)
        )

    @staticmethod
    def _update_logger_attributes_hook(
        function: "Callable[Concatenate[SnapLogger, P], R]",
    ) -> "Callable[Concatenate[SnapLogger, P], R]":
        """
        Update the instance attributes to reflect the logger's
        current attributes after the function `function` is run.

        Args:
            function (Callable[Concatenate["SnapLogger", P], R]):
                Function to run, after which the attributes are updated

        Returns:
            Callable[Concatenate["SnapLogger", P], R]: Wrapped function
        """
        from functools import wraps

        @wraps(function)
        def wrapper(self: "SnapLogger", *args: P.args, **kwargs: P.kwargs) -> R:
            """
            Returns the output of running the wrapped function with the
            given arguments and updates the logger's attributes after
            the wrapped function finishes running.

            Args:
                self (SnapLogger): The `SnapLogger` instance
                *args (P.args): Positional arguments to the
                    wrapped function
                **kwargs (P.kwargs): Keyword arguments to the
                    wrapped function

            Returns:
                R: Output of running the wrapped function
            """
            # Run function
            result = function(self, *args, **kwargs)

            # Update attributes
            for attribute in (
                "name",
                "level",
                "handlers",
                "filters",
                "disabled",
                "propagate",
                "parent",
                "manager",
            ):
                setattr(self, attribute, getattr(self.logger, attribute))

            return result

        return wrapper

    @_update_logger_attributes_hook
    def add_handlers(
        self, handlers: "_HandlerSpec | Sequence[_HandlerSpec]"
    ) -> None:
        """
        Adds the `logging.Handlers` specified
        by `handlers` to the logger.

        If the logger has not yet been created, it will be created.

        Args:
            handlers (_HandlerSpec | Sequence[_HandlerSpec]):
                Specification of `logging.Handlers` to add to logger
        """
        from snaplog._functional import add_handlers_to_logger

        add_handlers_to_logger(handlers=handlers, logger=self.logger)

    @_update_logger_attributes_hook
    def set_formatter(  # noqa: PLR0913
        self,
        fmt: (
            "str | logging.Formatter | None"
        ) = "%(asctime)s | %(levelname)s | %(message)s",
        *,
        datefmt: str | None = None,
        style: "_FormatStyle" = "%",
        validate: bool = True,
        defaults: "Mapping[str, Any] | None" = None,
        copy: bool = False,
        force: bool = False,
    ) -> None:
        """
        Sets the formatter for the logger to the specified formatter.

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
        from snaplog._functional import get_formatter, set_formatter_for_logger

        # Set new formatter for logger
        self.formatter = get_formatter(
            fmt=fmt,
            datefmt=datefmt,
            style=style,
            validate=validate,
            defaults=defaults,
            copy=copy,
        )

        # Apply new formatter to logger's handlers
        set_formatter_for_logger(
            logger=self.logger, fmt=self.formatter, copy=False, force=force
        )

    @_update_logger_attributes_hook
    def add_filters(
        self, filters: "_FilterSpec | Sequence[_FilterSpec]"
    ) -> None:
        """
        Adds the `logging.Filters` specified
        by `filters` to the logger.

        If the logger has not yet been created, it will be created.

        Args:
            filters (_FilterSpec | Sequence[_FilterSpec]):
                Specification of `logging.Filters` to add to logger
        """
        from snaplog._functional import add_filters_to_target

        add_filters_to_target(filters=filters, target=self.logger)

    # Main logging methods

    def log(  # noqa: PLR0913  # pylint: disable=arguments-differ
        self,
        level: str | int,
        msg: object,
        *args: "Any",
        exc_info: "_ExcInfoType" = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: "Mapping[str, object] | None" = None,
    ) -> None:
        """
        Log a message using the standard `logging` API
        (plus support for `str` logging levels).

        Args:
            level (str | int): Valid log levels include a log level
                string from the options provided by
                `snaplog.get_log_levels()`, the `int` equivalents of
                those log levels as defined by the `logging` library, or
                any other `int`.
            msg (object): Message to log
            *args (Any): Arguments other than `msg` to pass to the
                `loggingLogger`'s `log` method. This might be used to
                provide variables to interpolate into `msg`.
            exc_info (_ExcInfoType, optional): See `logging.Logger`'s
                method `log` for details. Defaults to `None`.
            stack_info (bool, optional): See `logging.Logger`'s
                method `log` for details. Defaults to `False`.
            stacklevel (int, optional): See `logging.Logger`'s
                method `log` for details. Defaults to `1`.
            extra (Mapping[str, object] | None, optional): See
                `logging.Logger`'s method `log` for details.
                Defaults to `None`.
        """
        from snaplog._functional import _parse_log_level

        # Determine level
        level = _parse_log_level(level=level, quiet=False)
        # Log message
        self.logger.log(
            level,
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
        )

    def record(  # noqa: PLR0913
        self,
        msg: object,
        *args: "Any",
        level: str | int = "debug",
        quiet: bool = False,
        exc_info: "_ExcInfoType" = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: "Mapping[str, object] | None" = None,
    ) -> None:
        """
        Log/record a message using the `snaplog` API.

        *Note that this function's API differs from that of the
        `logging.Logger`'s `log` method: this function requires that
        `level` be provided as a keyword argument instead of as the
        first positional argument, and the `quiet` keyword argument
        is added.*

        Args:
            msg (object): Message to log
            *args (Any): Arguments other than `msg` to pass to the
                `loggingLogger`'s `log` method. This might be used to
                provide variables to interpolate into `msg`.
            level (str | int, optional): Logging level to use if
                `quiet` is `False`. Valid log levels include a log level
                string from the options provided by
                `snaplog.get_log_levels()`, the `int` equivalents of
                those log levels as defined by the `logging` library, or
                any other `int`. Overriden by the `quiet` argument if it
                is `True`. Defaults to `"debug"`.
            quiet (bool, optional): If `True`, forces the log to the
                `logging.DEBUG` level; otherwise, the `level` argument
                sets the log level. Defaults to `False`.
            exc_info (_ExcInfoType, optional): See `logging.Logger`'s
                method `log` for details. Defaults to `None`.
            stack_info (bool, optional): See `logging.Logger`'s
                method `log` for details. Defaults to `False`.
            stacklevel (int, optional): See `logging.Logger`'s
                method `log` for details. Defaults to `1`.
            extra (Mapping[str, object] | None, optional): See
                `logging.Logger`'s method `log` for details.
                Defaults to `None`.
        """
        from snaplog._functional import _parse_log_level

        # Determine level
        level = _parse_log_level(level=level, quiet=quiet)
        # Delegate to log method
        self.log(
            level,
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
        )

    def rec(  # noqa: PLR0913
        self,
        msg: object,
        *args: "Any",
        level: str | int = "debug",
        quiet: bool = False,
        exc_info: "_ExcInfoType" = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: "Mapping[str, object] | None" = None,
    ) -> None:
        """
        Log/record a message using the `snaplog` API.

        Alias of `record`.

        *Note that this function's API differs from that of the
        `logging.Logger`'s `log` method: this function requires that
        `level` be provided as a keyword argument instead of as the
        first positional argument, and the `quiet` keyword argument
        is added.*

        Args:
            msg (object): Message to log
            *args (Any): Arguments other than `msg` to pass to the
                `loggingLogger`'s `log` method. This might be used to
                provide variables to interpolate into `msg`.
            level (str | int, optional): Logging level to use if
                `quiet` is `False`. Valid log levels include a log level
                string from the options provided by
                `snaplog.get_log_levels()`, the `int` equivalents of
                those log levels as defined by the `logging` library, or
                any other `int`. Overriden by the `quiet` argument if it
                is `True`. Defaults to `"debug"`.
            quiet (bool, optional): If `True`, forces the log to the
                `logging.DEBUG` level; otherwise, the `level` argument
                sets the log level. Defaults to `False`.
            exc_info (_ExcInfoType, optional): See `logging.Logger`'s
                method `log` for details. Defaults to `None`.
            stack_info (bool, optional): See `logging.Logger`'s
                method `log` for details. Defaults to `False`.
            stacklevel (int, optional): See `logging.Logger`'s
                method `log` for details. Defaults to `1`.
            extra (Mapping[str, object] | None, optional): See
                `logging.Logger`'s method `log` for details.
                Defaults to `None`.
        """
        self.record(
            msg,
            *args,
            level=level,
            quiet=quiet,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
        )

    # Replicate logging.Logger interface

    def critical(
        self,
        msg: object,
        *args: object,
        exc_info: "_ExcInfoType" = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: "Mapping[str, object] | None" = None,
        **kwargs: "Any",
    ) -> None:
        """
        Log a message with level `CRITICAL` on this logger.

        Mirrors the interface of `logging.Logger.critical`.
        """
        self.logger.log(
            _logging.CRITICAL,
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
            **kwargs,
        )

    def debug(
        self,
        msg: object,
        *args: object,
        exc_info: "_ExcInfoType" = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: "Mapping[str, object] | None" = None,
        **kwargs: "Any",
    ) -> None:
        """
        Log a message with level `DEBUG` on this logger.

        Mirrors the interface of `logging.Logger.debug`.
        """
        self.logger.log(
            _logging.DEBUG,
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
            **kwargs,
        )

    def error(
        self,
        msg: object,
        *args: object,
        exc_info: "_ExcInfoType" = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: "Mapping[str, object] | None" = None,
        **kwargs: "Any",
    ) -> None:
        """
        Log a message with level `ERROR` on this logger.

        Mirrors the interface of `logging.Logger.error`.
        """
        self.logger.log(
            _logging.ERROR,
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
            **kwargs,
        )

    def exception(
        self,
        msg: object,
        *args: object,
        exc_info: "_ExcInfoType" = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: "Mapping[str, object] | None" = None,
        **kwargs: "Any",
    ) -> None:
        """
        Log a message with level `ERROR` on this logger.

        Mirrors the interface of `logging.Logger.exception`.
        """
        self.logger.log(
            _logging.ERROR,
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
            **kwargs,
        )

    def fatal(
        self,
        msg: object,
        *args: object,
        exc_info: "_ExcInfoType" = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: "Mapping[str, object] | None" = None,
        **kwargs: "Any",
    ) -> None:
        """
        Log a message with level `FATAL` on this logger.

        Mirrors the interface of `logging.Logger.fatal`.
        """
        self.logger.log(
            _logging.FATAL,
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
            **kwargs,
        )

    def info(
        self,
        msg: object,
        *args: object,
        exc_info: "_ExcInfoType" = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: "Mapping[str, object] | None" = None,
        **kwargs: "Any",
    ) -> None:
        """
        Log a message with level `INFO` on this logger.

        Mirrors the interface of `logging.Logger.info`.
        """
        self.logger.log(
            _logging.INFO,
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
            **kwargs,
        )

    def warn(
        self,
        msg: object,
        *args: object,
        exc_info: "_ExcInfoType" = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: "Mapping[str, object] | None" = None,
        **kwargs: "Any",
    ) -> None:
        """
        Log a message with level `WARNING` on this logger.

        Mirrors the interface of `logging.Logger.warning`.

        *Note that `logging.Logger.warn` is deprecated and should not be
        used, but it is included here for compatibility with the
        `logging.Logger` interface. See `logging.Logger.warning`
        for details.*
        """
        self.logger.log(
            _logging.WARNING,
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
            **kwargs,
        )

    def warning(
        self,
        msg: object,
        *args: object,
        exc_info: "_ExcInfoType" = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: "Mapping[str, object] | None" = None,
        **kwargs: "Any",
    ) -> None:
        """
        Log a message with level `WARNING` on this logger.

        Mirrors the interface of `logging.Logger.warning`.
        """
        self.logger.log(
            _logging.WARNING,
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
            **kwargs,
        )

    def filter(self, record: "logging.LogRecord") -> "bool | logging.LogRecord":
        """
        Returns the result of filtering the specified
        record using the logger's filters.

        See `logging.Logger`'s `filter` method for details.

        Args:
            record (logging.LogRecord): Record to filter

        Returns:
            bool | logging.LogRecord: Result of filtering the record
        """
        return self.logger.filter(record=record)

    def handle(self, record: "logging.LogRecord") -> None:
        """
        Handles the specified record using the logger's handlers.

        See `logging.Logger`'s `handle` method for details.

        Args:
            record (logging.LogRecord): Record to handle
        """
        self.logger.handle(record=record)

    @_update_logger_attributes_hook
    def addFilter(self, filter: "_FilterType") -> None:  # noqa: A002
        """
        Adds the specified `logging.Filter` to the logger.

        See `logging.Logger`'s `addFilter` method for details.

        Args:
            filter (_FilterType): Filter to add
        """
        self.add_filters(filters=filter)

    @_update_logger_attributes_hook
    def addHandler(self, hdlr: "logging.Handler") -> None:
        """
        Adds the specified `logging.Handler` to the logger.

        See `logging.Logger`'s `addHandler` method for details.

        Args:
            hdlr (logging.Handler): Handler to add
        """
        self.add_handlers(handlers=hdlr)

    @_update_logger_attributes_hook
    def removeFilter(self, filter: "_FilterType") -> None:  # noqa: A002
        """
        Removes the specified `logging.Filter` from the logger.

        See `logging.Logger`'s `removeFilter` method for details.

        Args:
            filter (_FilterType): Filter to remove
        """
        self.logger.removeFilter(filter=filter)

    @_update_logger_attributes_hook
    def removeHandler(self, hdlr: "logging.Handler") -> None:
        """
        Removes the specified `logging.Handler` from the logger.

        See `logging.Logger`'s `removeHandler` method for details.

        Args:
            hdlr (logging.Handler): Handler to remove
        """
        self.logger.removeHandler(hdlr=hdlr)

    @_update_logger_attributes_hook
    def setLevel(self, level: str | int) -> None:
        """
        Sets the logging level of the logger to the specified level.

        See `logging.Logger`'s `setLevel` method for details.
        Supports snaplog shorthand strings (e.g. ``"d"``,
        ``"i"``, ``"w"``, ``"e"``, ``"c"``).

        Args:
            level (str | int): Level to use
        """
        from snaplog._functional import _parse_log_level

        level = _parse_log_level(level=level, quiet=False)
        self.logger.setLevel(level=level)

    def callHandlers(self, record: "logging.LogRecord") -> None:
        """
        Calls the handlers for the specified record.

        See `logging.Logger`'s `callHandlers` method for details.

        Args:
            record (logging.LogRecord): Record to handle
        """
        self.logger.callHandlers(record=record)

    def findCaller(
        self,
        stack_info: bool = False,  # noqa: FBT001,FBT002
        stacklevel: int = 1,
    ) -> tuple[str, int, str, str | None]:
        """
        Returns a tupl of information about the caller of the logging
        function, including the filename, line number, function name,
        and stack info (if `stack_info` is `True`).

        See `logging.Logger`'s `findCaller` method for details.

        Args:
            stack_info (bool, optional): If `True`, includes stack info
                in the returned tuple; otherwise, stack info is not
                included. Defaults to `False`.
            stacklevel (int, optional): Number of stack frames to skip
                when determining the caller information.
                Defaults to `1`.

        Returns:
            tuple[str, int, str, str | None]: Tuple containing the
                filename, line number, function name, and stack info (if
                `stack_info` is `True`) of the caller of the
                logging function
        """
        return self.logger.findCaller(
            stack_info=stack_info, stacklevel=stacklevel
        )

    def getChild(  # type: ignore[override]
        self, suffix: str
    ) -> "logging.Logger":
        """
        Returns a logger which is a child of this logger,
        with the name of this logger as a prefix.

        See `logging.Logger`'s `getChild` method for details.

        Args:
            suffix (str): Suffix to append to this logger's name for the
                child logger

        Returns:
            logging.Logger: Logger which is a child of this logger, with
                the name of this logger as a prefix and `suffix` as
                a suffix
        """
        return self.logger.getChild(suffix=suffix)

    def getChildren(self) -> "set[logging.Logger]":
        """
        Returns a set of all child loggers of this logger.

        See `logging.Logger`'s `getChildren` method for details.

        Returns:
            set[logging.Logger]: Set of all child loggers of this logger
        """
        return self.logger.getChildren()

    def getEffectiveLevel(self) -> int:
        """
        Returns the effective logging level for this logger.

        See `logging.Logger`'s `getEffectiveLevel` method for details.

        Returns:
            int: Effective logging level for this logger
        """
        return self.logger.getEffectiveLevel()

    def hasHandlers(self) -> bool:
        """
        Returns `True` if this logger has any handlers
        configured; otherwise, returns `False`.

        See `logging.Logger`'s `hasHandlers` method for details.

        Returns:
            bool: `True` if this logger has any handlers configured;
                otherwise, `False`
        """
        return self.logger.hasHandlers()

    def isEnabledFor(self, level: int) -> bool:
        """
        Returns `True` if this logger is enabled for the
        specified level; otherwise returns `False`.

        See `logging.Logger`'s `isEnabledFor` method for details.

        Args:
            level (int): Integer log level to check

        Returns:
            bool: `True` if this logger is enabled for the specified
                level; otherwise, `False`
        """
        return self.logger.isEnabledFor(level=level)

    def makeRecord(  # noqa: PLR0913,PLR0917
        self,
        name: str,
        level: int,
        fn: str,
        lno: int,
        msg: object,
        args: "_ArgsType",
        exc_info: "_SysExcInfoType | None",
        func: str | None = None,
        extra: "Mapping[str, object] | None" = None,
        sinfo: str | None = None,
    ) -> "logging.LogRecord":
        """
        Returns a `logging.LogRecord` instance created
        using the specified arguments.

        Args:
            name (str): Name of logger to which record will be passed
            level (int): Integer log level for the record
            fn (str): Filename of the source file where the logging call
                was made
            lno (int): Line number in the source file where the logging
                call was made
            msg (object): Message to log
            args (_ArgsType): Arguments to pass to the
                `logging.LogRecord` constructor for interpolation
                into `msg`
            exc_info (_SysExcInfoType | None): Exception info to pass
                to the `logging.LogRecord` constructor. If `None`, no
                exception info is included in the record. If a tuple of
                the form returned by `sys.exc_info()`, the tuple is
                passed directly to the `logging.LogRecord` constructor.
            func (str | None, optional): Function name to pass to the
                `logging.LogRecord` constructor. If `None`, no function
                name is included in the record. Defaults to `None`.
            extra (Mapping[str, object] | None, optional): Extra
                attributes to add to the `logging.LogRecord` instance
                created by this function. Defaults to `None`.
            sinfo (str | None, optional): Stack info to pass to the
                `logging.LogRecord` constructor. If `None`, no stack
                info is included in the record. Defaults to `None`.

        Returns:
            logging.LogRecord: _description_
        """
        return self.logger.makeRecord(
            name=name,
            level=level,
            fn=fn,
            lno=lno,
            msg=msg,
            args=args,
            exc_info=exc_info,
            func=func,
            extra=extra,
            sinfo=sinfo,
        )
