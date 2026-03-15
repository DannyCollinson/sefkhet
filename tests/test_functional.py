"""Tests for `snaplog._functional`."""

import atexit
import io
import logging
import logging.handlers
import pathlib
import queue
from typing import Any

import pytest

import snaplog
from snaplog._color import ColorFormatter
from snaplog._functional import (
    _DEFAULT_FMT,
    _DEFAULT_FMT_WITH_NAME,
    _DEFAULT_LOGGER_NAMES,
    _get_default_fmt,
    _maybe_create_handler,
    _maybe_create_special_string_handler,
    _parse_filters_arg,
    _parse_handlers_arg,
    _parse_log_level,
    _wrap_handler_in_queue,
    add_filters_to_target,
    add_handlers_to_logger,
    get_filter,
    get_filter_from_spec,
    get_formatter,
    get_formatter_from_spec,
    get_handler,
    get_handler_from_spec,
    get_log_level_map,
    get_log_levels,
    get_logger,
    get_logger_from_spec,
    set_formatter_for_handler,
    set_formatter_for_logger,
)
from snaplog._typing import (
    _HandlerKwargs,
    _LoggerKwargs,
    _NoDefault,
    _RotatingFileHandlerKwargs,
    _SupportsFilter,
    _TimedRotatingFileHandlerKwargs,
)


class TestGetLogLevelMap:
    """Tests for `get_log_level_map`."""

    @staticmethod
    def test_returns_dict() -> None:
        """Returns a dict."""
        result = get_log_level_map()
        assert isinstance(result, dict)

    @staticmethod
    def test_contains_snaplog_defaults() -> None:
        """Contains all snaplog shorthand and full-name keys."""
        result = get_log_level_map()
        for key in (
            "debug",
            "d",
            "info",
            "i",
            "warning",
            "w",
            "warn",
            "error",
            "e",
            "critical",
            "c",
            "fatal",
            "f",
            "notset",
            "not_set",
            "n",
        ):
            assert key in result

    @staticmethod
    def test_contains_uppercase_variants() -> None:
        """Contains uppercase shorthand variants."""
        result = get_log_level_map()
        for key in ("D", "I", "W", "E", "C", "F", "N"):
            assert key in result

    @staticmethod
    def test_values_are_ints() -> None:
        """All values are integers."""
        result = get_log_level_map()
        assert all(isinstance(v, int) for v in result.values())

    @staticmethod
    def test_includes_custom_registered_level() -> None:
        """A level registered via `logging.addLevelName` appears."""
        logging.addLevelName(99, "MYCUSTOMLEVEL")
        result = get_log_level_map()
        assert "MYCUSTOMLEVEL" in result


class TestGetLogLevels:
    """Tests for `get_log_levels`."""

    @staticmethod
    def test_returns_set() -> None:
        """Returns a set."""
        assert isinstance(get_log_levels(), set)

    @staticmethod
    def test_contains_expected_level_strings() -> None:
        """Set includes expected level strings."""
        levels = get_log_levels()
        assert "debug" in levels
        assert "d" in levels
        assert "warning" in levels


class TestParseLogLevel:
    """Tests for `_parse_log_level`."""

    @staticmethod
    def test_quiet_true_returns_debug_from_str() -> None:
        """quiet=True returns DEBUG regardless of string level."""
        assert _parse_log_level("warning", quiet=True) == logging.DEBUG

    @staticmethod
    def test_quiet_true_returns_debug_from_int() -> None:
        """quiet=True returns DEBUG regardless of int level."""
        assert _parse_log_level(logging.ERROR, quiet=True) == logging.DEBUG

    @staticmethod
    def test_int_level_returned_as_is() -> None:
        """An integer level is returned unchanged."""
        assert _parse_log_level(42) == 42

    @staticmethod
    def test_valid_str_full_name() -> None:
        """Full-name string resolves correctly."""
        assert _parse_log_level("warning") == logging.WARNING

    @staticmethod
    def test_valid_str_shorthand_lowercase() -> None:
        """Lowercase shorthand 'd' resolves to DEBUG."""
        assert _parse_log_level("d") == logging.DEBUG

    @staticmethod
    def test_valid_str_shorthand_uppercase() -> None:
        """Uppercase shorthand 'W' resolves to WARNING."""
        assert _parse_log_level("W") == logging.WARNING

    @staticmethod
    def test_invalid_str_raises_value_error() -> None:
        """An unrecognized string raises ValueError."""
        with pytest.raises(ValueError, match="invalid value for 'level'"):
            _parse_log_level("bogus_level_xyz")


class TestGetFormatter:
    """Tests for `get_formatter`."""

    @staticmethod
    def test_formatter_instance_copy_false(
        simple_formatter: logging.Formatter,
    ) -> None:
        """
        Passing an existing Formatter with
        copy=False returns same object.
        """
        result = get_formatter(fmt=simple_formatter, copy=False)
        assert result is simple_formatter

    @staticmethod
    def test_formatter_instance_copy_true(
        simple_formatter: logging.Formatter,
    ) -> None:
        """
        Passing an existing Formatter with copy=True returns a deepcopy.
        """  # noqa: D200
        result = get_formatter(fmt=simple_formatter, copy=True)
        assert result is not simple_formatter
        assert isinstance(result, logging.Formatter)

    @staticmethod
    def test_string_fmt() -> None:
        """A format string creates a new Formatter."""
        result = get_formatter(fmt="%(message)s")
        assert isinstance(result, logging.Formatter)

    @staticmethod
    def test_none_fmt() -> None:
        """None as fmt creates a Formatter."""
        result = get_formatter(fmt=None)
        assert isinstance(result, logging.Formatter)

    @staticmethod
    def test_default_no_args() -> None:
        """No args creates a Formatter with the default format."""
        result = get_formatter()
        assert isinstance(result, logging.Formatter)
        assert result._fmt is not None

    @staticmethod
    def test_datefmt_style_validate_passed_through() -> None:
        """
        Arguments datefmt and style are forwarded to logging.Formatter.
        """  # noqa: D200
        result = get_formatter(
            fmt="%(message)s", datefmt="%Y", style="%", validate=False
        )
        assert result.datefmt == "%Y"


class TestGetFormatterFromSpec:
    """Tests for `get_formatter_from_spec`."""

    @staticmethod
    def test_dict_spec() -> None:
        """A dict spec is unpacked as kwargs."""
        result = get_formatter_from_spec({"fmt": "%(message)s"})
        assert isinstance(result, logging.Formatter)

    @staticmethod
    def test_str_spec() -> None:
        """A string spec is used as fmt."""
        result = get_formatter_from_spec("%(message)s")
        assert isinstance(result, logging.Formatter)

    @staticmethod
    def test_none_spec() -> None:
        """None spec creates a Formatter with None fmt."""
        result = get_formatter_from_spec(None)
        assert isinstance(result, logging.Formatter)

    @staticmethod
    def test_formatter_instance_spec(
        simple_formatter: logging.Formatter,
    ) -> None:
        """
        A Formatter instance spec returns the same object (copy=False).
        """  # noqa: D200
        result = get_formatter_from_spec(simple_formatter)
        assert result is simple_formatter


