"""Typing definitions for `snaplog`."""

import datetime
import logging
import logging.handlers
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
    type_check_only,
)


# Define general helpers


# Define type for arguments with no default
# (stolen from typing typeshed)
class NoDefaultType: ...  # pylint: disable=too-few-public-methods  # pragma: no branch


# Define sentinel for having no default value
NoDefault = NoDefaultType()

# Define types for info in logging calls
type SysExcInfoType = (
    tuple[type, BaseException, TracebackType | None] | tuple[None, None, None]
)
type ExcInfoType = bool | SysExcInfoType | BaseException | None
type ArgsType = tuple[Any, ...] | Mapping[str, Any]

# Define formatter spec

# Define type alias for format string styles
# (stolen from logging typeshed)
type FormatStyle = Literal["%", "{", "$"]

# Define type alias for color mode
type ColorMode = Literal["full", "partial", "level", "msg", "off"]

# Define type aliases for custom color maps and color spec
type ColorMap = Callable[[int], str] | Mapping[int, str]
type ColorSpec = ColorMode | tuple[ColorMode, ColorMap]


# Define typed dict for JSON formatter spec
class JsonSpec(TypedDict, total=False):
    fields: Sequence[str]
    indent: int | None
    ensure_ascii: bool
    sort_keys: bool


# Define typed dict for CSV formatter spec
class CsvSpec(TypedDict, total=False):
    fields: Sequence[str]
    delimiter: str
    quoting: int
    header: bool


# Define typed dict for logfmt formatter spec
class LogfmtSpec(TypedDict, total=False):
    fields: Sequence[str]
    sort_keys: bool


# Define type alias for handler type discriminator
type HandlerType = Literal[
    "stream",
    "file",
    "watched_file",
    "rotating_file",
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
    "nt_event",
]


# Define typed dict for specifying formatter keyword arguments
class FormatterKwargs(TypedDict, total=False):
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


# Define type alias for valid formatter specs
type FormatterSpec = (
    str  # Format string
    | logging.Formatter  # Pre-configured formatter
    | FormatterKwargs  # Keyword arguments for logging.Formatter
    | None  # Default formatter
)

# Define filter spec


# Define type alias for filter-like (stolen from logging typeshed)
@runtime_checkable
class SupportsFilter(Protocol):  # pylint: disable=too-few-public-methods
    # The filter attribute must exist and have the correct signature
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

# Define type alias for valid filter specs
# (name of filter or object supporting filter)
type FilterSpec = (
    str  # Filter creation argument
    | logging.Filter  # Pre-configured filter
    | tuple[logging.Filter, bool]  # Pre-configured filter + copy argument
    | FilterLike  # Non-logging.Filter objects that can be used as filters
)

# Define handler spec


# Define typed dict for specifying handler
class FileHandlerKwargs(TypedDict, total=False):
    mode: str
    encoding: str | None
    delay: bool
    errors: str | None


# Define type alias for str/pathlike arguments
type StrOrPathLike = str | os.PathLike[str] | os.PathLike[bytes]

# Define type alias for TextIO-like arguments
type TextIOLike = TextIO | TextIOBase

# Define allowed queue-like objects
# (stolen from logging.handlers typeshed)
T = TypeVar("T")


@type_check_only
class QueueLike(Protocol[T]):
    def get(self) -> T: ...
    def put_nowait(self, item: T, /) -> None: ...


logging.handlers.QueueHandler()
logging.handlers.QueueListener()
logging.handlers.MemoryHandler()


# Define typed dict for specifying handler config using keyword args
class HandlerKwargs(TypedDict, total=False):
    # Special keywords
    formatter: FormatterSpec | NoDefaultType
    filters: FilterSpec | Sequence[FilterSpec]
    # Other configurations
    level: int | None
    name: str | None
    copy: bool
    queued: bool
    buffered: bool
    handler_type: HandlerType
    # Ignored unless creating queue handler/listener or wrapping in pair
    queue: QueueLike[Any] | NoDefaultType
    # Ignored unless creating queue handler
    handler_queue: QueueLike[Any] | NoDefaultType
    # Ignored unless creating queue listener or wrapping in pair
    listener_queue: QueueLike[Any] | NoDefaultType
    listener_handlers: (
        logging.Handler | Sequence[logging.Handler] | NoDefaultType
    )
    respect_handler_level: bool
    # Ignored unless creating/wrapping with memory handler
    capacity: int
    flush_level: int | str
    target: logging.Handler | NoDefaultType | None
    flush_on_close: bool
    # Ignored unless creating file handler
    mode: str
    encoding: str | None
    delay: bool
    errors: str | None
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


