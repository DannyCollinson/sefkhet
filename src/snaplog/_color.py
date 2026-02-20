"""Color formatting utilities for `snaplog`."""

import logging
from collections.abc import Mapping
from typing import Any

from snaplog._typing import _ColorMode  # pyright: ignore[reportPrivateUsage]


########################################################################
# ANSI constants
########################################################################


_ANSI_RESET = "\033[0m"
_PINK = "\033[95m"
_BLUE = "\033[94m"
_GREEN = "\033[92m"
_CYAN = "\033[96m"
_YELLOW = "\033[93m"
_ORANGE = "\033[38;5;208m"
_RED = "\033[91m"


########################################################################
# Public utilities
########################################################################


def get_level_color(level: int) -> str:  # noqa: PLR0911
    """
    Returns the ANSI escape code string for the given integer log level.

    The mapping from level to color is:

    - ``<= 0``: pink
    - ``1-9``: blue
    - ``10-19``: green
    - ``20-29``: cyan
    - ``30-39``: yellow
    - ``40-49``: orange
    - ``>= 50``: red

    Args:
        level (int): Integer log level

    Returns:
        str: ANSI escape code string for the given level
    """
    if level <= 0:
        return _PINK
    if level <= 9:  # noqa: PLR2004
        return _BLUE
    if level <= 19:  # noqa: PLR2004
        return _GREEN
    if level <= 29:  # noqa: PLR2004
        return _CYAN
    if level <= 39:  # noqa: PLR2004
        return _YELLOW
    if level <= 49:  # noqa: PLR2004
        return _ORANGE
    return _RED


class ColorFormatter(logging.Formatter):
    """
    A `logging.Formatter` subclass that applies ANSI color codes
    to log output based on the log record's level.

    The scope of colorization is controlled by the ``color`` mode:

    - ``"off"``: no colorization; output is identical to
      `logging.Formatter`
    - ``"full"``: the entire formatted line is wrapped in color
    - ``"level"``: only the level name is wrapped in color
    - ``"msg"``: only the message is wrapped in color
    - ``"partial"``: everything except the message is colored
    """

    def __init__(  # noqa: PLR0913
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: str = "%",
        validate: bool = True,  # noqa: FBT001,FBT002
        *,
        defaults: Mapping[str, Any] | None = None,
        color: _ColorMode,
    ) -> None:
        """
        Creates a `ColorFormatter` with the given format and color mode.

        Args:
            fmt (str | None, optional): Format string. Defaults to
                `None`.
            datefmt (str | None, optional): Date format string.
                Defaults to `None`.
            style (str, optional): Format style. Defaults to `"%"`.
            validate (bool, optional): If `True`, validates the format
                string. Defaults to `True`.
            defaults (Mapping[str, Any] | None, optional): Default
                values for string interpolation. Defaults to `None`.
            color (_ColorMode): Color mode controlling the scope of
                colorization. One of ``"off"``, ``"full"``,
                ``"level"``, ``"msg"``, or ``"partial"``.
        """
        super().__init__(
            fmt=fmt,
            datefmt=datefmt,
            style=style,  # type: ignore[arg-type]
            validate=validate,
            defaults=defaults,
        )
        self._color_mode: _ColorMode = color

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the log record with ANSI color codes applied
        according to ``self._color_mode``.

        Args:
            record (logging.LogRecord): Log record to format

        Returns:
            str: Formatted log record string
        """
        color = get_level_color(record.levelno)
        reset = _ANSI_RESET

        if self._color_mode == "off":
            return super().format(record)

        if self._color_mode == "full":
            return f"{color}{super().format(record)}{reset}"

        if self._color_mode == "level":
            orig_levelname = record.levelname
            record.levelname = f"{color}{orig_levelname}{reset}"
            result = super().format(record)
            record.levelname = orig_levelname
            return result

        if self._color_mode == "msg":
            orig_msg = record.msg
            orig_args = record.args
            record.msg = f"{color}{record.getMessage()}{reset}"
            record.args = None
            result = super().format(record)
            record.msg = orig_msg
            record.args = orig_args
            return result

        # "partial": color everything except the message
        orig_msg = record.msg
        orig_args = record.args
        record.msg = f"{reset}{record.getMessage()}{color}"
        record.args = None
        result = f"{color}{super().format(record)}{reset}"
        record.msg = orig_msg
        record.args = orig_args
        return result