class TestGetFilter:
    """Tests for `get_filter`."""

    @staticmethod
    def test_filter_instance_copy_false(simple_filter: logging.Filter) -> None:
        """Passing a Filter with copy=False returns the same object."""
        result = get_filter(filt=simple_filter, copy=False)
        assert result is simple_filter

    @staticmethod
    def test_filter_instance_copy_true(simple_filter: logging.Filter) -> None:
        """Passing a Filter with copy=True returns a deepcopy."""
        result = get_filter(filt=simple_filter, copy=True)
        assert result is not simple_filter
        assert isinstance(result, logging.Filter)

    @staticmethod
    def test_str_creates_filter() -> None:
        """A string creates a logging.Filter with that name."""
        result = get_filter(filt="myapp")
        assert isinstance(result, logging.Filter)
        assert result.name == "myapp"

    @staticmethod
    def test_empty_str_creates_filter() -> None:
        """An empty string creates a logging.Filter."""
        result = get_filter(filt="")
        assert isinstance(result, logging.Filter)


class TestGetFilterFromSpec:
    """Tests for `get_filter_from_spec`."""

    @staticmethod
    def test_str_spec() -> None:
        """A string spec creates a Filter."""
        result = get_filter_from_spec("myapp")
        assert isinstance(result, logging.Filter)

    @staticmethod
    def test_filter_instance_spec(simple_filter: logging.Filter) -> None:
        """
        A Filter instance spec returns the same object (copy=False).
        """  # noqa: D200
        result = get_filter_from_spec(simple_filter)
        assert result is simple_filter

    @staticmethod
    def test_tuple_spec_copy_false(simple_filter: logging.Filter) -> None:
        """A (filter, False) tuple returns the same object."""
        result = get_filter_from_spec((simple_filter, False))
        assert result is simple_filter

    @staticmethod
    def test_tuple_spec_copy_true(simple_filter: logging.Filter) -> None:
        """A (filter, True) tuple returns a deepcopy."""
        result = get_filter_from_spec((simple_filter, True))
        assert result is not simple_filter
        assert isinstance(result, logging.Filter)

    @staticmethod
    def test_invalid_spec_raises_type_error() -> None:
        """An invalid spec raises TypeError."""
        with pytest.raises(TypeError):
            get_filter_from_spec(
                42  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]
            )


class TestMaybeCreateSpecialStringHandler:
    """Tests for `_maybe_create_special_string_handler`."""

    @staticmethod
    def test_stdout_lowercase() -> None:
        """'stdout' creates a StreamHandler targeting sys.stdout."""
        import sys

        result = _maybe_create_special_string_handler(core="stdout", copy=False)
        assert isinstance(result, logging.StreamHandler)
        assert result.stream is sys.stdout  # pyright: ignore[reportUnknownMemberType]

    @staticmethod
    def test_stdout_uppercase() -> None:
        """'STDOUT' also matches (capitalization variant)."""
        import sys

        result = _maybe_create_special_string_handler(core="STDOUT", copy=False)
        assert isinstance(result, logging.StreamHandler)
        assert result.stream is sys.stdout  # pyright: ignore[reportUnknownMemberType]

    @staticmethod
    def test_stderr_lowercase() -> None:
        """'stderr' creates a StreamHandler targeting sys.stderr."""
        import sys

        result = _maybe_create_special_string_handler(core="stderr", copy=False)
        assert isinstance(result, logging.StreamHandler)
        assert result.stream is sys.stderr  # pyright: ignore[reportUnknownMemberType]

    @staticmethod
    def test_null_lowercase() -> None:
        """'null' creates a NullHandler."""
        result = _maybe_create_special_string_handler(core="null", copy=False)
        assert isinstance(result, logging.NullHandler)

    @staticmethod
    def test_null_uppercase() -> None:
        """'NULL' also matches."""
        result = _maybe_create_special_string_handler(core="NULL", copy=False)
        assert isinstance(result, logging.NullHandler)

    @staticmethod
    def test_existing_named_handler_copy_false(
        named_handler: tuple[logging.NullHandler, str],
    ) -> None:
        """A handler's registered name returns the same object."""
        hdlr, name = named_handler
        result = _maybe_create_special_string_handler(core=name, copy=False)
        assert result is hdlr

    @staticmethod
    def test_existing_named_handler_copy_true(
        named_handler: tuple[logging.NullHandler, str],
    ) -> None:
        """
        A handler's registered name with copy=True returns a deepcopy.
        """  # noqa: D200
        hdlr, name = named_handler
        result = _maybe_create_special_string_handler(core=name, copy=True)
        assert result is not hdlr
        assert isinstance(result, logging.NullHandler)

    @staticmethod
    def test_non_matching_string_returns_none() -> None:
        """An unrecognized non-special string returns None."""
        result = _maybe_create_special_string_handler(
            core="/definitely/not/a/handler/name", copy=False
        )
        assert result is None


