"""Color formatting utilities for `snaplog`."""

import logging
from collections.abc import Callable, Mapping
from typing import Any

from snaplog._typing import _ColorMode, _ColorSpec, _FormatStyle


########################################################################
# ANSI constants
########################################################################


_ANSI_RESET = "\033[0m"
_PINK = "\033[38;5;212m"
_BLUE = "\033[94m"
_GREEN = "\033[32m"
_CYAN = "\033[38;5;123m"
_YELLOW = "\033[93m"
_ORANGE = "\033[38;5;214m"
_RED = "\033[91m"
_MAGENTA = "\033[35m"


########################################################################
# Levelname formatting
########################################################################


_LEVELNAME_WIDTH = 8


def _get_display_levelname(levelname: str) -> str:
    if levelname.startswith("Level ") and levelname[6:].isdigit():
        levelname = "LEVEL_" + levelname[6:]
    return levelname.ljust(_LEVELNAME_WIDTH)


########################################################################
# Public utilities
########################################################################


def get_level_color(level: int) -> str:  # noqa: PLR0911
    """
    Returns the ANSI escape code string for the given integer log level.

    The mapping from level to color is:

    - `<= 0` : pink
    - `1-9`  : blue
    - `10-19`: green
    - `20-29`: cyan
    - `30-39`: yellow
    - `40-49`: orange
    - `50-59`: red
    - `>= 59`: magenta

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
    if level <= 59:  # noqa: PLR2004
        return _RED
    return _MAGENTA


def _parse_color_spec(
    color: _ColorSpec,
) -> tuple[_ColorMode, Callable[[int], str]]:
    """
    Parses a `_ColorSpec` into a color mode and a color function.

    Args:
        color (_ColorSpec): Either a bare `_ColorMode` string or a
            tuple of `(_ColorMode, colormap)` where `colormap` is a
            `Callable[[int], str]` or a `Mapping[int, str]`.

    Returns:
        tuple[_ColorMode, Callable[[int], str]]: The color mode and a
            callable that maps an integer log level to an ANSI color
            escape code string
    """
    if not isinstance(color, tuple):
        return color, get_level_color
    mode, colormap = color
    if isinstance(colormap, Mapping):

        def _map_fn(level: int) -> str:
            try:
                return colormap[level]  # pyright: ignore[reportUnknownVariableType]
            except KeyError:
                return get_level_color(level)

        return mode, _map_fn
    return mode, colormap


class ColorFormatter(logging.Formatter):
    """
    A `logging.Formatter` subclass that applies ANSI color codes
    to log output based on the log record's level.

    The scope of colorization is controlled by the `color` mode:

    - `"off"`: no colorization; output is identical to
      `logging.Formatter`
    - `"full"`: the entire formatted line is wrapped in color
    - `"level"`: only the level name is wrapped in color
    - `"msg"`: only the message is wrapped in color
    - `"partial"`: everything except the message is colored
    """

    def __init__(  # noqa: PLR0913
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: _FormatStyle = "%",
        validate: bool = True,  # noqa: FBT001,FBT002
        *,
        defaults: Mapping[str, Any] | None = None,
        color: _ColorSpec,
    ) -> None:
        """
        Creates a `ColorFormatter` with the given format and color mode.

        Args:
            fmt (str | None, optional): Format string. Defaults to
                `None`.
            datefmt (str | None, optional): Date format string.
                Defaults to `None`.
            style (_FormatStyle, optional): Format style.
                Defaults to `"%"`.
            validate (bool, optional): If `True`, validates the format
                string. Defaults to `True`.
            defaults (Mapping[str, Any] | None, optional): Default
                values for string interpolation. Defaults to `None`.
            color (_ColorSpec): Color mode controlling the scope of
                colorization. Either a bare `_ColorMode` string
                (`"off"`, `"full"`, `"level"`, `"msg"`, or
                `"partial"`) or a tuple of `(_ColorMode, colormap)`
                where `colormap` is a `Callable[[int], str]` or a
                `Mapping[int, str]` for per-level color overrides.
        """
        super().__init__(
            fmt=fmt,
            datefmt=datefmt,
            style=style,
            validate=validate,
            defaults=defaults,
        )
        self._color_mode, self._color_fn = _parse_color_spec(color)

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the log record with ANSI color codes applied
        according to `self._color_mode`.

        Args:
            record (logging.LogRecord): Log record to format

        Returns:
            str: Formatted log record string
        """
        color = self._color_fn(record.levelno)
        reset = _ANSI_RESET
        orig_levelname = record.levelname
        display_levelname = _get_display_levelname(orig_levelname)

        if self._color_mode == "off":
            record.levelname = display_levelname
            result = super().format(record)
            record.levelname = orig_levelname
            return result

        if self._color_mode == "full":
            record.levelname = display_levelname
            result = f"{color}{super().format(record)}{reset}"
            record.levelname = orig_levelname
            return result

        if self._color_mode == "level":
            record.levelname = f"{color}{display_levelname}{reset}"
            result = super().format(record)
            record.levelname = orig_levelname
            return result

        if self._color_mode == "msg":
            orig_msg = record.msg
            orig_args = record.args
            record.levelname = display_levelname
            record.msg = f"{color}{record.getMessage()}{reset}"
            record.args = None
            result = super().format(record)
            record.msg = orig_msg
            record.args = orig_args
            record.levelname = orig_levelname
            return result

        # "partial": color everything except the message
        orig_msg = record.msg
        orig_args = record.args
        record.levelname = display_levelname
        record.msg = f"{reset}{record.getMessage()}{color}"
        record.args = None
        result = f"{color}{super().format(record)}{reset}"
        record.msg = orig_msg
        record.args = orig_args
        record.levelname = orig_levelname
        return result
