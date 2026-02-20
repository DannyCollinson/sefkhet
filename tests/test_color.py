"""Tests for `snaplog._color`."""

import logging

from snaplog._color import (
    _ANSI_RESET,
    _LEVELNAME_WIDTH,
    ColorFormatter,
    _get_display_levelname,
    _parse_color_spec,
    get_level_color,
)


def _make_record(
    msg: str = "hello",
    level: int = logging.INFO,
    args: tuple[object, ...] | None = None,
) -> logging.LogRecord:
    """
    Create a minimal LogRecord for testing.

    Args:
        msg (str, optional): Log message. Defaults to `"hello"`.
        level (int, optional): Log level. Defaults to `logging.INFO`.
        args (tuple[object, ...] | None, optional): Format args.
            Defaults to `None`.

    Returns:
        logging.LogRecord: A minimal log record for testing
    """
    return logging.LogRecord(
        name="test",
        level=level,
        pathname="",
        lineno=0,
        msg=msg,
        args=args,
        exc_info=None,
    )


class TestGetLevelColor:
    """Tests for `get_level_color`."""

    @staticmethod
    def test_returns_str() -> None:
        """Return type is always str."""
        assert isinstance(get_level_color(20), str)

    @staticmethod
    def test_does_not_return_reset() -> None:
        """Never returns the bare reset code."""
        for level in (
            -1,
            0,
            1,
            9,
            10,
            19,
            20,
            29,
            30,
            39,
            40,
            49,
            50,
            59,
            60,
            61,
        ):
            assert get_level_color(level) != _ANSI_RESET

    @staticmethod
    def test_level_minus_one_is_pink() -> None:
        """Level -1 (<=0) maps to pink."""
        assert get_level_color(-1) == get_level_color(0)

    @staticmethod
    def test_level_zero_boundary() -> None:
        """Level 0 (<=0) is pink; level 1 (1-9) is blue."""
        assert get_level_color(0) != get_level_color(1)

    @staticmethod
    def test_level_nine_ten_boundary() -> None:
        """Level 9 (1-9) and 10 (10-19) are different colors."""
        assert get_level_color(9) != get_level_color(10)

    @staticmethod
    def test_level_nineteen_twenty_boundary() -> None:
        """Level 19 (10-19) and 20 (20-29) are different colors."""
        assert get_level_color(19) != get_level_color(20)

    @staticmethod
    def test_level_twentynine_thirty_boundary() -> None:
        """Level 29 (20-29) and 30 (30-39) are different colors."""
        assert get_level_color(29) != get_level_color(30)

    @staticmethod
    def test_level_thirtynine_forty_boundary() -> None:
        """Level 39 (30-39) and 40 (40-49) are different colors."""
        assert get_level_color(39) != get_level_color(40)

    @staticmethod
    def test_level_fortynine_fifty_boundary() -> None:
        """Level 49 (40-49) and 50 (>=50) are different colors."""
        assert get_level_color(49) != get_level_color(50)

    @staticmethod
    def test_level_fifty_and_above_same() -> None:
        """Levels 50 and 51 both map to the same color."""
        assert get_level_color(50) == get_level_color(51)

    @staticmethod
    def test_within_range_1_to_9_same() -> None:
        """Levels 1 and 9 both map to the same color."""
        assert get_level_color(1) == get_level_color(9)

    @staticmethod
    def test_within_range_10_to_19_same() -> None:
        """Levels 10 and 19 both map to the same color."""
        assert get_level_color(10) == get_level_color(19)

    @staticmethod
    def test_within_range_20_to_29_same() -> None:
        """Levels 20 and 29 both map to the same color."""
        assert get_level_color(20) == get_level_color(29)

    @staticmethod
    def test_within_range_30_to_39_same() -> None:
        """Levels 30 and 39 both map to the same color."""
        assert get_level_color(30) == get_level_color(39)

    @staticmethod
    def test_within_range_40_to_49_same() -> None:
        """Levels 40 and 49 both map to the same color."""
        assert get_level_color(40) == get_level_color(49)