class QueueHandlerKwargs(HandlerKwargs, total=False):
    """Kwargs for creating a `logging.handlers.MemoryHandler`."""

    handler_type: Required[Literal["queue_pair", "queue_handler"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
    queue: QueueLike[Any]


class MemoryHandlerKwargs(HandlerKwargs, total=False):
    """Kwargs for creating a `logging.handlers.MemoryHandler`."""

    handler_type: Required[Literal["memory"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
    capacity: Required[int]  # type: ignore[misc] # pyright: ignore[reportGeneralTypeIssues]


class RotatingFileHandlerKwargs(HandlerKwargs, total=False):
    """Kwargs for creating a `logging.handlers.RotatingFileHandler`."""

    handler_type: Required[Literal["rotating_file"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
    max_bytes: int
    backup_count: int


class TimedRotatingFileHandlerKwargs(HandlerKwargs, total=False):
    """Kwargs for creating a `TimedRotatingFileHandler`."""

    handler_type: Required[Literal["timed_rotating_file"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]
    when: str
    interval: int
    backup_count: int
    utc: bool
    at_time: datetime.time | None
    namer: Callable[[str], str] | None
    rotator: Callable[[str, str], None] | None


class SysLogHandlerKwargs(HandlerKwargs, total=False):
    """Kwargs for creating a `logging.handlers.SysLogHandler`."""

    handler_type: Required[Literal["syslog"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]


class SMTPHandlerKwargs(HandlerKwargs, total=False):
    """Kwargs for creating a `logging.handlers.SMTPHandler`."""

    handler_type: Required[Literal["smtp"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]


class HTTPHandlerKwargs(HandlerKwargs, total=False):
    """Kwargs for creating a `logging.handlers.HTTPHandler`."""

    handler_type: Required[Literal["http"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]


class SocketHandlerKwargs(HandlerKwargs, total=False):
    """Kwargs for creating a `logging.handlers.SocketHandler`."""

    handler_type: Required[Literal["socket"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]


class DatagramHandlerKwargs(HandlerKwargs, total=False):
    """Kwargs for creating a `logging.handlers.DatagramHandler`."""

    handler_type: Required[Literal["datagram"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]


class NTEventLogHandlerKwargs(HandlerKwargs, total=False):
    """Kwargs for creating a `logging.handlers.NTEventHandler`."""

    handler_type: Required[Literal["nt_event"]]  # type: ignore[misc] # pyright: ignore[reportIncompatibleVariableOverride]


# Define type alias for valid handler specs
type HandlerSpec = (
    StrOrPathLike  # File path, special string, or existing handler name
    | TextIOLike  # Stream for stream handler
    | logging.Handler  # Pre-configured handler
    # Handler specifier plus additional configurations
    | tuple[StrOrPathLike | TextIOLike | logging.Handler, HandlerKwargs]
    | tuple[StrOrPathLike, RotatingFileHandlerKwargs]
    | tuple[StrOrPathLike, TimedRotatingFileHandlerKwargs]
    | tuple[
        StrOrPathLike | TextIOLike | logging.Handler | None, MemoryHandlerKwargs
    ]
    | tuple[None, SysLogHandlerKwargs]
    | tuple[None, SMTPHandlerKwargs]
    | tuple[None, HTTPHandlerKwargs]
    | tuple[None, SocketHandlerKwargs]
    | tuple[None, DatagramHandlerKwargs]
    | tuple[None, NTEventLogHandlerKwargs]
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


# Define type alias for valid logger specs
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
