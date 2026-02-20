"""Typing definitions for `snaplog`."""

import logging
import os
from collections.abc import Callable, Mapping, Sequence
from io import TextIOBase
from types import TracebackType
from typing import Any, Literal, Protocol, TextIO, TypedDict, runtime_checkable


# Define general helpers


# Define type for arguments with no default
# (stolen from typing typeshed)
class _NoDefaultType: ...  # pylint: disable=too-few-public-methods  # pragma: no branch


# Define sentinel for having no default value
NoDefault = _NoDefaultType()

# Define types for info in logging calls
type _SysExcInfoType = (
    tuple[type, BaseException, TracebackType | None] | tuple[None, None, None]
)
type _ExcInfoType = (  # noqa: PYI047
    bool | _SysExcInfoType | BaseException | None
)
type _ArgsType = tuple[Any, ...] | Mapping[str, Any]  # noqa: PYI047

# Define formatter spec

# Define type alias for format string styles
# (stolen from logging typeshed)
type _FormatStyle = Literal["%", "{", "$"]

# Define type alias for color mode
type _ColorMode = Literal["full", "partial", "level", "msg", "off"]


# Define typed dict for specifying formatter keyword arguments
class _FormatterKwargs(TypedDict, total=False):
    fmt: str | None
    datefmt: str | None
    style: _FormatStyle
    validate: bool
    defaults: Mapping[str, Any] | None
    copy: bool
    color: _ColorMode


# Define type alias for valid formatter specs
type _FormatterSpec = (
    str  # Format string
    | logging.Formatter  # Pre-configured formatter
    | _FormatterKwargs  # Keyword arguments for logging.Formatter
    | None  # Default formatter
)

# Define filter spec


# Define type alias for filter-like (stolen from logging typeshed)
@runtime_checkable
class _SupportsFilter(Protocol):  # pylint: disable=too-few-public-methods
    # The filter attribute must exist and have the correct signature
    def filter(
        self, record: logging.LogRecord, /
    ) -> bool | logging.LogRecord: ...


# A filter-like must implement the SupportsFilter protocol
# or be a callable that matches the filter type signature
type _FilterLike = (
    _SupportsFilter | Callable[[logging.LogRecord], bool | logging.LogRecord]
)

# A filter-type must be a filter, implement the SupportsFilter protocol,
# or be a callable that matches the filter type signature
type _FilterType = logging.Filter | _FilterLike  # noqa: PYI047

# Define type alias for valid filter specs
# (name of filter or object supporting filter)
type _FilterSpec = (
    str  # Filter creation argument
    | logging.Filter  # Pre-configured filter
    | tuple[logging.Filter, bool]  # Pre-configured filter + copy argument
    | _FilterLike  # Non-logging.Filter objects that can be used as filters
)

# Define handler spec


# Define typed dict for specifying handler
class _FileHandlerKwargs(  # pyright: ignore[reportUnusedClass]  # noqa: PYI049
    TypedDict, total=False
):
    mode: str
    encoding: str | None
    delay: bool
    errors: str | None


# Define type alias for str/pathlike arguments
type _StrOrPathLike = str | os.PathLike[str] | os.PathLike[bytes]

# Define type alias for TextIO-like arguments
type _TextIOLike = TextIO | TextIOBase


# Define typed dict for specifying handler config using keyword args
class _HandlerKwargs(TypedDict, total=False):
    # Special keywords
    formatter: _FormatterSpec | _NoDefaultType
    filters: _FilterSpec | Sequence[_FilterSpec]
    # Other configurations
    name: str | None
    level: int | None
    copy: bool
    # Ignored unless creating file handler
    mode: str
    encoding: str | None
    delay: bool
    errors: str | None


# Define type alias for valid handler specs
type _HandlerSpec = (
    _StrOrPathLike  # File path, special string, or existing handler name
    | _TextIOLike  # Stream for stream handler
    | logging.Handler  # Pre-configured handler
    # Handler specifier plus additional configurations
    | tuple[_StrOrPathLike | _TextIOLike | logging.Handler, _HandlerKwargs]
    | None  # Default stderr handler
)

# Define logger spec


# Define typed dict for specifying logger keyword arguments
class _LoggerKwargs(TypedDict, total=False):
    # Regular keywords, overriden if provided separately
    name: str
    level: int
    # Special keywords
    handlers: _HandlerSpec | Sequence[_HandlerSpec]
    formatter: _FormatterSpec
    filters: _FilterSpec | Sequence[_FilterSpec]
    color: _ColorMode


# Define type alias for valid logger specs
type _LoggerSpec = (  # noqa: PYI047
    str  # Name only
    | int  # Level only
    | tuple[str | None, int]  # Name and level
    | _LoggerKwargs  # Keyword arguments
    | tuple[str | None, _LoggerKwargs]  # Name and keyword arguments
    | tuple[int, _LoggerKwargs]  # Level and keyword arguments
    | tuple[str | None, int, _LoggerKwargs]  # Name, level, and keyword args
    | None  # Default name
)