class TestColorFormatter:  # noqa: PLR0904
    """Tests for `ColorFormatter`."""

    @staticmethod
    def test_off_mode_pads_levelname() -> None:
        """Mode 'off' pads the levelname and does not match plain."""
        fmt = "%(levelname)s | %(message)s"
        plain = logging.Formatter(fmt)
        colored = ColorFormatter(fmt, color="off")
        record = _make_record(level=logging.WARNING)
        result = colored.format(record)
        plain_out = plain.format(record)
        assert "WARNING " in result
        assert result != plain_out

    @staticmethod
    def test_full_mode_starts_with_color_ends_with_reset() -> None:
        """Mode 'full' wraps the entire line in color+reset."""
        colored = ColorFormatter("%(levelname)s | %(message)s", color="full")
        record = _make_record(level=logging.INFO)
        result = colored.format(record)
        color = get_level_color(record.levelno)
        assert result.startswith(color)
        assert result.endswith(_ANSI_RESET)

    @staticmethod
    def test_full_mode_contains_padded_levelname() -> None:
        """Mode 'full' output contains the padded levelname."""
        fmt = "%(levelname)s | %(message)s"
        colored = ColorFormatter(fmt, color="full")
        record = _make_record(level=logging.DEBUG)
        result = colored.format(record)
        assert "DEBUG   " in result

    @staticmethod
    def test_level_mode_wraps_levelname() -> None:
        """Mode 'level' wraps only the level name with color+reset."""
        fmt = "%(levelname)s | %(message)s"
        colored = ColorFormatter(fmt, color="level")
        record = _make_record(level=logging.WARNING)
        color = get_level_color(record.levelno)
        result = colored.format(record)
        wrapped_level = f"{color}WARNING {_ANSI_RESET}"
        assert wrapped_level in result

    @staticmethod
    def test_level_mode_message_not_wrapped() -> None:
        """Mode 'level' does not wrap the message in color codes."""
        msg = "plain_message_xyz"
        fmt = "%(levelname)s | %(message)s"
        colored = ColorFormatter(fmt, color="level")
        record = _make_record(msg=msg, level=logging.ERROR)
        color = get_level_color(record.levelno)
        result = colored.format(record)
        # The message itself should not have color codes around it
        assert f"{color}{msg}" not in result
        assert f"{msg}{_ANSI_RESET}" not in result

    @staticmethod
    def test_level_mode_restores_levelname() -> None:
        """Mode 'level' restores record.levelname after formatting."""
        colored = ColorFormatter("%(levelname)s | %(message)s", color="level")
        record = _make_record(level=logging.ERROR)
        orig_levelname = record.levelname
        colored.format(record)
        assert record.levelname == orig_levelname

    @staticmethod
    def test_msg_mode_wraps_message() -> None:
        """Mode 'msg' wraps the message in color+reset."""
        msg = "hello world"
        fmt = "%(levelname)s | %(message)s"
        colored = ColorFormatter(fmt, color="msg")
        record = _make_record(msg=msg, level=logging.INFO)
        color = get_level_color(record.levelno)
        result = colored.format(record)
        wrapped_msg = f"{color}{msg}{_ANSI_RESET}"
        assert wrapped_msg in result

    @staticmethod
    def test_msg_mode_levelname_not_wrapped() -> None:
        """Mode 'msg' does not wrap the level name in color codes."""
        fmt = "%(levelname)s | %(message)s"
        colored = ColorFormatter(fmt, color="msg")
        record = _make_record(level=logging.CRITICAL)
        color = get_level_color(record.levelno)
        result = colored.format(record)
        assert f"{color}CRITICAL{_ANSI_RESET}" not in result

    @staticmethod
    def test_msg_mode_restores_msg_and_args() -> None:
        """Mode 'msg' fully restores record.msg and record.args."""
        colored = ColorFormatter("%(levelname)s | %(message)s", color="msg")
        record = _make_record(msg="val=%s", args=("42",), level=logging.DEBUG)
        orig_msg = record.msg
        orig_args = record.args
        colored.format(record)
        assert record.msg == orig_msg
        assert record.args == orig_args

    @staticmethod
    def test_msg_mode_with_args_formats_correctly() -> None:
        """Mode 'msg' works when record.args is non-None."""
        fmt = "%(message)s"
        colored = ColorFormatter(fmt, color="msg")
        record = _make_record(msg="x=%s", args=("99",), level=logging.INFO)
        color = get_level_color(record.levelno)
        result = colored.format(record)
        assert f"{color}x=99{_ANSI_RESET}" in result

    @staticmethod
    def test_partial_mode_levelname_region_colored() -> None:
        """Mode 'partial' colors the level name region."""
        fmt = "%(levelname)s | %(message)s"
        colored = ColorFormatter(fmt, color="partial")
        record = _make_record(level=logging.WARNING)
        color = get_level_color(record.levelno)
        result = colored.format(record)
        assert result.startswith(color)
        assert _ANSI_RESET in result

    @staticmethod
    def test_partial_mode_message_not_colored() -> None:
        """Mode 'partial' does not color the message."""
        msg = "uncolored_message"
        fmt = "%(levelname)s | %(message)s"
        colored = ColorFormatter(fmt, color="partial")
        record = _make_record(msg=msg, level=logging.INFO)
        result = colored.format(record)
        # The plain message text appears after the reset code
        reset_idx = result.index(_ANSI_RESET)
        tail = result[reset_idx + len(_ANSI_RESET) :]
        assert msg in tail or msg in result

    @staticmethod
    def test_partial_mode_restores_msg_and_args() -> None:
        """Mode 'partial' fully restores record.msg and record.args."""
        colored = ColorFormatter("%(levelname)s | %(message)s", color="partial")
        record = _make_record(msg="v=%s", args=("7",), level=logging.WARNING)
        orig_msg = record.msg
        orig_args = record.args
        colored.format(record)
        assert record.msg == orig_msg
        assert record.args == orig_args

    @staticmethod
    def test_partial_mode_with_args_formats_correctly() -> None:
        """Mode 'partial' works when record.args is non-None."""
        fmt = "%(levelname)s | %(message)s"
        colored = ColorFormatter(fmt, color="partial")
        record = _make_record(msg="n=%s", args=("5",), level=logging.ERROR)
        result = colored.format(record)
        assert "n=5" in result

    @staticmethod
    def test_off_mode_restores_levelname() -> None:
        """Mode 'off' restores record.levelname after formatting."""
        colored = ColorFormatter("%(levelname)s | %(message)s", color="off")
        record = _make_record(level=logging.WARNING)
        orig_levelname = record.levelname
        colored.format(record)
        assert record.levelname == orig_levelname

    @staticmethod
    def test_full_mode_restores_levelname() -> None:
        """Mode 'full' restores record.levelname after formatting."""
        colored = ColorFormatter("%(levelname)s | %(message)s", color="full")
        record = _make_record(level=logging.INFO)
        orig_levelname = record.levelname
        colored.format(record)
        assert record.levelname == orig_levelname

    @staticmethod
    def test_msg_mode_restores_levelname() -> None:
        """Mode 'msg' restores record.levelname after formatting."""
        colored = ColorFormatter("%(levelname)s | %(message)s", color="msg")
        record = _make_record(level=logging.ERROR)
        orig_levelname = record.levelname
        colored.format(record)
        assert record.levelname == orig_levelname

    @staticmethod
    def test_partial_mode_restores_levelname() -> None:
        """Mode 'partial' restores record.levelname after formatting."""
        colored = ColorFormatter("%(levelname)s | %(message)s", color="partial")
        record = _make_record(level=logging.DEBUG)
        orig_levelname = record.levelname
        colored.format(record)
        assert record.levelname == orig_levelname

    @staticmethod
    def test_no_side_effects_across_calls() -> None:
        """
        Formatting the same record twice produces consistent results
        with no leftover mutations from the first call.
        """
        fmt = "%(levelname)s | %(message)s"
        for mode in ("off", "full", "level", "msg", "partial"):
            colored = ColorFormatter(
                fmt,
                color=mode,
            )
            record = _make_record(msg="side_effect_test", level=logging.INFO)
            result1 = colored.format(record)
            result2 = colored.format(record)
            assert result1 == result2, f"mode={mode!r} differs on second call"

    @staticmethod
    def test_custom_callable_colormap_full_mode() -> None:
        """Custom callable colormap is used in 'full' mode."""
        sentinel = "\033[99m"
        colored = ColorFormatter(
            "%(levelname)s | %(message)s",
            color=("full", lambda _: sentinel),
        )
        record = _make_record(level=logging.INFO)
        result = colored.format(record)
        assert result.startswith(sentinel)

    @staticmethod
    def test_custom_callable_colormap_level_mode() -> None:
        """Custom callable colormap wraps levelname in 'level' mode."""
        sentinel = "\033[99m"
        colored = ColorFormatter(
            "%(levelname)s | %(message)s",
            color=("level", lambda _: sentinel),
        )
        record = _make_record(level=logging.INFO)
        result = colored.format(record)
        assert sentinel in result
        assert result.index(sentinel) < result.index(_ANSI_RESET)

    @staticmethod
    def test_custom_mapping_colormap_full_mode() -> None:
        """Mapping colormap maps a matched level in 'full' mode."""
        sentinel = "\033[99m"
        colored = ColorFormatter(
            "%(levelname)s | %(message)s",
            color=("full", {logging.INFO: sentinel}),
        )
        record = _make_record(level=logging.INFO)
        result = colored.format(record)
        assert result.startswith(sentinel)

    @staticmethod
    def test_custom_mapping_fallback_for_unmapped_level() -> None:
        """Mapping colormap falls back to default for unmapped level."""
        sentinel = "\033[99m"
        colored = ColorFormatter(
            "%(levelname)s | %(message)s",
            color=("full", {logging.INFO: sentinel}),
        )
        record = _make_record(level=logging.DEBUG)
        result = colored.format(record)
        default_color = get_level_color(logging.DEBUG)
        assert result.startswith(default_color)
        assert not result.startswith(sentinel)


