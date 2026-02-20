"""Object-oriented interface for `snaplog`."""

import logging
import threading
from collections.abc import Callable, Mapping, Sequence
from functools import wraps
from typing import Any, Concatenate, ParamSpec, TypeVar

from snaplog._functional import (
    _parse_log_level,
    add_filters_to_target,
    add_handlers_to_logger,
    get_formatter,
    get_formatter_from_spec,
    get_logger,
    set_formatter_for_logger,
)
from snaplog._typing import (
    NoDefault,
    _ArgsType,
    _ColorMode,
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
P = ParamSpec("P")
R = TypeVar("R")


class SnapLogger(logging.Logger):  # noqa: PLR0904  # pylint: disable=R0902
    """
    The base logger class for `snaplog`.

    A `SnapLogger` adds an intuitive interface to the `logging`
    library and makes logging a snap. It includes helpful default
    configurations and implements the standard `logging.Logger`
    interface for compatibility.
    """

    # Create class attributes to make assigning default log names easier
    _lock = threading.Lock()
    _counter = 0

    def __init__(  # noqa: PLR0913
        self,
        name: str | _NoDefaultType | None = NoDefault,
        level: str | int = 20,
        *,
        handlers: _HandlerSpec | Sequence[_HandlerSpec] = None,
        formatter: _FormatterSpec | _NoDefaultType = NoDefault,
        filters: _FilterSpec | Sequence[_FilterSpec] = (),
        color: _ColorMode = "level",
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
            name (str | None, optional): Name to apply to the logger. If
                `None`, uses the root logger. If `NoDefault`, uses
                `"logX"`, where `X` is the cumulative number of
                `SnapLogger` instances created with a default name.
                Defaults to `NoDefault`.
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
                alternative formatter specified. If `NoDefault`, no
                formatters are added. Defaults to `NoDefault`.
            filters (_FilterSpec | Sequence[_FilterSpec], optional):
                Specification of any `logging.Filter`s to add to the
                logger. Multiple filters can be specified by providing a
                sequence of filter specifications. Specification of each
                filter is the same as when using the
                `snaplog.get_handler` inteface.
                Defaults to `()` (no filters).
            color (_ColorMode, optional): Color mode for the formatter.
                Passed through to `get_logger`. If not `"off"`, a
                `ColorFormatter` is used. Defaults to `"level"`.
        """
        # Call super init and create root logger
        super().__init__("root", level=0)

        # Set default name if none provided
        if isinstance(name, _NoDefaultType):
            # Use thread lock to ensure that only
            # one of each number can be created
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
        function: Callable[Concatenate["SnapLogger", P], R],
    ) -> Callable[Concatenate["SnapLogger", P], R]:
        """
        Update the instance attributes to reflect the logger's
        current attributes after the function `function` is run.

        Args:
            function (Callable[Concatenate["SnapLogger", P], R]):
                Function to run, after which the attributes are updated

        Returns:
            Callable[Concatenate["SnapLogger", P], R]: Wrapped function
        """

        @wraps(function)
        def wrapper(self: SnapLogger, *args: P.args, **kwargs: P.kwargs) -> R:
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
        self, handlers: _HandlerSpec | Sequence[_HandlerSpec]
    ) -> None:
        """
        Adds the `logging.Handlers` specified
        by `handlers` to the logger.

        If the logger has not yet been created, it will be created.

        Args:
            handlers (_HandlerSpec | Sequence[_HandlerSpec]):
                Specification of `logging.Handlers` to add to logger
        """
        add_handlers_to_logger(handlers=handlers, logger=self.logger)

    @_update_logger_attributes_hook
    def set_formatter(  # noqa: PLR0913
        self,
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
    def add_filters(self, filters: _FilterSpec | Sequence[_FilterSpec]) -> None:
        """
        Adds the `logging.Filters` specified
        by `filters` to the logger.

        If the logger has not yet been created, it will be created.

        Args:
            filters (_FilterSpec | Sequence[_FilterSpec]):
                Specification of `logging.Filters` to add to logger
        """
        add_filters_to_target(filters=filters, target=self.logger)

    def log(
        self,
        msg: object,
        *args: Any,
        level: str | int = "debug",
        quiet: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Log a message.

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
            **kwargs (Any): Keyword arguments to pass to the
                `logging.Logger`'s `log` method. This might be used to
                pass exception information.
        """
        # Determine level
        level = _parse_log_level(level=level, quiet=quiet)
        # Log message
        self.logger.log(level, msg, *args, **kwargs)

    ####################################################################
    # Replicate logging.Logger interface
    ####################################################################

    def critical(
        self,
        msg: object,
        *args: object,
        exc_info: _ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
        **kwargs: Any,
    ) -> None:
        self.logger.log(
            logging.CRITICAL,
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
        exc_info: _ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
        **kwargs: Any,
    ) -> None:
        self.logger.log(
            logging.DEBUG,
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
        exc_info: _ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
        **kwargs: Any,
    ) -> None:
        self.logger.log(
            logging.ERROR,
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
        exc_info: _ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
        **kwargs: Any,
    ) -> None:
        self.logger.log(
            logging.ERROR,
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
        exc_info: _ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
        **kwargs: Any,
    ) -> None:
        self.logger.log(
            logging.FATAL,
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
        exc_info: _ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
        **kwargs: Any,
    ) -> None:
        self.logger.log(
            logging.INFO,
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
        exc_info: _ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
        **kwargs: Any,
    ) -> None:
        self.logger.log(
            logging.WARNING,
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
        exc_info: _ExcInfoType = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
        **kwargs: Any,
    ) -> None:
        self.logger.log(
            logging.WARNING,
            msg,
            *args,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
            extra=extra,
            **kwargs,
        )

    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        return self.logger.filter(record=record)

    def handle(self, record: logging.LogRecord) -> None:
        self.logger.handle(record=record)

    @_update_logger_attributes_hook
    def addFilter(self, filter: _FilterType) -> None:  # noqa: A002
        self.add_filters(filters=filter)

    @_update_logger_attributes_hook
    def addHandler(self, hdlr: logging.Handler) -> None:
        self.add_handlers(handlers=hdlr)

    @_update_logger_attributes_hook
    def removeFilter(self, filter: _FilterType) -> None:  # noqa: A002
        self.logger.removeFilter(filter=filter)

    @_update_logger_attributes_hook
    def removeHandler(self, hdlr: logging.Handler) -> None:
        self.logger.removeHandler(hdlr=hdlr)

    @_update_logger_attributes_hook
    def setLevel(self, level: str | int) -> None:
        self.logger.setLevel(level=level)

    def callHandlers(self, record: logging.LogRecord) -> None:
        self.logger.callHandlers(record=record)

    def findCaller(
        self,
        stack_info: bool = False,  # noqa: FBT001,FBT002
        stacklevel: int = 1,
    ) -> tuple[str, int, str, str | None]:
        return self.logger.findCaller(
            stack_info=stack_info, stacklevel=stacklevel
        )

    def getChild(self, suffix: str) -> logging.Logger:
        return self.logger.getChild(suffix=suffix)

    def getChildren(self) -> set[logging.Logger]:
        return self.logger.getChildren()

    def getEffectiveLevel(self) -> int:
        return self.logger.getEffectiveLevel()

    def hasHandlers(self) -> bool:
        return self.logger.hasHandlers()

    def isEnabledFor(self, level: int) -> bool:
        return self.logger.isEnabledFor(level=level)

    def makeRecord(  # noqa: PLR0913,PLR0917
        self,
        name: str,
        level: int,
        fn: str,
        lno: int,
        msg: object,
        args: _ArgsType,
        exc_info: _SysExcInfoType | None,
        func: str | None = None,
        extra: Mapping[str, object] | None = None,
        sinfo: str | None = None,
    ) -> logging.LogRecord:
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
