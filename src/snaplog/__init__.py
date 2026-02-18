"""
Logging for Python in a snap.

The `snaplog` package aims to enable one-step configuration of the
built-in `logging` package, making logging a snap.

The main utilities are the `log` function and `SnapLogger` class.
Getting started is as easy as importing and calling `log`:
```py3
from snaplog import log

log("I <3 snaplog!")
```

You can also use the `SnapLogger` class for more fine-grained control:
```py3
import snaplog

logger = snaplog.SnapLogger(handlers="example.log")
logger.log("I <3 snaplog!")
```
"""

# Make top-level utilities available
from snaplog._functional import (
    add_filters_to_target,
    add_handlers_to_logger,
    get_filter,
    get_formatter,
    get_handler,
    get_log_level_map,
    get_log_levels,
    get_logger,
)
from snaplog._object_oriented import SnapLogger
from snaplog._one_step import configure_default_logger, log

# Make version number available
from snaplog._version import __version__


# Define public API
__all__ = [  # noqa: RUF022
    # Metadata
    "__version__",
    # Classes
    "SnapLogger",
    # Functions
    "add_filters_to_target",
    "add_handlers_to_logger",
    "configure_default_logger",
    "get_filter",
    "get_formatter",
    "get_handler",
    "get_log_level_map",
    "get_log_levels",
    "get_logger",
    "log",
]