class TestMaybeCreateHandler:
    """Tests for `_maybe_create_handler`."""

    @staticmethod
    def _call(core: object, *, copy: bool = False) -> logging.Handler | None:
        """
        Helper to call with default file handler params.

        Args:
            core (object): Used as `core` argument
                to `snaplog._functional._maybe_create_handler`
            copy (bool, optional): Used as `copy` argument
                to `snaplog._functional._maybe_create_handler`

        Returns:
            logging.Handler | None: Returns the result of calling
                `snaplog._functional._maybe_create_handler` with
                default values for all file handler params

        """
        return _maybe_create_handler(
            core=core,  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]
            handler_type="file",
            mode="a",
            encoding="utf-8",
            delay=False,
            errors=None,
            max_bytes=0,
            backup_count=0,
            when="h",
            interval=1,
            utc=False,
            at_time=None,
            namer=None,
            rotator=None,
            copy=copy,
        )

    def test_handler_instance_copy_false(
        self, null_handler: logging.NullHandler
    ) -> None:
        """
        Passing an existing Handler with copy=False returns same object.
        """  # noqa: D200
        result = self._call(null_handler, copy=False)
        assert result is null_handler

    def test_handler_instance_copy_true(
        self, null_handler: logging.NullHandler
    ) -> None:
        """
        Passing an existing Handler with copy=True returns a deepcopy.
        """  # noqa: D200
        result = self._call(null_handler, copy=True)
        assert result is not null_handler
        assert isinstance(result, logging.NullHandler)

    def test_none_creates_stderr_stream_handler(self) -> None:
        """None creates a StreamHandler targeting sys.stderr."""
        import sys

        result = self._call(None)
        assert isinstance(result, logging.StreamHandler)
        assert result.stream is sys.stderr  # pyright: ignore[reportUnknownMemberType]

    def test_stdout_string(self) -> None:
        """'stdout' string creates a StreamHandler for stdout."""
        import sys

        result = self._call("stdout")
        assert isinstance(result, logging.StreamHandler)
        assert result.stream is sys.stdout  # pyright: ignore[reportUnknownMemberType]

    def test_stderr_string(self) -> None:
        """'stderr' string creates a StreamHandler for stderr."""
        import sys

        result = self._call("stderr")
        assert isinstance(result, logging.StreamHandler)
        assert result.stream is sys.stderr  # pyright: ignore[reportUnknownMemberType]

    def test_null_string(self) -> None:
        """'null' string creates a NullHandler."""
        result = self._call("null")
        assert isinstance(result, logging.NullHandler)

    def test_named_handler_string(
        self, named_handler: tuple[logging.NullHandler, str]
    ) -> None:
        """A registered handler name returns the named handler."""
        hdlr, name = named_handler
        result = self._call(name, copy=False)
        assert result is hdlr

    @staticmethod
    def _call_with_path(
        core: object, *, handler_type: str = "file", delay: bool = True
    ) -> logging.Handler | None:
        """
        Helper to call `_maybe_create_handler` with a path core.

        Args:
            core (object): Used as `core` argument
            handler_type (str, optional): Handler type discriminator.
                Defaults to `"file"`.
            delay (bool, optional): If `True`, file open is deferred.
                Defaults to `True`.

        Returns:
            logging.Handler | None: Result of `_maybe_create_handler`

        """
        return _maybe_create_handler(
            core=core,  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]
            handler_type=handler_type,  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]
            mode="a",
            encoding="utf-8",
            delay=delay,
            errors=None,
            max_bytes=0,
            backup_count=0,
            when="h",
            interval=1,
            utc=False,
            at_time=None,
            namer=None,
            rotator=None,
            copy=False,
        )

    def test_path_string_creates_file_handler(self, log_file: str) -> None:
        """A path string creates a FileHandler."""
        result = self._call_with_path(log_file)
        try:
            assert isinstance(result, logging.FileHandler)
        finally:
            if result is not None:  # type: ignore[comparison-overlap] # pragma: no branch
                result.close()

    def test_pathlike_object_creates_file_handler(self, log_file: str) -> None:
        """A Path object creates a FileHandler."""
        path = pathlib.Path(log_file)
        result = self._call_with_path(path)
        try:
            assert isinstance(result, logging.FileHandler)
        finally:
            if result is not None:  # type: ignore[comparison-overlap] # pragma: no branch
                result.close()

    def test_watched_file_handler(self, log_file: str) -> None:
        """handler_type='watched_file' creates WatchedFileHandler."""
        import logging.handlers

        result = self._call_with_path(log_file, handler_type="watched_file")
        try:
            assert isinstance(result, logging.handlers.WatchedFileHandler)
        finally:
            if result is not None:  # type: ignore[comparison-overlap] # pragma: no branch
                result.close()

    @staticmethod
    def test_rotating_file_handler(log_file: str) -> None:
        """handler_type='rotating_file' creates RotatingFileHandler."""
        import logging.handlers

        result = _maybe_create_handler(
            core=log_file,
            handler_type="rotating_file",
            mode="a",
            encoding="utf-8",
            delay=True,
            errors=None,
            max_bytes=1024,
            backup_count=3,
            when="h",
            interval=1,
            utc=False,
            at_time=None,
            namer=None,
            rotator=None,
            copy=False,
        )
        try:
            assert isinstance(result, logging.handlers.RotatingFileHandler)
            assert result.maxBytes == 1024
            assert result.backupCount == 3
        finally:
            if result is not None:  # type: ignore[comparison-overlap] # pragma: no branch
                result.close()

    @staticmethod
    def test_timed_rotating_file_handler(log_file: str) -> None:
        """handler_type='timed_rotating_file' creates handler."""
        import logging.handlers

        result = _maybe_create_handler(
            core=log_file,
            handler_type="timed_rotating_file",
            mode="a",
            encoding="utf-8",
            delay=True,
            errors=None,
            max_bytes=0,
            backup_count=5,
            when="midnight",
            interval=1,
            utc=True,
            at_time=None,
            namer=None,
            rotator=None,
            copy=False,
        )
        try:
            assert isinstance(result, logging.handlers.TimedRotatingFileHandler)
            assert result.backupCount == 5
            assert result.utc is True
        finally:
            if result is not None:  # type: ignore[comparison-overlap] # pragma: no branch
                result.close()

    @staticmethod
    def test_timed_rotating_file_handler_namer_rotator(log_file: str) -> None:
        """TimedRotatingFileHandler accepts namer and rotator."""
        import logging.handlers

        def _namer(name: str) -> str:
            return name + ".gz"  # pragma: no cover

        def _rotator(source: str, dest: str) -> None:
            pass  # pragma: no cover

        result = _maybe_create_handler(
            core=log_file,
            handler_type="timed_rotating_file",
            mode="a",
            encoding="utf-8",
            delay=True,
            errors=None,
            max_bytes=0,
            backup_count=0,
            when="h",
            interval=1,
            utc=False,
            at_time=None,
            namer=_namer,
            rotator=_rotator,
            copy=False,
        )
        try:
            assert isinstance(result, logging.handlers.TimedRotatingFileHandler)
            assert result.namer is _namer
            assert result.rotator is _rotator
        finally:
            if result is not None:  # type: ignore[comparison-overlap] # pragma: no branch
                result.close()

    def test_textiobase_creates_stream_handler(
        self, string_io_stream: io.StringIO
    ) -> None:
        """
        A TextIOBase instance creates a StreamHandler for that stream.
        """  # noqa: D200
        result = self._call(string_io_stream)
        assert isinstance(result, logging.StreamHandler)
        assert result.stream is string_io_stream  # pyright: ignore[reportUnknownMemberType]

    def test_invalid_type_returns_none(self) -> None:
        """An unrecognized type returns None."""
        result = self._call(42)
        assert result is None


