"""Typing definitions for `sefkhet`."""

import datetime
import logging
import os
from collections.abc import Callable, Mapping, Sequence
from io import TextIOBase
from socket import SocketKind
from ssl import SSLContext
from types import TracebackType
from typing import (
    Any,
    Literal,
    Protocol,
    Required,
    TextIO,
    TypeVar,
    TypedDict,
    runtime_checkable,
)


########################################################################
# Default types
########################################################################


class DefaultType:  # pylint: disable=too-few-public-methods
    """
    Sentinel to denote that an argument will set to a default
    value within the function if another value is not specified.

    Often used when the default setting is not representable using
    normal default specifier syntax (e.g., the default comes from a
    function call).
    """


class NoDefaultType:  # pylint: disable=too-few-public-methods
    """
    Sentinel to denote that an argument has no set default value.

    Often used when an argument is ignored if not given,
    the default value is inferred from the values of other arguments.
    """


class NotGivenType:  # pylint: disable=too-few-public-methods
    """
    Sentinel to denote that a value was not given for an argument.

    Used when `None` needs to be differentiated from "not given".
    """


# Create instances to use throughout the package
Default = DefaultType()
NoDefault = NoDefaultType()
NotGiven = NotGivenType()

########################################################################
# Logging module-specific types
########################################################################

# Define types for info in logging calls
type SysExcInfoType = (
    tuple[type, BaseException, TracebackType | None] | tuple[None, None, None]
)
type ExcInfoType = bool | SysExcInfoType | BaseException | None
type ArgsType = tuple[Any, ...] | Mapping[str, Any]


########################################################################
# Formatters
########################################################################

# Define valid format string styles (taken from logging typeshed)
type FormatStyle = Literal["%", "{", "$"]

# Formatter types
########################################################################

# Color specifiers
type ColorMode = Literal["full", "partial", "level", "msg", "off"]
type ColorMap = Callable[[int], str] | Mapping[int, str]
type ColorSpec = ColorMode | tuple[ColorMode, ColorMap]


class JsonSpec(TypedDict, total=False):
    """Specifiers for a `sefkhet.JsonFormatter`."""

    fields: Sequence[str]
    indent: int | None
    ensure_ascii: bool
    sort_keys: bool


class CsvSpec(TypedDict, total=False):
    """Specifiers for a `sefkhet.CsvFormatter`."""

    fields: Sequence[str]
    delimiter: str
    quoting: int
    header: bool


class LogfmtSpec(TypedDict, total=False):
    """Specifiers for a `sefkhet.LogfmtFormatter`."""

    fields: Sequence[str]
    sort_keys: bool


# Formatter specification
########################################################################


class FormatterOpts(TypedDict, total=False):
    """Options for creating a `logging.Formatter`."""

    fmt: str | None
    datefmt: str | None
    style: FormatStyle
    validate: bool
    defaults: Mapping[str, Any] | None
    copy: bool
    color: ColorSpec
    json: bool | JsonSpec
    csv: bool | CsvSpec
    logfmt: bool | LogfmtSpec


# Define valid formatter specs
type FormatterSpec = (
    str  # Just format string
    | logging.Formatter  # Pre-configured formatter
    | FormatterOpts  # Options to specify a formatter
    | DefaultType  # Default formatter
)


########################################################################
# Filters
########################################################################

# Definitions for SupportsFilter, FilterLike and FilterType
# were taken from the logging typeshed


# In 3.12+, a filter can be any object that supports the filter protocol
# The filter attribute/method must exist and have the correct signature
@runtime_checkable
class SupportsFilter(Protocol):  # pylint: disable=too-few-public-methods
    def filter(
        self, record: logging.LogRecord, /
    ) -> bool | logging.LogRecord: ...


# A filter-like must implement the SupportsFilter protocol
# or be a callable that matches the filter type signature
type FilterLike = (
    SupportsFilter | Callable[[logging.LogRecord], bool | logging.LogRecord]
)

# A filter-type must be a filter, implement the SupportsFilter protocol,
# or be a callable that matches the filter type signature
type FilterType = logging.Filter | FilterLike

# Define valid filter specs
# (name of filter or object supporting filter)
type FilterSpec = (
    str  # Filter creation argument
    | logging.Filter  # Pre-configured filter
    | tuple[logging.Filter, bool]  # Pre-configured filter + copy argument
    | FilterLike  # Non-logging.Filter objects that can be used as filters
)