class TestParseColorSpec:
    """Tests for `_parse_color_spec`."""

    @staticmethod
    def test_bare_mode_returns_default_fn() -> None:
        """A bare mode string returns get_level_color as the fn."""
        mode, fn = _parse_color_spec("level")
        assert mode == "level"
        assert fn is get_level_color

    @staticmethod
    def test_tuple_callable_returned_as_is() -> None:
        """A callable colormap is passed through directly."""
        sentinel = "\033[99m"

        def my_fn(_: int) -> str:
            return sentinel

        mode, fn = _parse_color_spec(("full", my_fn))
        assert mode == "full"
        assert fn is my_fn
        assert fn(logging.INFO) == sentinel

    @staticmethod
    def test_tuple_mapping_returns_mapped_value() -> None:
        """Mapping colormap returns the mapped value for matched key."""
        sentinel = "\033[99m"
        mode, fn = _parse_color_spec(("level", {logging.INFO: sentinel}))
        assert mode == "level"
        assert fn(logging.INFO) == sentinel

    @staticmethod
    def test_tuple_mapping_falls_back_for_missing_key() -> None:
        """Mapping falls back to get_level_color for absent key."""
        sentinel = "\033[99m"
        _, fn = _parse_color_spec(("level", {logging.INFO: sentinel}))
        assert fn(logging.DEBUG) == get_level_color(logging.DEBUG)

    @staticmethod
    def test_tuple_empty_mapping_always_falls_back() -> None:
        """An empty mapping always falls back to get_level_color."""
        _, fn = _parse_color_spec(("full", {}))
        for level in (logging.DEBUG, logging.INFO, logging.WARNING):
            assert fn(level) == get_level_color(level)