class TestSetFormatterForHandler:
    """Tests for `set_formatter_for_handler`."""

    @staticmethod
    def test_sets_formatter_with_string(
        null_handler: logging.NullHandler,
    ) -> None:
        """A string fmt is set as the handler's formatter."""
        set_formatter_for_handler(null_handler, fmt="%(message)s")
        assert null_handler.formatter is not None

    @staticmethod
    def test_sets_formatter_with_formatter_instance_copy_true(
        null_handler: logging.NullHandler, simple_formatter: logging.Formatter
    ) -> None:
        """
        An existing Formatter with copy=True is deepcopied onto handler.
        """  # noqa: D200
        set_formatter_for_handler(null_handler, fmt=simple_formatter, copy=True)
        assert null_handler.formatter is not None
        assert null_handler.formatter is not simple_formatter


class TestParseFiltersArg:
    """Tests for `_parse_filters_arg`."""

    @staticmethod
    def test_str_input() -> None:
        """A string is wrapped in a single-element tuple."""
        result = _parse_filters_arg("myapp")
        assert result == ("myapp",)

    @staticmethod
    def test_filter_instance_input(simple_filter: logging.Filter) -> None:
        """A Filter instance is wrapped as (filter, False)."""
        result = _parse_filters_arg(simple_filter)
        assert result == ((simple_filter, False),)

    @staticmethod
    def test_callable_input() -> None:
        """A callable covers the `callable(filters)` branch."""

        def _filt(*args: Any, **kwargs: Any) -> bool:
            return True  # pragma: no cover

        result = _parse_filters_arg(_filt)
        assert result == (_filt,)

    @staticmethod
    def test_supports_filter_protocol_input(
        protocol_filter: _SupportsFilter,
    ) -> None:
        """
        A non-callable _SupportsFilter object covers the
        `isinstance(filters, _SupportsFilter)` branch.
        """
        assert not callable(protocol_filter)
        result = _parse_filters_arg(protocol_filter)
        assert result == (protocol_filter,)

    @staticmethod
    def test_tuple_filter_copy_pair(simple_filter: logging.Filter) -> None:
        """
        A (Filter, bool) tuple is wrapped in a single-element tuple.
        """  # noqa: D200
        pair = (simple_filter, True)
        result = _parse_filters_arg(pair)
        assert result == (pair,)

    @staticmethod
    def test_sequence_input(simple_filter: logging.Filter) -> None:
        """A list of specs is converted to a tuple."""
        result = _parse_filters_arg(["myapp", simple_filter])
        assert result == ("myapp", simple_filter)


class TestAddFiltersToTarget:
    """Tests for `add_filters_to_target`."""

    @staticmethod
    def test_str_filter_on_logger() -> None:
        """
        A string filter is added to a logger (string branch in loop).
        """  # noqa: D200
        logger = logging.getLogger("test_aft_str")
        add_filters_to_target(logger, "myapp")
        assert len(logger.filters) == 1

    @staticmethod
    def test_filter_instance_on_handler(
        null_handler: logging.NullHandler, simple_filter: logging.Filter
    ) -> None:
        """A Filter instance is added directly (Filter branch)."""
        add_filters_to_target(null_handler, simple_filter)
        assert len(null_handler.filters) == 1

    @staticmethod
    def test_tuple_filter_copy_true(
        null_handler: logging.NullHandler, simple_filter: logging.Filter
    ) -> None:
        """
        A (filter, True) tuple adds a deepcopy
        (tuple branch, copy=True).
        """
        add_filters_to_target(null_handler, (simple_filter, True))
        assert len(null_handler.filters) == 1
        assert null_handler.filters[0] is not simple_filter

    @staticmethod
    def test_tuple_filter_copy_false(
        null_handler: logging.NullHandler, simple_filter: logging.Filter
    ) -> None:
        """
        A (filter, False) adds original (tuple branch, copy=False).
        """  # noqa: D200
        add_filters_to_target(null_handler, (simple_filter, False))
        assert len(null_handler.filters) == 1
        assert null_handler.filters[0] is simple_filter

    @staticmethod
    def test_callable_filter_on_logger() -> None:
        """A callable is added directly (else/callable branch)."""
        logger = logging.getLogger("test_aft_callable")

        def _filt(*args: Any, **kwargs: Any) -> bool:
            return True  # pragma: no cover

        add_filters_to_target(logger, _filt)
        assert len(logger.filters) == 1

    @staticmethod
    def test_multiple_filters_sequence(simple_filter: logging.Filter) -> None:
        """A sequence of filter specs adds all of them."""
        logger = logging.getLogger("test_aft_seq")
        add_filters_to_target(logger, ["myapp", simple_filter])
        assert len(logger.filters) == 2


class TestGetHandler:
    """Tests for `get_handler`."""

    @staticmethod
    def test_invalid_core_raises_value_error() -> None:
        """An unrecognized core type raises ValueError."""
        with pytest.raises(ValueError, match="No handler was created"):
            get_handler(
                core=42  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]
            )

    @staticmethod
    def test_name_assigned() -> None:
        """Keyword argument name sets the handler's name."""
        handler = get_handler(core="null", name="myhandler")
        assert handler.name == "myhandler"

    @staticmethod
    def test_name_none_not_assigned() -> None:
        """Keyword arg name=None leaves the handler's name unset."""
        handler = get_handler(core="null", name=None)
        assert handler.name is None

    @staticmethod
    def test_level_assigned() -> None:
        """Keyword argument level sets the handler's level."""
        handler = get_handler(core="null", level=logging.WARNING)
        assert handler.level == logging.WARNING

    @staticmethod
    def test_level_none_not_assigned() -> None:
        """Kwarg level=None skips setLevel; handler stays at NOTSET."""
        handler = get_handler(core="null", level=None)
        assert handler.level == logging.NOTSET

    @staticmethod
    def test_formatter_set_when_not_nodefault() -> None:
        """A formatter spec sets the handler's formatter."""
        handler = get_handler(core="null", formatter="%(message)s")
        assert handler.formatter is not None

    @staticmethod
    def test_formatter_not_set_when_nodefault() -> None:
        """
        Keyword argument formatter=_NoDefault
        leaves handler formatter as None.
        """
        handler = get_handler(core="null", formatter=_NoDefault)
        assert handler.formatter is None

    @staticmethod
    def test_filters_added() -> None:
        """Keyword argument filters adds filters to the handler."""
        handler = get_handler(core="null", filters="myapp")
        assert len(handler.filters) == 1

    @staticmethod
    def test_default_creates_stderr_handler() -> None:
        """No args creates a StreamHandler."""
        handler = get_handler()
        assert isinstance(handler, logging.StreamHandler)

    @staticmethod
    def test_file_handler_with_mode_encoding_delay(log_file: str) -> None:
        """File handler kwargs (mode, encoding, delay) are forwarded."""
        handler = get_handler(
            core=log_file, mode="w", encoding="utf-8", delay=True
        )
        try:
            assert isinstance(handler, logging.FileHandler)
        finally:
            handler.close()

    @staticmethod
    def test_watched_file_handler_type(log_file: str) -> None:
        """handler_type='watched_file' creates WatchedFileHandler."""
        import logging.handlers

        handler = get_handler(
            core=log_file, handler_type="watched_file", delay=True
        )
        try:
            assert isinstance(handler, logging.handlers.WatchedFileHandler)
        finally:
            handler.close()

    @staticmethod
    def test_rotating_file_handler_type(log_file: str) -> None:
        """handler_type='rotating_file' with max_bytes/backup_count."""
        import logging.handlers

        handler = get_handler(
            core=log_file,
            handler_type="rotating_file",
            max_bytes=2048,
            backup_count=2,
            delay=True,
        )
        try:
            assert isinstance(handler, logging.handlers.RotatingFileHandler)
            assert handler.maxBytes == 2048
            assert handler.backupCount == 2
        finally:
            handler.close()

    @staticmethod
    def test_timed_rotating_file_handler_type(log_file: str) -> None:
        """handler_type='timed_rotating_file' with time kwargs."""
        import logging.handlers

        handler = get_handler(
            core=log_file,
            handler_type="timed_rotating_file",
            when="midnight",
            interval=1,
            backup_count=7,
            utc=True,
            delay=True,
        )
        try:
            assert isinstance(
                handler, logging.handlers.TimedRotatingFileHandler
            )
            assert handler.backupCount == 7
            assert handler.utc is True
        finally:
            handler.close()