########################################################################
# Handlers
########################################################################


# Define alias for str/pathlike arguments
type StrOrPathLike = str | os.PathLike[str] | os.PathLike[bytes]

# Define alias for TextIO-like arguments
type TextIOLike = TextIO | TextIOBase


# Define valid names for handler types
type HandlerType = Literal[
    "stream",
    "file",
    "watched_file",
    "rotating_file",
    "timed_file",
    "timed_rotating_file",
    "queue_pair",
    "queue_handler",
    "queue_listener",
    "memory",
    "syslog",
    "smtp",
    "http",
    "socket",
    "datagram",
    "nt_eventlog",
    "null",
]


class HandlerOpts(TypedDict, total=False):
    """Base options for creating a `logging.Handler`."""

    core: StrOrPathLike | TextIOLike | logging.Handler | DefaultType | None
    # Special keywords
    formatter: FormatterSpec | DefaultType
    filters: FilterSpec | Sequence[FilterSpec]
    # Other configurations
    level: int | None
    name: str | None
    copy: bool
    queued: bool
    buffered: bool
    handler_type: HandlerType


# Basic handlers
########################################################################


class StreamHandlerOpts(HandlerOpts, total=False):
    """Options for creating a `logging.StreamHandler`."""

    core: StrOrPathLike | TextIOLike | logging.Handler | DefaultType  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
    handler_type: Literal["stream"]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]


class FileHandlerOpts(HandlerOpts, total=False):
    """Options for creating a `logging.FileHandler`."""

    handler_type: Literal["file"]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
    mode: str
    encoding: str | None
    delay: bool
    errors: str | None


