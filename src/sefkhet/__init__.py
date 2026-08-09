"""
Complex logging setup made simple.

The `sefkhet` package aims to enable one-step configuration of the
built-in `logging` package, making complex logging setup easy.

The main utilities are the `record`/`rec` function
and the `Scribe` class.

Getting started is as easy as importing and calling `record`:
```
from sefkhet import record

record("I <3 sefkhet!")
```

You can also use the `Scribe` class for more fine-grained control:
```
import sefkhet

scribe = sefkhet.Scribe(handlers="example.log")
scribe.log("I <3 sefkhet!")
```
"""

# Make top-level utilities available
from sefkhet._color import ColorFormatter, get_level_color
from sefkhet._csv import CsvFormatter
from sefkhet._functional import (
    add_filters_to_target,
    add_handlers_to_logger,
    get_filter,
    get_formatter,
    get_handler,
    get_log_level_map,
    get_log_levels,
    get_logger,
)
from sefkhet._json import JsonFormatter
from sefkhet._logfmt import LogfmtFormatter
from sefkhet._object_oriented import Scribe
from sefkhet._one_step import configure_default_logger, log, rec, record

# Make version number available
from sefkhet._version import __version__


# Define public API
__all__ = [  # noqa: RUF022
    # Metadata
    "__version__",
    # Classes
    "ColorFormatter",
    "CsvFormatter",
    "JsonFormatter",
    "LogfmtFormatter",
    "Scribe",
    # Functions
    "add_filters_to_target",
    "add_handlers_to_logger",
    "configure_default_logger",
    "get_filter",
    "get_formatter",
    "get_handler",
    "get_level_color",
    "get_log_level_map",
    "get_log_levels",
    "get_logger",
    "log",
    "rec",
    "record",
]