class TestGetDisplayLevelname:
    """Tests for `_get_display_levelname`."""

    @staticmethod
    def test_registered_levels_padded_to_width() -> None:
        """
        Registered level names are right-padded to _LEVELNAME_WIDTH.
        """  # noqa: D200
        for name in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            result = _get_display_levelname(name)
            assert len(result) == _LEVELNAME_WIDTH
            assert result.startswith(name)

    @staticmethod
    def test_unregistered_level_produces_level_x_format() -> None:
        """'Level 25' becomes 'LEVEL_25', not the Python default."""
        result = _get_display_levelname("Level 25")
        assert result.startswith("LEVEL_25")

    @staticmethod
    def test_unregistered_level_padded_to_width() -> None:
        """
        Unregistered level names are also padded to _LEVELNAME_WIDTH.
        """  # noqa: D200
        result = _get_display_levelname("Level 5")
        assert len(result) == _LEVELNAME_WIDTH
        assert result.startswith("LEVEL_5")

    @staticmethod
    def test_non_level_string_unchanged_except_padding() -> None:
        """Strings that don't match 'Level N' are only padded."""
        result = _get_display_levelname("CUSTOM")
        assert result == "CUSTOM  "
        assert len(result) == _LEVELNAME_WIDTH

    @staticmethod
    def test_level_prefix_without_digit_not_transformed() -> None:
        """'Level X' where X is not a digit is not transformed."""
        result = _get_display_levelname("Level AB")
        assert result.startswith("Level AB")