class TestGetHandlerFromSpec:
    """Tests for `get_handler_from_spec`."""

    @staticmethod
    def test_non_tuple_spec() -> None:
        """A non-tuple spec passes core directly to get_handler."""
        result = get_handler_from_spec("null")
        assert isinstance(result, logging.NullHandler)

    @staticmethod
    def test_tuple_spec() -> None:
        """A tuple spec unpacks core and kwargs."""
        result = get_handler_from_spec(
            ("null", {"name": "h1"})  # type: ignore[arg-type]
        )
        assert isinstance(result, logging.NullHandler)
        assert result.name == "h1"

    @staticmethod
    def test_rotating_file_handler_kwargs_spec(log_file: str) -> None:
        """Tuple with _RotatingFileHandlerKwargs creates handler."""
        import logging.handlers

        kwargs = _RotatingFileHandlerKwargs(
            handler_type="rotating_file",
            max_bytes=512,
            backup_count=1,
            delay=True,
        )
        result = get_handler_from_spec((log_file, kwargs))
        try:
            assert isinstance(result, logging.handlers.RotatingFileHandler)
            assert result.maxBytes == 512
        finally:
            result.close()

    @staticmethod
    def test_timed_rotating_file_handler_kwargs_spec(log_file: str) -> None:
        """Tuple with _TimedRotatingFileHandlerKwargs creates it."""
        import logging.handlers

        kwargs = _TimedRotatingFileHandlerKwargs(
            handler_type="timed_rotating_file",
            when="d",
            interval=1,
            backup_count=3,
            delay=True,
        )
        result = get_handler_from_spec((log_file, kwargs))
        try:
            assert isinstance(result, logging.handlers.TimedRotatingFileHandler)
            assert result.backupCount == 3
        finally:
            result.close()


class TestParseHandlersArg:
    """Tests for `_parse_handlers_arg`."""

    @staticmethod
    def test_none_input() -> None:
        """None is wrapped in a single-element tuple."""
        assert _parse_handlers_arg(None) == (None,)

    @staticmethod
    def test_str_input() -> None:
        """A string is wrapped in a single-element tuple."""
        assert _parse_handlers_arg("null") == ("null",)

    @staticmethod
    def test_pathlike_input() -> None:
        """A Path object is wrapped in a single-element tuple."""
        p = pathlib.Path("/example/test.log")
        result = _parse_handlers_arg(p)
        assert result == (p,)

    @staticmethod
    def test_textiobase_input(string_io_stream: io.StringIO) -> None:
        """A StringIO is wrapped in a single-element tuple."""
        result = _parse_handlers_arg(string_io_stream)
        assert result == (string_io_stream,)

    @staticmethod
    def test_handler_instance_input(null_handler: logging.NullHandler) -> None:
        """A Handler instance is wrapped in a single-element tuple."""
        result = _parse_handlers_arg(null_handler)
        assert result == (null_handler,)

    @staticmethod
    def test_tuple_with_dict_input() -> None:
        """A (core, dict) tuple is wrapped in a single-element tuple."""
        spec = ("null", _HandlerKwargs({"name": "h1"}))
        result = _parse_handlers_arg(spec)
        assert result == (spec,)

    @staticmethod
    def test_list_multiple_handlers() -> None:
        """A list of handler specs is converted to a tuple."""
        result = _parse_handlers_arg(["null", "stderr"])
        assert result == ("null", "stderr")


class TestAddHandlersToLogger:
    """Tests for `add_handlers_to_logger`."""

    @staticmethod
    def test_single_handler_added() -> None:
        """A single handler spec adds one handler to the logger."""
        logger = logging.getLogger("test_ahl_single")
        before = len(logger.handlers)
        add_handlers_to_logger(logger, "null")
        assert len(logger.handlers) == before + 1

    @staticmethod
    def test_multiple_handlers_added() -> None:
        """A sequence of specs adds multiple handlers."""
        logger = logging.getLogger("test_ahl_multi")
        before = len(logger.handlers)
        add_handlers_to_logger(logger, ["null", "stderr"])
        assert len(logger.handlers) == before + 2


class TestSetFormatterForLogger:
    """Tests for `set_formatter_for_logger`."""

    @staticmethod
    def test_sets_formatter_on_handler_without_formatter() -> None:
        """
        Handler with no formatter gets formatter set (condition True).
        """  # noqa: D200
        logger = logging.getLogger("test_sfl_no_fmt")
        handler = logging.NullHandler()
        logger.addHandler(handler)
        assert handler.formatter is None

        set_formatter_for_logger(logger, "%(message)s")

        assert handler.formatter is not None

    @staticmethod
    def test_skips_handler_with_formatter_force_false(
        simple_formatter: logging.Formatter,
    ) -> None:
        """
        Handler with formatter skipped when
        force=False (condition False).
        """
        logger = logging.getLogger("test_sfl_has_fmt")
        handler = logging.NullHandler()
        handler.setFormatter(simple_formatter)
        logger.addHandler(handler)

        set_formatter_for_logger(
            logger, "%(levelname)s %(message)s", force=False
        )

        assert handler.formatter is simple_formatter

    @staticmethod
    def test_overwrites_with_force_true(
        simple_formatter: logging.Formatter,
    ) -> None:
        """Handler with formatter is overwritten when force=True."""
        logger = logging.getLogger("test_sfl_force")
        handler = logging.NullHandler()
        handler.setFormatter(simple_formatter)
        logger.addHandler(handler)

        set_formatter_for_logger(
            logger, "%(levelname)s %(message)s", force=True
        )

        assert handler.formatter is not simple_formatter

    @staticmethod
    def test_no_handlers_no_error() -> None:
        """
        Logger with no handlers runs without error (empty loop branch).
        """  # noqa: D200
        logger = logging.getLogger("test_sfl_no_handlers")
        assert len(logger.handlers) == 0
        set_formatter_for_logger(logger, "%(message)s")