class NullHandlerOpts(HandlerOpts, total=False):
    """Options for creating a `logging.NullHandler`."""

    handler_type: Required[Literal["null"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]


# Wrapper handlers
########################################################################

# Define allowed queue-like objects for queue handlers/listeners
# (taken from logging.handlers typeshed)
T = TypeVar("T")


class QueueLike(Protocol[T]):
    def get(self) -> T: ...
    def put_nowait(self, item: T, /) -> None: ...


class QueuePairOpts(HandlerOpts, total=False):
    """
    Options for creating a `logging.handlers.QueueHandler`/
    `logging.handlers.QueueListener` pair.
    """

    handler_type: Required[Literal["queue_pair"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
    queue: QueueLike[Any] | DefaultType
    respect_handler_level: bool


class QueueHandlerOpts(HandlerOpts, total=False):
    """Options for creating a `logging.handlers.QueueHandler`."""

    handler_type: Required[Literal["queue_handler"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
    queue: QueueLike[Any] | DefaultType


class QueueListenerKwargs(HandlerOpts, total=False):
    """Options for creating a `logging.handlers.QueueListener`."""

    handler_type: Required[Literal["queue_listener"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
    queue: QueueLike[Any] | NoDefaultType
    listener_handlers: logging.Handler | Sequence[logging.Handler]


class MemoryHandlerOpts(HandlerOpts, total=False):
    """Options for creating a `logging.handlers.MemoryHandler`."""

    handler_type: Required[Literal["memory"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
    capacity: int
    flush_level: int | str
    target: logging.Handler | None
    flush_on_close: bool


# File handlers
########################################################################


class WatchedFileHandlerOpts(FileHandlerOpts, total=False):
    """Options for creating a `logging.WatchedFileHandler`."""

    handler_type: Required[Literal["watched"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]


class RotatingFileHandlerOpts(FileHandlerOpts, total=False):
    """Options for creating a `logging.handlers.RotatingFileHandler`."""

    handler_type: Required[Literal["rotating_file"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
    max_bytes: int
    backup_count: int


class TimedRotatingFileHandlerOpts(FileHandlerOpts, total=False):
    """Kwargs for creating a `TimedRotatingFileHandler`."""

    handler_type: Required[Literal["timed_rotating_file", "timed_file"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
    when: str
    interval: int
    backup_count: int
    utc: bool
    at_time: datetime.time | None
    namer: Callable[[str], str] | None
    rotator: Callable[[str, str], None] | None


class SysLogHandlerOpts(HandlerOpts, total=False):
    """Kwargs for creating a `logging.handlers.SysLogHandler`."""

    handler_type: Required[Literal["syslog"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
    address: str | tuple[str, int]
    facility: str | int
    socktype: SocketKind | None
    timeout: float | None


class SMTPHandlerOpts(HandlerOpts, total=False):
    """Kwargs for creating a `logging.handlers.SMTPHandler`."""

    handler_type: Required[Literal["smtp"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
    mailhost: str | tuple[str, int]
    fromaddr: str
    toaddrs: str | list[str]
    subject: str
    credentials: tuple[str, str] | None
    secure: tuple[()] | tuple[str] | tuple[str, str] | None
    timeout: float


class HTTPHandlerOpts(HandlerOpts, total=False):
    """Kwargs for creating a `logging.handlers.HTTPHandler`."""

    handler_type: Required[Literal["http"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
    host: str
    url: str
    method: Literal["GET", "POST"]
    secure: bool
    credentials: tuple[str, str] | None
    context: SSLContext | None


class SocketHandlerOpts(HandlerOpts, total=False):
    """Kwargs for creating a `logging.handlers.SocketHandler`."""

    handler_type: Required[Literal["socket"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
    host: str
    port: int | None


class DatagramHandlerOpts(HandlerOpts, total=False):
    """Kwargs for creating a `logging.handlers.DatagramHandler`."""

    handler_type: Required[Literal["datagram"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
    host: str
    port: int | None


class NTEventLogHandlerOpts(HandlerOpts, total=False):
    """Kwargs for creating a `logging.handlers.NTEventHandler`."""

    handler_type: Required[Literal["nt_event"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
    appname: str
    dllname: str | None
    logtype: str


class A:  # pylint: disable=too-few-public-methods
    # Ignored unless creating syslog handler
    address: str | tuple[str, int]
    facility: int | str
    socktype: int | SocketKind | None
    syslog_timeout: float | None
    # Ignored unless creating SMTP handler
    mailhost: str | tuple[str, int] | NoDefaultType
    fromaddr: str | NoDefaultType
    toaddrs: str | list[str] | NoDefaultType
    subject: str | NoDefaultType
    smtp_credentials: tuple[str, str] | None
    smtp_secure: tuple[()] | tuple[str] | tuple[str, str] | None
    smtp_timeout: float
    # Ignored unless creating HTTP, socket, or datagram handler
    host: str | NoDefaultType
    # Ignored unless creating HTTP handler
    url: str | NoDefaultType
    http_method: str
    http_secure: bool
    http_credentials: tuple[str, str] | None
    http_context: SSLContext | None
    # Ignored unless creating socket or datagram handler
    port: int | None


# Define valid handler specs
type HandlerSpec = (
    StrOrPathLike  # File path, special string, or existing handler name
    | TextIOLike  # Stream for stream handler
    | logging.Handler  # Pre-configured handler
    # Handler specifier plus additional configurations
    | tuple[StrOrPathLike | TextIOLike | logging.Handler, HandlerOpts]
    | tuple[StrOrPathLike, RotatingFileHandlerOpts]
    | tuple[StrOrPathLike, TimedRotatingFileHandlerOpts]
    | tuple[
        StrOrPathLike | TextIOLike | logging.Handler | None, MemoryHandlerOpts
    ]
    | tuple[None, SysLogHandlerOpts]
    | tuple[None, SMTPHandlerOpts]
    | tuple[None, HTTPHandlerOpts]
    | tuple[None, SocketHandlerOpts]
    | tuple[None, DatagramHandlerOpts]
    | tuple[None, NTEventLogHandlerOpts]
    | None  # Default stderr handler
)

# Define logger spec


# Define typed dict for specifying logger keyword arguments
class LoggerKwargs(TypedDict, total=False):
    # Regular keywords, overriden if provided separately
    name: str | None
    level: int
    # Special keywords
    handlers: HandlerSpec | Sequence[HandlerSpec]
    formatter: FormatterSpec
    filters: FilterSpec | Sequence[FilterSpec]
    color: ColorSpec
    json: bool | JsonSpec
    csv: bool | CsvSpec
    logfmt: bool | LogfmtSpec


# Define valid logger specs
type LoggerSpec = (
    str  # Name only
    | int  # Level only
    | tuple[str | None, int]  # Name and level
    | LoggerKwargs  # Keyword arguments
    | tuple[str | None, LoggerKwargs]  # Name and keyword arguments
    | tuple[int, LoggerKwargs]  # Level and keyword arguments
    | tuple[str | None, int, LoggerKwargs]  # Name, level, and keyword args
    | None  # Default name
)