class TestGetLogger:
    """Tests for `get_logger`."""

    @staticmethod
    def test_default_name_is_log() -> None:
        """Default name argument produces a logger named 'log'."""
        logger = get_logger()
        assert logger.name == "log"

    @staticmethod
    def test_explicit_name() -> None:
        """An explicit name is applied."""
        logger = get_logger(name="test_gl_explicit")
        assert logger.name == "test_gl_explicit"

    @staticmethod
    def test_none_name_uses_root_logger() -> None:
        """name=None returns the root logger."""
        logger = get_logger(name=None)
        assert logger is logging.root

    @staticmethod
    def test_level_set_by_int() -> None:
        """An integer level is applied."""
        logger = get_logger(name="test_gl_level_int", level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    @staticmethod
    def test_level_set_by_str() -> None:
        """A string level is resolved and applied."""
        logger = get_logger(name="test_gl_level_str", level="warning")
        assert logger.level == logging.WARNING

    @staticmethod
    def test_handlers_added() -> None:
        """Handler specs are added to the logger."""
        logger = get_logger(name="test_gl_handlers", handlers="null")
        assert len(logger.handlers) >= 1

    @staticmethod
    def test_filters_added() -> None:
        """Filter specs are added to the logger."""
        logger = get_logger(name="test_gl_filters", filters="myapp")
        assert len(logger.filters) == 1

    @staticmethod
    def test_formatter_with_no_handlers() -> None:
        """A formatter spec with no handlers runs without error."""
        logger = get_logger(
            name="test_gl_fmt_no_handlers", handlers=(), formatter="%(message)s"
        )
        assert len(logger.handlers) == 0

    @staticmethod
    def test_formatter_set_on_handler_without_one() -> None:
        """
        When formatter is specified and handler has no formatter,
        the formatter IS applied:
        handler.formatter is None → True branch.
        """
        logger = get_logger(
            name="test_gl_fmt_set_on_bare",
            handlers="null",
            formatter="%(message)s",
        )
        assert logger.handlers[-1].formatter is not None

    @staticmethod
    def test_formatter_not_set_on_handler_that_already_has_one() -> None:
        """
        When formatter is specified and handler already has a formatter,
        the outer formatter is NOT applied (condition False branch).
        """
        inner_fmt = "%(message)s"
        outer_fmt = "%(levelname)s %(message)s"
        logger = get_logger(
            name="test_gl_fmt_not_overwrite",
            handlers=("null", _HandlerKwargs({"formatter": inner_fmt})),
            formatter=outer_fmt,
        )
        handler = logger.handlers[-1]
        assert handler.formatter is not None
        assert handler.formatter._fmt == inner_fmt


class TestGetLoggerFromSpec:
    """Tests for `get_logger_from_spec`."""

    @staticmethod
    def test_none_spec() -> None:
        """None spec calls get_logger(name=None) → root logger."""
        result = get_logger_from_spec(None)
        assert result is logging.root

    @staticmethod
    def test_str_spec() -> None:
        """A string spec calls get_logger(name=spec)."""
        result = get_logger_from_spec("test_glfs_str")
        assert result.name == "test_glfs_str"

    @staticmethod
    def test_int_spec() -> None:
        """An int spec calls get_logger(level=spec)."""
        result = get_logger_from_spec(logging.DEBUG)
        assert result.level == logging.DEBUG

    @staticmethod
    def test_dict_spec() -> None:
        """A dict spec is unpacked as kwargs to get_logger."""
        result = get_logger_from_spec(
            {"name": "test_glfs_dict", "level": logging.DEBUG}
        )
        assert result.name == "test_glfs_dict"
        assert result.level == logging.DEBUG

    @staticmethod
    def test_tuple_str_int() -> None:
        """(str, int) applies name and level; len=2, kwargs={}."""
        result = get_logger_from_spec(("test_glfs_str_int", logging.DEBUG))
        assert result.name == "test_glfs_str_int"
        assert result.level == logging.DEBUG

    @staticmethod
    def test_tuple_str_int_kwargs_len3() -> None:
        """
        (str, int, dict) covers the len(spec)==3 branch for kwargs.
        """  # noqa: D200
        result = get_logger_from_spec(
            ("test_glfs_len3", logging.DEBUG, {"filters": ()})
        )
        assert result.name == "test_glfs_len3"
        assert result.level == logging.DEBUG

    @staticmethod
    def test_tuple_none_int() -> None:
        """(None, int) covers the spec[0] is None branch."""
        result = get_logger_from_spec((None, logging.DEBUG))
        assert result is logging.root
        assert result.level == logging.DEBUG

    @staticmethod
    def test_tuple_str_dict() -> None:
        """(str, dict) covers the level is None return path."""
        result = get_logger_from_spec(
            ("test_glfs_str_dict", _LoggerKwargs({"handlers": ()}))
        )
        assert result.name == "test_glfs_str_dict"

    @staticmethod
    def test_tuple_none_dict() -> None:
        """(None, dict) covers None name with kwargs."""
        result = get_logger_from_spec((None, _LoggerKwargs({"handlers": ()})))
        assert result is logging.root

    @staticmethod
    def test_tuple_int_dict() -> None:
        """(int, dict) covers the name=_NoDefault branch."""
        result = get_logger_from_spec(
            (logging.DEBUG, _LoggerKwargs({"handlers": ()}))
        )
        assert result.level == logging.DEBUG


class TestPublicApi:  # pylint: disable=too-few-public-methods
    """
    Verify symbols are exported from the top-level `snaplog` package.
    """  # noqa: D200

    @staticmethod
    def test_public_exports_accessible() -> None:
        """
        All __all__ symbols are accessible on the snaplog namespace.
        """  # noqa: D200
        for name in snaplog.__all__:
            assert hasattr(snaplog, name), f"Missing export: {name}"


class TestGetDefaultFmt:
    """Tests for `_get_default_fmt` and name-aware format strings."""

    @staticmethod
    def test_default_names_return_fmt_without_name() -> None:
        """Default logger names produce a format without %(name)s."""
        for name in (None, "root", "log", "snaplogger"):
            result = _get_default_fmt(name)
            assert result == _DEFAULT_FMT
            assert "%(name)s" not in result

    @staticmethod
    def test_custom_name_returns_fmt_with_name() -> None:
        """A non-default name produces a format with %(name)s."""
        result = _get_default_fmt("myapp")
        assert result == _DEFAULT_FMT_WITH_NAME
        assert "%(name)s" in result

    @staticmethod
    def test_auto_numbered_name_returns_fmt_with_name() -> None:
        """Auto-numbered names like 'log0' include %(name)s."""
        result = _get_default_fmt("log0")
        assert result == _DEFAULT_FMT_WITH_NAME

    @staticmethod
    def test_default_logger_names_frozenset() -> None:
        """_DEFAULT_LOGGER_NAMES contains the expected values."""
        assert (
            frozenset({None, "root", "log", "snaplogger"})
            == _DEFAULT_LOGGER_NAMES
        )

    @staticmethod
    def test_get_logger_custom_name_has_name_in_fmt() -> None:
        """
        get_logger with non-default name auto-creates
        a formatter that includes %(name)s.
        """
        logger = get_logger(name="test_gdf_custom", handlers="null")
        handler = logger.handlers[-1]
        assert handler.formatter is not None
        assert "%(name)s" in handler.formatter._fmt  # type: ignore[operator] # pyright: ignore[reportOperatorIssue]

    @staticmethod
    def test_get_logger_default_name_no_name_in_fmt() -> None:
        """
        get_logger with default name 'log' auto-creates
        a formatter without %(name)s.
        """
        logger = get_logger(name="log", handlers="null")
        handler = logger.handlers[-1]
        assert handler.formatter is not None
        assert "%(name)s" not in handler.formatter._fmt  # type: ignore[operator] # pyright: ignore[reportOperatorIssue]

    @staticmethod
    def test_get_logger_none_name_no_name_in_fmt() -> None:
        """
        get_logger with name=None auto-creates
        a formatter without %(name)s.
        """
        logger = get_logger(name=None, handlers="null")
        handler = logger.handlers[-1]
        assert handler.formatter is not None
        assert "%(name)s" not in handler.formatter._fmt  # type: ignore[operator] # pyright: ignore[reportOperatorIssue]

    @staticmethod
    def test_explicit_formatter_not_overridden() -> None:
        """
        When user provides an explicit formatter,
        the name logic does not interfere.
        """
        logger = get_logger(
            name="test_gdf_explicit_fmt",
            handlers="null",
            formatter="%(message)s",
        )
        handler = logger.handlers[-1]
        assert handler.formatter is not None
        assert handler.formatter._fmt == "%(message)s"

    @staticmethod
    def test_set_formatter_for_logger_default_custom() -> None:
        """
        set_formatter_for_logger with default fmt uses
        name-aware format for custom-named loggers.
        """
        logger = logging.getLogger("test_gdf_sfl_custom")
        handler = logging.NullHandler()
        logger.addHandler(handler)
        set_formatter_for_logger(logger)
        assert handler.formatter is not None
        assert "%(name)s" in handler.formatter._fmt  # type: ignore[operator] # pyright: ignore[reportOperatorIssue]

    @staticmethod
    def test_set_formatter_for_logger_default_builtin() -> None:
        """
        set_formatter_for_logger with default fmt uses format
        without %(name)s for default-named loggers.
        """
        logger = logging.getLogger("log")
        handler = logging.NullHandler()
        logger.addHandler(handler)
        set_formatter_for_logger(logger)
        assert handler.formatter is not None
        assert "%(name)s" not in handler.formatter._fmt  # type: ignore[operator] # pyright: ignore[reportOperatorIssue]


class TestGetFormatterColor:
    """Tests for the `color` parameter of `get_formatter`."""

    @staticmethod
    def test_color_full_returns_color_formatter() -> None:
        """color='full' returns a ColorFormatter."""
        result = get_formatter(color="full")
        assert isinstance(result, ColorFormatter)

    @staticmethod
    def test_color_off_returns_plain_formatter() -> None:
        """color='off' returns a plain logging.Formatter."""
        result = get_formatter(color="off")
        assert isinstance(result, logging.Formatter)
        assert not isinstance(result, ColorFormatter)

    @staticmethod
    def test_existing_formatter_ignores_color(
        simple_formatter: logging.Formatter,
    ) -> None:
        """Passing an existing Formatter ignores the color param."""
        result = get_formatter(fmt=simple_formatter, color="full")
        assert result is simple_formatter

    @staticmethod
    def test_tuple_callable_colormap_returns_color_formatter() -> None:
        """Tuple color with callable colormap returns ColorFormatter."""
        result = get_formatter(color=("full", lambda _: "\033[99m"))
        assert isinstance(result, ColorFormatter)

    @staticmethod
    def test_tuple_mapping_colormap_returns_color_formatter() -> None:
        """Tuple color with mapping colormap returns ColorFormatter."""
        result = get_formatter(color=("level", {20: "\033[99m"}))
        assert isinstance(result, ColorFormatter)


class TestGetFormatterFromSpecColor:
    """Tests for the `color` parameter of `get_formatter_from_spec`."""

    @staticmethod
    def test_dict_spec_with_color_key_uses_dict_color() -> None:
        """Dict spec with 'color' key uses that color, not the param."""
        result = get_formatter_from_spec({"color": "full"})
        assert isinstance(result, ColorFormatter)

    @staticmethod
    def test_dict_spec_without_color_uses_param() -> None:
        """Dict spec without 'color' key uses the color param."""
        result = get_formatter_from_spec({"fmt": "%(message)s"}, color="full")
        assert isinstance(result, ColorFormatter)

    @staticmethod
    def test_str_spec_with_color_param() -> None:
        """A string spec with color param creates a ColorFormatter."""
        result = get_formatter_from_spec("%(message)s", color="full")
        assert isinstance(result, ColorFormatter)

    @staticmethod
    def test_tuple_color_with_str_spec_returns_color_formatter() -> None:
        """Tuple color with string spec creates a ColorFormatter."""
        result = get_formatter_from_spec(
            "%(message)s", color=("full", lambda _: "\033[99m")
        )
        assert isinstance(result, ColorFormatter)


class TestGetLoggerColor:
    """Tests for the `color` parameter of `get_logger`."""

    @staticmethod
    def test_color_full_with_nodefault_formatter_creates_formatter() -> None:
        """
        color='full' + formatter=_NoDefault auto-creates ColorFormatter.
        """  # noqa: D200
        logger = get_logger(
            name="test_gl_color_full", handlers="null", color="full"
        )
        handler = logger.handlers[-1]
        assert isinstance(handler.formatter, ColorFormatter)

    @staticmethod
    def test_color_with_formatter_spec_uses_color() -> None:
        """color='full' + formatter spec creates a ColorFormatter."""
        logger = get_logger(
            name="test_gl_color_spec",
            handlers="null",
            formatter="%(message)s",
            color="full",
        )
        handler = logger.handlers[-1]
        assert isinstance(handler.formatter, ColorFormatter)

    @staticmethod
    def test_color_off_with_nodefault_formatter_no_formatter() -> None:
        """
        color='off' + formatter=_NoDefault: handlers have no formatter.
        """  # noqa: D200
        logger = get_logger(
            name="test_gl_color_off", handlers="null", color="off"
        )
        handler = logger.handlers[-1]
        assert handler.formatter is None

    @staticmethod
    def test_tuple_color_creates_color_formatter() -> None:
        """Tuple color with callable creates a ColorFormatter."""
        logger = get_logger(
            name="test_gl_color_tuple",
            handlers="null",
            color=("full", lambda _: "\033[99m"),
        )
        handler = logger.handlers[-1]
        assert isinstance(handler.formatter, ColorFormatter)


class TestQueueHandler:
    """Tests for queued handler support in `get_handler`."""

    @staticmethod
    def test_queued_false_returns_plain_handler() -> None:
        """queued=False (default) returns a non-QueueHandler."""
        handler = get_handler(core="null", queued=False)
        assert not isinstance(handler, logging.handlers.QueueHandler)
        handler.close()

    @staticmethod
    def test_queued_true_returns_queue_handler() -> None:
        """queued=True returns a QueueHandler."""
        handler = get_handler(core="null", queued=True)
        assert isinstance(handler, logging.handlers.QueueHandler)
        assert handler.listener is not None
        handler.listener.stop()
        handler.close()

    @staticmethod
    def test_listener_attribute_is_set() -> None:
        """handler.listener is a QueueListener."""
        handler = get_handler(core="null", queued=True)
        assert isinstance(handler, logging.handlers.QueueHandler)
        assert isinstance(handler.listener, logging.handlers.QueueListener)
        handler.listener.stop()
        handler.close()

    @staticmethod
    def test_listener_is_running() -> None:
        """handler.listener._thread.is_alive() after creation."""
        handler = get_handler(core="null", queued=True)
        assert isinstance(handler, logging.handlers.QueueHandler)
        assert handler.listener is not None
        listener = handler.listener
        assert listener._thread is not None
        assert listener._thread.is_alive()
        listener.stop()
        handler.close()

    @staticmethod
    def test_atexit_registered(monkeypatch: pytest.MonkeyPatch) -> None:
        """atexit.register is called with listener.stop."""
        registered: list[Any] = []

        def _capture(fn: Any) -> None:
            registered.append(fn)

        monkeypatch.setattr(atexit, "register", _capture)
        handler = get_handler(core="null", queued=True)
        assert isinstance(handler, logging.handlers.QueueHandler)
        assert handler.listener is not None
        listener = handler.listener
        assert listener.stop in registered
        listener.stop()
        handler.close()

    @staticmethod
    def test_queue_is_simple_queue() -> None:
        """handler.queue is queue.SimpleQueue."""
        handler = get_handler(core="null", queued=True)
        assert isinstance(handler, logging.handlers.QueueHandler)
        assert isinstance(handler.queue, queue.SimpleQueue)
        assert handler.listener is not None
        handler.listener.stop()
        handler.close()

    @staticmethod
    def test_formatter_on_real_handler_not_queue_handler() -> None:
        """
        Formatter is None on the returned QueueHandler; real
        handler has the formatter.
        """
        fmt = logging.Formatter("%(message)s")
        stream = io.StringIO()
        real = logging.StreamHandler(stream)
        real.setFormatter(fmt)
        handler = get_handler(core=real, formatter=fmt, queued=True)
        assert isinstance(handler, logging.handlers.QueueHandler)
        assert handler.formatter is None
        assert handler.listener is not None
        listener = handler.listener
        assert listener.handlers[0].formatter is fmt
        listener.stop()
        handler.close()

    @staticmethod
    def test_level_on_real_handler() -> None:
        """Level set on real handler; QueueHandler level is NOTSET."""
        stream = io.StringIO()
        real = logging.StreamHandler(stream)
        handler = get_handler(core=real, level=logging.WARNING, queued=True)
        assert isinstance(handler, logging.handlers.QueueHandler)
        assert handler.level == logging.NOTSET
        assert handler.listener is not None
        listener = handler.listener
        assert listener.handlers[0].level == logging.WARNING
        listener.stop()
        handler.close()

    @staticmethod
    def test_record_delivered_end_to_end() -> None:
        """
        Log record reaches stream after listener.stop()
        joins thread.
        """
        stream = io.StringIO()
        real: logging.StreamHandler[io.StringIO] = logging.StreamHandler(stream)
        real.setFormatter(logging.Formatter("%(message)s"))
        real.setLevel(logging.DEBUG)
        logger = logging.getLogger("test_queue_e2e")
        logger.setLevel(logging.DEBUG)
        qh = get_handler(core=real, level=None, queued=True)
        assert isinstance(qh, logging.handlers.QueueHandler)
        logger.addHandler(qh)
        logger.info("hello")
        assert qh.listener is not None
        qh.listener.stop()
        assert "hello" in stream.getvalue()

    @staticmethod
    def test_queued_with_file_path(tmp_path: pytest.TempPathFactory) -> None:
        """
        get_handler with a file path and queued=True
        returns QueueHandler.
        """
        log_file = str(
            tmp_path / "queue_test.log"  # type: ignore[operator] # pyright: ignore[reportOperatorIssue,reportUnknownArgumentType]
        )
        handler = get_handler(core=log_file, queued=True)
        assert isinstance(handler, logging.handlers.QueueHandler)
        assert handler.listener is not None
        handler.listener.stop()
        handler.close()

    @staticmethod
    def test_queued_in_kwargs_dict() -> None:
        """
        get_handler_from_spec with queued=True in kwargs
        returns QueueHandler.
        """
        stream = io.StringIO()
        spec: tuple[Any, Any] = (stream, {"queued": True, "level": None})
        handler = get_handler_from_spec(spec)
        assert isinstance(handler, logging.handlers.QueueHandler)
        assert handler.listener is not None
        handler.listener.stop()
        handler.close()

    @staticmethod
    def test_already_queue_handler_returned_as_is() -> None:
        """
        Passing an existing QueueHandler as core with
        queued=True does not double-wrap.
        """
        q: queue.SimpleQueue[logging.LogRecord] = queue.SimpleQueue()
        existing = logging.handlers.QueueHandler(q)
        result = _wrap_handler_in_queue(existing)
        assert result is existing
        existing.close()
