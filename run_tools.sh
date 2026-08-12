#!/usr/bin/env bash

# run_tools.sh

# Run Python dev tools
# (ruff formatting, ruff linting, mypy, pyright,
# pylint, bandit, pydoclint, and pytest)
# with fine-grained control over which tools run,
# the environment they run in, and which targets they cover.

VERSION="1.0.0"

# ======================================================================
# Setup
# ======================================================================

# Shell options
set -uo pipefail
# Set locale to C for consistent numeric formatting (e.g., decimal point)
export LC_NUMERIC=C

# Set default python version to use for Ruff linting
DEFAULT_RUFF_PYTHON='13'

# Check for Bash version 4.4 or higher (to allow empty associative arrays)
if (( \
    BASH_VERSINFO[0] < 4 || (BASH_VERSINFO[0] == 4 && BASH_VERSINFO[1] < 4) \
)); then
    printf \
        'Error: Bash version 4.4+ required (found %s)\n' \
        "$BASH_VERSION" \
        >&2
    exit 16
fi

# Define function 'now' to get current time depending on platform.
# Use EPOCHREALTIME if available (Bash 5.0+), then fall back to date command,
# then use Python as last resort.
if [[ -n "${EPOCHREALTIME:-}" ]]; then
    now() { printf '%s' "$EPOCHREALTIME"; }
elif [[ "$(date +%N)" != 'N' ]]; then
    now() { date +%s.%N; }
else
    now() { python3 -c 'import time; print(time.time())'; }
fi

# format_utc EPOCH_TIME
#   Formats a given epoch time (seconds since 1970-01-01 UTC) into
#   a human-readable UTC timestamp (YYYY-MM-DD HH:MM:SS UTC).
#   Called with the epoch time as $1.
format_utc() {
    local secs="$1"
    # Use date command with GNU date syntax if available
    if date --utc --date "@$secs" +'%Y' > /dev/null 2>&1; then
        date --utc --date "@$secs" +'%Y-%m-%d %H:%M:%S UTC'
    # Try to fall back to BSD/macOS date syntax if GNU date is not available
    elif date --utc -r "$secs" +'%Y' > /dev/null 2>&1; then
        date --utc -r "$secs" +'%Y-%m-%d %H:%M:%S UTC'
    # Otherwise, use Python as a last resort
    else
        local python_cmd='import sys; import time; '
        python_cmd+='print(time.strftime('
        python_cmd+="'%Y-%m-%d %H:%M:%S UTC', time.gmtime(float(sys.argv[1]))"
        python_cmd+='))'
        python3 -c "$python_cmd" "$secs"
    fi
}

# Record start time for total runtime reporting at the end
START_TIME="$(now)"
PRETTY_START_TIME="$(format_utc "$START_TIME")"

# ======================================================================
# Message display functions
# ======================================================================

show_version() { printf '%s v%s\n' "$(basename "$0")" "$VERSION"; }


show_help() {
    cat <<EOF
Usage: $0 [OPTIONS] [TARGETS...]

Description:
    Run Python dev tools with fine-grained control.
    Use --help for detailed descriptions of all options and examples.

Options:
    -p, --project NAME      Project name
                                (default: current directory name)
    -v, --venv PATH         Virtual environment path
                                (default: \$HOME/venvs/NAME/.venv on
                                Windows, .venv on other platforms)
    -c, --config FILE       Config file path (default: pyproject.toml)
    -a, --all               Run all tools (ruff-format, ruff-lint,
                                mypy, pyright, pylint, bandit, and
                                pydoclint; plain 'ruff' implies
                                ruff-format and ruff-lint);
                                default is ruff, mypy, and pyright
    -i, --include TOOLS     Comma-separated tools to add to active set
    -o, --only TOOLS        Comma-separated tools to run exclusively
                                (overrides -a and -i; -e still applies)
    -e, --exclude TOOLS     Comma-separated tools to skip
                                (applied last, overrides all others)
    -t, --test [TARGETS]    Run pytest in addition to the selected
                                tools. More details on -t/--test
                                behavior can be found in the detailed
                                help message (default: pytest not run;
                                pass -t/test as flag to run pytest
                                without explicit targets, or also pass
                                targets as a comma-separated list
                                to run on those targets)
    ...                     Additional options for each tool are
                                available; run with --help to see the
                                full list and detailed descriptions
    -q, --quiet             Suppress all output except for found issues
                                and errors for console output (-q) or
                                console and file output (--quiet).
                                More details on quiet mode behavior can
                                be found in the detailed help message.
                                (default: quiet mode disabled; pass -q
                                as flag to enable quiet mode for
                                console output only or --quiet as flag
                                to enable quiet mode for both console
                                and file output)
    ...                     Additional options controlling output
                                and runtime behavior are available;
                                run with --help to see the full list
                                and detailed descriptions
    -h                      Show the abbreviated help message
                                (this message) and exit
    --help                  Show the detailed help message and exit
    -V, --version           Show version information and exit

Positional:
    TARGETS                 One or more code/test targets
                                (default: src/NAME tests docsrc/source/demos;
                                non-existent defaults are skipped)
EOF
}


show_detailed_help() {
    cat <<EOF
Usage: $0 [OPTIONS] [TARGETS...]

Description:
    Run Python dev tools with fine-grained control.

    By default, runs ruff (formatting and linting), mypy, and pyright,
    skipping any that are not available. Use -a/--all to run all
    available tools (ruff, mypy, pyright, pylint, bandit, pydoclint).
    Use the options -i/--include, -o/--only, and -e/--exclude for finer
    control over which tools run (priority: -i < -a < -o < -e).

    The -t/--test option can also be provided to run pytest, but pytest
    is not considered one of the standard tools and is not included
    when specifying -a/--all and does not use the target list;
    however, it can be included using -i/--include. If no pytest targets
    are provided, it is run without explicit targets (i.e., runs
    `pytest <pytest-opts>`, where <pytest-opts> are any additional
    options provided via --pytest-opts), and if targets are provided,
    they should be given as a comma-separated list, and they are passed
    to pytest but not used for the other tools.

    Per-tool options allow enabling/disabling specific features (e.g.,
    ruff output verbosity, target Python version, preview features;
    mypy daemon mode, pydoclint short docstring checks, automatic
    baseline file handling). The -q/--quiet flag is a global option
    that suppresses all output except errors for console output (-q)
    or for console and file output (--quiet). Plain 'ruff' implies
    ruff-format and ruff-lint, and ruff-format includes import
    sorting unless explicitly disabled via the --ruff-no-sort flag.

    Note that when using any of the "TOOL-opts" options, you MUST use
    the "--TOOL-opts=value" syntax (NOT "--TOOL-opts value" syntax) to
    guarantee that it will be parsed correctly. If providing multiple
    options within a "TOOL-opts" option, the value MUST be quoted so
    that the whole value reaches the script as one argument. The value
    is then tokenized using shell-style quoting rules (whitespace
    separates tokens; single and double quotes group text; a backslash
    escapes the next character), but it is NOT evaluated as shell code.
    Command and arithmetic substitution ($(...) and $((...))) are
    rejected with an error, and globs (e.g., *) and backticks are
    passed through literally instead of being expanded. Environment
    variables ARE expanded by default: $NAME and ${NAME} are replaced
    with their values (empty if unset) in unquoted and double-quoted
    text. To keep a literal '$', wrap the token in single quotes (e.g.,
    '$HOME') or escape it (\$). An unterminated quote or an unsupported
    expansion is reported as an error. As an example, if you want to
    pass the options "--line-length=88" and "--isolated" to ruff-format,
    you would write: --ruff-format-opts='--line-length=88 --isolated'
    noting the use of the single quotes and "--option=value" syntax.

    Runs on specified targets, with defaults to src/NAME/, tests/,
    and docsrc/source/demos/ if they exist.

    This script uses a bit-encoded exit code: If all tools run
    successfully and find no issues, the script exits with code 0. If a
    non-formatting tool finds an issue, a 1 is added to the exit code.
    If a tool fails to run successfully, including pytest, a 2 is added
    to the exit code. If pytest finds a failed test, a 4 is added to the
    exit code. If a bad option is provided, it adds 8 to the exit code.
    If the script itself encounters an error (e.g., reached a bad
    state), it adds 16 to the exit code. The final exit code is the sum
    of these values (e.g., if pylint finds an issue and bandit fails to
    run, the exit code is 1+2=3).

Options:
    -p, --project NAME      Project name
                                (default: current directory name)
    -v, --venv PATH         Virtual environment path
                                (default: \$HOME/venvs/NAME/.venv on
                                Windows, .venv on other platforms)
    -c, --config FILE       Config file path (default: pyproject.toml)
    -a, --all               Run all tools (ruff-format, ruff-lint,
                                mypy, pyright, pylint, bandit, and
                                pydoclint; plain 'ruff' implies
                                ruff-format and ruff-lint);
                                default is ruff, mypy, and pyright
    -i, --include TOOLS     Comma-separated tools to add to active set
    -o, --only TOOLS        Comma-separated tools to run exclusively
                                (overrides -a and -i; -e still applies)
    -e, --exclude TOOLS     Comma-separated tools to skip
                                (applied last, overrides all others)
    -t, --test [TARGETS]    Run pytest in addition to the selected
                                tools. Specifying -a/--all does not
                                include pytest, but it can be included
                                with -i/--include. If no targets are
                                specified, then no targets are passed
                                to pytest, and it is just run as
                                `pytest <pytest-opts>`, where
                                <pytest-opts> are any additional options
                                provided via --pytest-opts. If targets
                                are specified, they should be given as a
                                comma-separated list, and they are
                                passed to pytest but are not used for
                                the other tools. If passing -t as a
                                flag, must be a separate flag (i.e., not
                                combined with non-arg-taking short flags
                                in a cluster (e.g., -at is invalid,
                                but -a -t is valid))
                                (default: pytest not run; pass
                                -t/test as flag to run pytest without
                                explicit targets, and pass -t/test
                                followed by a comma-separated list of
                                targets to run pytest on those targets)
    --ruff-python VERSION   Python minor version for ruff target-version
                                (default: virtual environment's minor
                                Python version; e.g., pass 11 for py311)
    --ruff-full-output      Toggle full output for ruff linting.
                                If enabled, ruff linting is run twice:
                                once with --statistics to get summary
                                stats and once without to get full
                                output, where the summary stats are
                                printed before the full output.
                                If disabled, ruff is run once with
                                --statistics to get summary stats only.
                                (default: use --statistics flag to limit
                                output to summary stats; pass
                                --ruff-full-output as flag to disable
                                --statistics and show all diagnostics)
    --ruff-no-preview       Toggle preview features for ruff linting
                                (default: enabled; pass
                                --ruff-no-preview as flag to disable)
    --ruff-no-sort          Skip import sorting for ruff-format
                                (default: import sorting included in
                                ruff-format; pass --ruff-no-sort
                                as flag to disable)
    --mypy-no-daemon        Run mypy in non-daemon mode
                                (default: run in daemon mode for faster
                                subsequent runs; pass --mypy-no-daemon
                                as flag to disable)
    --mypy-restart-daemon   Restart mypy daemon before running.
                                Also accepted as --mypy-daemon-restart.
                                (default: do not restart daemon; pass
                                --mypy-restart-daemon as flag to restart
                                the daemon on this run)
    --bandit-full-output    Toggle full output for bandit
                                (default: when not in quiet mode,
                                suppress setup output and only display
                                results; pass --bandit-full-output
                                as flag to display all bandit output)
    --doc-style STYLE       Docstring style for pydoclint
                                (default: google;
                                e.g., google, numpy, pep257)
    --doc-no-skip-short     Skip checking short docstrings with
                                pydoclint [see pydoclint docs for
                                details] (default: skip short
                                docstrings; pass --doc-no-skip-short
                                as flag to disable skipping)
    --doc-no-auto-baseline  Check for an existing baseline at
                                .pydoclint-baseline.txt,
                                .pydoclint-baseline, or
                                pydoclint-baseline.txt in the project
                                root, and if not found, run pydoclint
                                with --generate-baseline=True to create
                                one at --doc-baseline if set or at
                                .pydoclint-baseline.txt otherwise.
                                (default: check for existing baseline
                                and generate if not found; pass
                                --doc-no-auto-baseline as flag to
                                disable this behavior)
    --doc-baseline FILE     Baseline file path for pydoclint, intended
                                to enable support for custom baselines
                                and not using a baseline. If set here
                                and in the config file, then this option
                                takes precedence (see pydoclint docs).
                                If --doc-no-auto-baseline is not set,
                                then if this option is set, the provided
                                path will be checked for an existing
                                baseline and used if found, and if not
                                found, a new baseline will be generated
                                at this path; if this option is not set,
                                then the default baseline handling
                                behavior described under
                                --doc-no-auto-baseline will apply.
                                If --doc-no-auto-baseline
                                is set, then if this option is set, the
                                provided path will be used as the
                                baseline file for pydoclint if it
                                exists (otherwise, a warning is printed
                                and no baseline will be used); if this
                                option is not set, then no baseline is
                                used unless set in the config file.
                                If "n", "no", or "none" is specified
                                (case-insensitive), then no baseline
                                file is used, regardless of
                                --doc-no-auto-baseline or config file,
                                and any existing baseline file will be
                                ignored. (default: unset; leave unset to
                                use default baseline handling behavior)
    --doc-full-output       Toggle full output for pydoclint
                                (default: when not in quiet mode,
                                suppress progress output and only
                                display results; pass --doc-full-output
                                as flag to display all pydoclint output)
    --test-full-output      Toggle full output for pytest
                                (default: when not in quiet mode,
                                suppress progress output and only
                                display results; pass --test-full-output
                                as flag to display all pytest output)
    --ruff-format-opts OPTS Additional options to pass to ruff format;
                                an alternative/supplement to using a
                                config file for format-specific
                                settings (e.g.,
                                --ruff-format-opts='--line-length=88')
    --ruff-sort-opts OPTS   Additional options to pass to ruff import
                                sorting; an alternative/supplement to
                                using a config file for
                                import-sorting-specific settings.
                                Note that '--select=I --fix' is implied
                                and should not be included. (e.g.,
                                --ruff-sort-opts='--line-length=88')
    --ruff-lint-opts OPTS   Additional options to pass to ruff linting;
                                an alternative/supplement to using a
                                config file for lint-specific settings.
                                Note that --config and --target-version
                                are implied and should not be included
                                and that --statistics is implied when
                                --ruff-full-output is not included and
                                that --preview is implied when
                                --ruff-no-preview is not included.
                                (e.g., --ruff-lint-opts='--select=E,F')
    --mypy-opts OPTS        Additional options to pass to mypy; an
                                alternative/supplement to using a config
                                file for mypy-specific settings.
                                Not applicable when using daemon mode.
                                Note that --config-file is implied
                                and should not be included.
                                (e.g., --mypy-opts='--strict')
    --dmypy-start-opts OPTS Additional options to pass to dmypy when
                                starting the daemon; not applicable when
                                not using daemon mode or using an
                                already-running daemon. Note that
                                --config-file is implied and should not
                                be included. (e.g.,
                                --dmypy-start-opts='--timeout 60')
    --dmypy-check-opts OPTS Additional options to pass to dmypy when
                                running; not applicable when not using
                                daemon mode (e.g.,
                                --dmypy-check-opts='--verbose')
    --pyright-opts OPTS     Additional options to pass to pyright; an
                                alternative/supplement to using a config
                                file for pyright-specific settings.
                                Note that --project and --venvpath
                                are implied and should not be included.
                                (e.g., --pyright-opts='--level=error')
    --pylint-opts OPTS      Additional options to pass to pylint; an
                                alternative/supplement to using a config
                                file for pylint-specific settings
                                (e.g., --pylint-opts='--disable=C0114')
    --bandit-opts OPTS      Additional options to pass to bandit; an
                                alternative/supplement to using a config
                                file for bandit-specific settings.
                                Note that --recursive and --configfile
                                are implied and should not be included.
                                (e.g., --bandit-opts='--ignore-nosec')
    --pydoclint-opts OPTS   Additional options to pass to pydoclint; an
                                alternative/supplement to using a config
                                file for pydoclint-specific settings.
                                Note that --config, --style,
                                --skip-checking-short-docstrings, and
                                baseline handling options are implied
                                and should not be included. (e.g.,
                                --pydoclint-opts='-scr True -crt False')
    --pytest-opts OPTS      Options to pass to pytest;
                                an alternative/supplement to using a
                                config file for pytest settings. (e.g.,
                                --pytest-opts='ignore=tests/example.py')
    -q, --quiet             Suppress all output except for found issues
                                and errors. If the short version (-q) is
                                passed, quiet mode only applies to
                                console output, so file output, if
                                enabled, is not affected. If the long
                                version (--quiet) is passed, quiet mode
                                applies to both console and file output.
                                Note that the --TOOL-full-output flags
                                are implicitly enabled for file output
                                unless file output is in quiet mode
                                or --no-full-output-file is passed.
                                (default: quiet mode disabled; pass -q
                                as flag to enable quiet mode for
                                console output only or --quiet as flag
                                to enable quiet mode for both console
                                and file output)
    -f, --file [FILE]       Specify a file path to output results to in
                                addition to or instead of stdout/stderr.
                                If "n", "no", or "none",
                                (case-insensitive) disables file
                                output. Note that version and help
                                messages and argument-parsing errors
                                will not be written to a file.
                                Also note that if the file already
                                exists, it will be overwritten.
                                Can also be passed as a flag, which
                                enables file output to the default path.
                                If passing -f as a flag, must be a
                                separate flag (i.e., not combined with
                                non-arg-taking short flags in a cluster
                                (e.g., -af is invalid, but -a -f is
                                valid)) (default: "$LOGFILE" in project
                                root; e.g., "no" or "none" to disable or
                                "logs/example.path" for a custom path)
    --no-file               Disable file output. Overrides -f/--file if
                                both are provided. (default: file output
                                to -f/--file enabled unless -f/--file is
                                "n", "no", or "none" (case-insensitive);
                                pass --no-file as flag to disable file
                                output unconditionally)
    --no-console            Disable console output (stdout/stderr).
                                Note that this does not apply to
                                output emitted due to bad options given,
                                other errors in the script itself, or
                                requests for version or help messages.
                                (default: output to console enabled;
                                pass --no-console as flag to disable)
    --no-full-output-file   If file output is enabled and not in quiet
                                mode, then this disables the implicit
                                enablement of the --TOOL-full-output
                                options for file output. Passing an
                                individual --TOOL-full-output flag
                                in addition to this flag will override
                                full output suppression for that tool.
                                (default: the --TOOL-full-output flags
                                are implicitly enabled for file output;
                                pass --no-full-output-file as flag to
                                disable this behavior and require
                                explicit --TOOL-full-output flags for
                                each tool where full output is desired)
    --no-preserve-prev      Disables preserving a copy of a previous
                                run's log file (if it exists at the
                                same path as the current run's log file)
                                by creating a backup with the extension
                                ".prev" before generating the new file.
                                (default: preserve previous log file
                                by creating a backup with the extension
                                ".prev" if it exists; pass
                                --no-preserve-prev as flag to disable)
    --no-parallel           Disable parallel execution when running
                                multiple non-"ruff-format" tools.
                                (default: parallel execution enabled;
                                pass --no-parallel as flag to disable)
    -h                      Show the abbreviated help message and exit
    --help                  Show the detailed help message
                                (this message) and exit
    -V, --version           Show version information and exit

Positional:
    TARGETS                 One or more code targets
                                (default: src/NAME tests docsrc/source/demos;
                                non-existent defaults are skipped)

Examples:
    $0                                       # Run defaults
    $0 src/mypackage tests                   # Run defaults on custom targets
    $0 -a --quiet                            # Run all tools in quiet mode
    $0 -o ruff,mypy --mypy-restart-daemon    # Run ruff and mypy w/ fresh daemon
    $0 -e mypy                               # Exclude mypy from defaults
    $0 -i pylint                             # Add pylint to defaults
    $0 -a -e mypy,bandit                     # All tools except mypy and bandit
    $0 --ruff-python 14 --ruff-full-output   # Ruff for py3.14 with all output
    $0 -a --doc-no-skip-short            # Check short docstrings with pydoclint
EOF
}


# ======================================================================
# Default option values
# ======================================================================

# General settings
PROJECT_NAME="$(basename "$PWD")"
CONFIG_FILE='pyproject.toml'
VIRTUAL_ENV=''
PARALLEL=1

# Logging and output settings
QUIET_CONSOLE=0
QUIET_FILE=0
LOGFILE='run_tools.log'
CONSOLE=1
FULL_OUTPUT_FILE=1
PRESERVE_PREV_LOG=1

# Ruff settings
RUFF_FORMAT=1
RUFF_SORT=1
RUFF_LINT=1
# Defaults to the virtual environment's Python version, detected later
RUFF_PYTHON=''
RUFF_FULL_OUTPUT=0
RUFF_PREVIEW=1
RUFF_FORMAT_OPTS=()
RUFF_SORT_OPTS=()
RUFF_LINT_OPTS=()

# Mypy settings
DMYPY=1
DMYPY_RESTART=0
MYPY_OPTS=()
DMYPY_START_OPTS=()
DMYPY_CHECK_OPTS=()

# Pyright settings
PYRIGHT_OPTS=()

# Pylint settings
PYLINT_OPTS=()

# Bandit settings
BANDIT_FULL_OUTPUT=0
BANDIT_OPTS=()

# Pydoclint settings
PYDOCLINT_STYLE='google'
PYDOCLINT_SKIP_SHORT=1
PYDOCLINT_AUTO_BASELINE=1
PYDOCLINT_BASELINE_FILE=''
PYDOCLINT_FALLBACK_BASELINE_FILE='.pydoclint-baseline.txt'
PYDOCLINT_FULL_OUTPUT=0
PYDOCLINT_OPTS=()

# Pytest settings
PYTEST=0
PYTEST_TARGETS=()
PYTEST_FULL_OUTPUT=0
PYTEST_OPTS=()

# ======================================================================
# Parse command-line options
# ======================================================================

# Tool-selection flags (final set resolved after all options are parsed)
INCLUDE_TOOLS=''
ONLY_TOOLS=''
EXCLUDE_TOOLS=''
RUN_ALL=0

# ----------------------------------------------------------------------
# Expand short-option clusters before the main parser runs.
#   - No-arg short flags  : -a -q -h -V   (bundleable)
#   - Arg-taking flags    : -p -v -c -i -o -e
#   - Optional arg flags  : -f -t  (error on inclusion in invalid cluster)
# Examples:
#   -aq           -> -a -q
#   -qa           -> -q -a
#   -pmyproject   -> -p myproject
#   -qpmyproject  -> -q -p myproject
#   -p myproject  -> unchanged (already split)
# Unknown clusters are passed through so the main parser can reject them.
# ----------------------------------------------------------------------
EXPANDED_ARGS=()
for arg in "$@"; do
    # Pass through: long options (--foo), non-options, "--", and lone "-"
    if [[ "$arg" != -?* || "$arg" == --* ]]; then
        EXPANDED_ARGS+=("$arg")
        continue
    fi

    # Expand short-option clusters

    # Drop leading dash
    rest="${arg:1}"
    # Iterate through characters in cluster, building an expanded list of args
    cluster=()
    valid=1
    i=0
    while (( i < ${#rest} )); do
        char="${rest:i:1}"
        case "$char" in
            a|q|h|V)
                # If here, got a valid single-letter flag, so accept it
                # and continue to next character in this cluster
                cluster+=("-$char")
                ((i++))
                ;;
            p|v|c|i|o|e)
                # If here, assume the rest of the cluster is the value
                # for this flag (e.g., -pmyproject), so accept the flag with the
                # value and break out of the loop to move on to the next arg
                cluster+=("-$char")
                if (( i + 1 < ${#rest} )); then
                    cluster+=("${rest:i+1}")
                fi
                break
                ;;
            f|t)
                # If here, the arg is optional, but as a flag,
                # it must be separate from other flags

                # Detect combination with other flags
                # by checking position in cluster
                if [[ i -ne 0 ]]; then
                    msg="Error: -$char passed as flag must be separate "
                    msg+="from other flags (e.g., -a$char is invalid, "
                    msg+="but -a -$char is valid)"
                    printf "%s\n" "$msg" >&2
                    exit 8
                fi
                # If -f is the only flag in the cluster, give it the default arg
                if [[ "$char" == 'f' && i -eq 0 && ${#rest} -eq 1 ]]; then
                    cluster+=("-f")
                    cluster+=("$LOGFILE")
                # Otherwise, treat the rest as its argument (e.g., -fmylog.txt)
                else
                    cluster+=("-$char")
                    if (( i + 1 < ${#rest} )); then
                        cluster+=("${rest:i+1}")
                    fi
                fi
                break
                ;;
            *)
                # If here, got a bad option,
                # so mark invalid and break
                # to pass through to main parser for error reporting
                valid=0
                break
                ;;
        esac
    done

    if (( valid )); then
        EXPANDED_ARGS+=("${cluster[@]}")
    else
        # Let the main parser report unknown options
        EXPANDED_ARGS+=("$arg")
    fi
done
set -- "${EXPANDED_ARGS[@]}"

# ----------------------------------------------------------------------
# Expand --long=value into --long value, rejecting =value on boolean flags
# (If a boolean flag is passed with =value, value is treated as a target)
#
# Examples:
#   --ruff-python=14         -> --ruff-python 14
#   --only=ruff,mypy         -> --only ruff,mypy
#   --project=my=weird=name  -> --project my=weird=name
#   --quiet                  -> --quiet                  (no =, unchanged)
#   --                       -> --                       (end-of-options marker)
# ----------------------------------------------------------------------
BOOLEAN_LONG_OPTS=(
    --all
    --bandit-full-output
    --doc-full-output
    --doc-no-auto-baseline
    --doc-no-skip-short
    --help
    --mypy-daemon-restart
    --mypy-no-daemon
    --mypy-restart-daemon
    --no-console
    --no-file
    --no-full-output-file
    --no-parallel
    --no-preserve-prev
    --quiet
    --ruff-full-output
    --ruff-no-preview
    --ruff-no-sort
    --version
)

_is_boolean_long_opt() {
    local needle="$1" opt
    for opt in "${BOOLEAN_LONG_OPTS[@]}"; do
        [[ "$opt" == "$needle" ]] && return 0
    done
    return 1
}

EQ_EXPANDED_ARGS=()
for arg in "$@"; do
    # Add =default to bare --file flag to use default value if no value provided
    # (special case since it can be a flag or have a value)
    [[ "$arg" == '--file' ]] && arg="$arg=$LOGFILE"
    # Split on the first '=' if present, otherwise pass through unchanged
    if [[ "$arg" == --*=* ]]; then
        name="${arg%%=*}"
        value="${arg#*=}"
        if _is_boolean_long_opt "$name"; then
            printf \
                    'Error: %s does not take a value (got %s)\n' \
                    "$name" "$arg" \
                    >&2
            exit 8
        fi
        EQ_EXPANDED_ARGS+=("$name" "$value")
    else
        EQ_EXPANDED_ARGS+=("$arg")
    fi
done
set -- "${EQ_EXPANDED_ARGS[@]}"

# ----------------------------------------------------------------------
# Option parsing helper functions
# ----------------------------------------------------------------------

# require_value OPTION_NAME CANDIDATE_VALUE [IS_OPTS]
#   Verifies that a value was provided for an option that requires one.
#   Called with the option name as $1, the candidate value as $2,
#   and optionally whether or not the option is a <TOOL>_OPTS option as $3.
#   If the candidate value is missing or looks like another option
#   (starts with --), an error is printed and the script exits;
#   the "starts with --" check does not apply for <TOOL>_OPTS options,
#   since they are supposed to have values that may start with "--".
require_value() {
    local option_name="$1" candidate_value="$2" is_opts="${3:-0}"
    if [[ -z "$2" || ("$is_opts" -eq 0 && "$2" == --*) ]]; then
        printf 'Error: %s requires a value\n' "$1" >&2
        exit 8
    fi
}

# parse_comma_list COMMA_LIST ARRAY_NAME
#   Parses a comma-separated list of items into an array.
#   Called with the comma-separated list as $1
#   and the name of the array to populate as $2.
parse_comma_list() {
    local comma_list="$1" array_name="$2"
    IFS=',' read -r -a "$array_name" <<< "$comma_list"
}

# _read_var_ref STRING INDEX
#   Reads a variable reference at a given index from a string and returns
#   its value and the index of the next character after the reference.
#   Called with the string containing a variable expansion as $1
#   and the index to start reading from as $2.
#   The index points at a "$", from which the function parses $NAME or ${NAME},
#   expands it from the environment (empty if unset),
#   and reports via two caller-scoped variables:
#       REPLY_VALUE - the input string with the reference expanded
#       REPLY_NEXT - the index of the first character after the reference
#   Returns 2 on command or arithmetic substitution
#   or an unsupported or unterminated ${...} form.
_read_var_ref() {
    local str="$1" ind="$2" len="${#1}"
    local first_char="${str:ind+1:1}" var_name=''
    REPLY_VALUE=''
    REPLY_NEXT=$(( ind + 1 ))
    # Block command substitution and arithmetic by checking first char for "("
    if [[ "$first_char" == '(' ]]; then
        printf \
            'Error: Command and arithmetic substitution are not allowed: %s\n' \
            "${str:ind}" \
            >&2
        return 2
    fi
    # Handle braced form (${NAME})
    if [[ "$first_char" == '{' ]]; then
        local sub_ind=$(( ind + 2 ))
        # Add each character to the variable name until we hit the closing brace
        while (( sub_ind < len )) && [[ "${str:sub_ind:1}" != '}' ]]; do
            var_name+="${str:sub_ind:1}"
            (( sub_ind++ ))
        done
        # If the end of the string was reached, the "}" never came
        if (( sub_ind >= len )); then
            printf 'Error: Unterminated ${...} in %s' "${str:ind}\n" >&2
            return 2
        fi
        # Make sure the variable name is valid
        if [[ ! "$var_name" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
            printf \
                'Error: Unsupported parameter expansion: ${%s}\n' \
                "$var_name" \
                >&2
            return 2
        fi
        # Set the reply values
        REPLY_VALUE="${!var_name-}"
        REPLY_NEXT=$(( sub_ind + 1 ))
        return 0
    fi
    # Handle bare form ($NAME)
    if [[ "$first_char" =~ [A-Za-z_] ]]; then
        local sub_ind=$(( ind + 1 ))
        # Add each valid character to the variable name until
        # we reach the end of the string or hit an invalid character
        while (( sub_ind < len )) \
                && [[ "${str:sub_ind:1}" =~ [A-Za-z0-9_] ]]; do
            var_name+="${str:sub_ind:1}"
            (( sub_ind++ ))
        done
        # Set the reply values
        REPLY_VALUE="${!var_name-}"
        REPLY_NEXT="$sub_ind"
        return 0
    fi
    # If here, got a lone "$" (e.g., "$", "$1", "$$"), so use a literal "$"
    REPLY_VALUE='$'
    return 0
}

# split_opts OPT_STRING DESTINATION_ARRAY
#   Splits a string of options into an array,
#   honoring single and double quotes and backslash escapes
#   and expanding environment variables ($NAME and ${NAME})
#   by default in unquoted and double-quoted text;
#   single quotes are fully literal.
#   Called with the string of options as $1 and
#   the name of the destination array as $2.
#   The array is populated with the split options by the function.
#   Command and arithmetic substitution and globbing are NOT performed.
#   Expanded values are inserted literally (never re-split or re-globbed).
#   Returns 2 on a parse error
#   (e.g., unterminated quote, disallowed or unsupported expansion).
split_opts() {
    local opt_string="$1"
    local -n dest_array="$2"
    local ind=0 len="${#opt_string}" char next
    # Note that 'quote' tracks the quote style and can be '', "'", or '"'
    local token='' in_token=0 quote=''
    local REPLY_VALUE='' REPLY_NEXT=0
    # Initialize the destination array as empty
    dest_array=()
    # Walk the options string, adding valid options to the array as discovered
    while (( ind < len )); do
        # Get the next character
        char="${opt_string:ind:1}"
        # If in a single-quoted context, then no expansion
        if [[ "$quote" == "'" ]]; then
            # If the current character is a single quote,
            # then the single quote is terminated, so reset to no quote
            if [[ "$char" == "'" ]]; then
                quote=''
            # Otherwise, add the current character to the token
            else
                token+="$char"
            fi
        # If in a double-quoted context,
        # then expand on "$" and honor the '\"', '\', and '\$' escapes
        elif [[ "$quote" == '"' ]]; then
            # If the current character is a double quote,
            # then the double quote is terminated, so reset to no quote
            if [[ "$char" == '"' ]]; then
                quote=''
            # If a "$", then try expansion using the helper function
            elif [[ "$char" == '$' ]]; then
                # Return 2 if the helper reports an error
                _read_var_ref "$opt_string" "$ind" || return 2
                # Otherwise, add the reply to the token
                # and advance the index by the length of the variable name
                token+="$REPLY_VALUE"
                ind="$REPLY_NEXT"
                continue
            # If a "\", then check the next character to decide how to handle
            elif [[ "$char" == '\' ]]; then
                # Get the next character
                next="${opt_string:ind+1:1}"
                case "$next" in
                    # If the next character makes a valid escape, then add the
                    # next character to the token and advance the index by one
                    '"'|'\'|'$')
                        token+="$next"
                        (( ind++ ))
                        ;;
                    # Otherwise, just add the current character to the token
                    *)
                        token+="$char"
                        ;;
                esac
            # Otherwise, just add the current character to the token
            else
                token+="$char"
            fi
        # Otherwise, we're in an unquoted context
        else
            # Detect changing context
            case "$char" in
                # If a single or double quote, then change to that context and
                # set the in_token flag to indicate that we're building a token
                \')
                    quote="'"
                    in_token=1
                    ;;
                \")
                    quote='"'
                    in_token=1
                    ;;
                # If a "$", then try expansion using the helper function
                \$)
                    _read_var_ref "$opt_string" "$ind" || return 2
                    token+="$REPLY_VALUE"
                    # An empty unquoted expansion produces no word (shell-like)
                    [[ -n "$REPLY_VALUE" ]] && in_token=1
                    ind="$REPLY_NEXT"
                    continue
                    ;;
                # If a "\", then add the next character to the token
                # and advance the index by one
                \\)
                    (( ind++ ))
                    (( ind < len )) && token+="${opt_string:ind:1}"
                    in_token=1
                    ;;
                # If a whitespace character,
                # then flush the current token if there is one
                ' '|$'\t'|$'\n')
                    if (( in_token )); then
                        dest_array+=("$token")
                        token=''
                        in_token=0
                    fi
                    ;;
                # Otherwise, just add the current character to the token
                *)
                    token+="$char"
                    in_token=1
                    ;;
            esac
        fi
        # If here (no continue hit), increment the index to the next character
        (( ind++ ))
    done
    # If we're still in a quoted context at the end of the string,
    # then we have an unterminated quote, so error and return 2
    if [[ -n "$quote" ]]; then
        printf \
            'Error: Unterminated %s quote in options: %s\n' \
            "$quote" \
            "$opt_string" \
            >&2
        return 2
    fi
    # Flush the final token if there is one
    (( in_token )) && dest_array+=("$token")
    return 0
}

# ----------------------------------------------------------------------
# Parse options with a while loop and case statement
# ----------------------------------------------------------------------
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        # Help and information
        -h)
            show_help
            exit 0
            ;;
        --help)
            show_detailed_help
            exit 0
            ;;
        -V|--version)
            show_version
            exit 0
            ;;
        # Configuration options
        -p|--project)
            require_value "$1" "${2:-}"
            PROJECT_NAME="$2"
            shift 2
            ;;
        -v|--venv)
            require_value "$1" "${2:-}"
            VIRTUAL_ENV="$2"
            shift 2
            ;;
        -c|--config)
            require_value "$1" "${2:-}"
            CONFIG_FILE="$2"
            shift 2
            ;;
        # Tool selection options
        -a|--all)
            RUN_ALL=1
            shift
            ;;
        -i|--include)
            require_value "$1" "${2:-}"
            INCLUDE_TOOLS="$2"
            shift 2
            ;;
        -o|--only)
            require_value "$1" "${2:-}"
            ONLY_TOOLS="$2"
            shift 2
            ;;
        -e|--exclude)
            require_value "$1" "${2:-}"
            EXCLUDE_TOOLS="$2"
            shift 2
            ;;
        -t|--test)
            PYTEST=1
            # Check if targets were provided
            if [[ -n "${2:-}" && "$2" != -* ]]; then
                parse_comma_list "$2" 'PYTEST_TARGETS' || exit 8
                shift 2
            else
                shift
            fi
            ;;
        # Ruff-specific options
        --ruff-python)
            require_value "$1" "${2:-}"
            RUFF_PYTHON="$2"
            shift 2
            ;;
        --ruff-full-output)
            RUFF_FULL_OUTPUT=1
            shift
            ;;
        --ruff-no-preview)
            RUFF_PREVIEW=0
            shift
            ;;
        --ruff-no-sort)
            RUFF_SORT=0
            shift
            ;;
        # Mypy-specific options
        --mypy-no-daemon)
            DMYPY=0
            shift
            ;;
        --mypy-restart-daemon)
            DMYPY_RESTART=1
            shift
            ;;
        --mypy-daemon-restart)
            # Alias of --mypy-restart-daemon noted in the
            # --mypy-restart-daemon help message description;
            # added because I keep forgetting which one is correct
            # and want to avoid having to fix it every time I get it wrong
            DMYPY_RESTART=1
            shift
            ;;
        # Bandit-specific options
        --bandit-full-output)
            BANDIT_FULL_OUTPUT=1
            shift
            ;;
        # Pydoclint-specific options
        --doc-style)
            require_value "$1" "${2:-}"
            PYDOCLINT_STYLE="$2"
            shift 2
            ;;
        --doc-no-skip-short)
            PYDOCLINT_SKIP_SHORT=0
            shift
            ;;
        --doc-no-auto-baseline)
            PYDOCLINT_AUTO_BASELINE=0
            shift
            ;;
        --doc-baseline)
            require_value "$1" "${2:-}"
            PYDOCLINT_BASELINE_FILE="$2"
            shift 2
            ;;
        --doc-full-output)
            PYDOCLINT_FULL_OUTPUT=1
            shift
            ;;
        # Pytest-specific options
        --test-full-output)
            PYTEST_FULL_OUTPUT=1
            shift
            ;;
        # Extra tool options options
        --ruff-format-opts)
            require_value "$1" "${2:-}" 1
            split_opts "$2" RUFF_FORMAT_OPTS || exit 8
            shift 2
            ;;
        --ruff-sort-opts)
            require_value "$1" "${2:-}" 1
            split_opts "$2" RUFF_SORT_OPTS || exit 8
            shift 2
            ;;
        --ruff-lint-opts)
            require_value "$1" "${2:-}" 1
            split_opts "$2" RUFF_LINT_OPTS || exit 8
            shift 2
            ;;
        --mypy-opts)
            require_value "$1" "${2:-}" 1
            split_opts "$2" MYPY_OPTS || exit 8
            shift 2
            ;;
        --dmypy-start-opts)
            require_value "$1" "${2:-}" 1
            split_opts "$2" DMYPY_START_OPTS || exit 8
            shift 2
            ;;
        --dmypy-check-opts)
            require_value "$1" "${2:-}" 1
            split_opts "$2" DMYPY_CHECK_OPTS || exit 8
            shift 2
            ;;
        --pyright-opts)
            require_value "$1" "${2:-}" 1
            split_opts "$2" PYRIGHT_OPTS || exit 8
            shift 2
            ;;
        --pylint-opts)
            require_value "$1" "${2:-}" 1
            split_opts "$2" PYLINT_OPTS || exit 8
            shift 2
            ;;
        --bandit-opts)
            require_value "$1" "${2:-}" 1
            split_opts "$2" BANDIT_OPTS || exit 8
            shift 2
            ;;
        --pydoclint-opts)
            require_value "$1" "${2:-}" 1
            split_opts "$2" PYDOCLINT_OPTS || exit 8
            shift 2
            ;;
        --pytest-opts)
            require_value "$1" "${2:-}" 1
            split_opts "$2" PYTEST_OPTS || exit 8
            shift 2
            ;;
        # Output control options
        -q)
            QUIET_CONSOLE=1
            shift
            ;;
        --quiet)
            QUIET_CONSOLE=1
            QUIET_FILE=1
            shift
            ;;
        -f|--file)
            # Make sure LOGFILE hasn't been set to '' to avoid
            # overriding --no-file if it has already been parsed
            if [[ -n "$LOGFILE" ]]; then
                # If it was passed as a flag, we should have already
                # expanded it to have the default value earlier
                require_value "$1" "$2"
                LOGFILE="$2"
                # Check if the provided value is "n", "no", or "none"
                # (case-insensitive) to disable file output
                if [[ \
                    "${LOGFILE,,}" == 'n' \
                    || "${LOGFILE,,}" == 'no' \
                    || "${LOGFILE,,}" == 'none' \
                ]]; then
                    LOGFILE=''
                fi
            fi
            shift 2
            ;;
        --no-file)
            # Parsing of -f/--file checks for LOGFILE to be '' first
            # so that it does not override this option
            LOGFILE=''
            shift
            ;;
        --no-console)
            CONSOLE=0
            shift
            ;;
        --no-full-output-file)
            FULL_OUTPUT_FILE=0
            shift
            ;;
        --no-preserve-prev)
            PRESERVE_PREV_LOG=0
            shift
            ;;
        # Additional options
        --no-parallel)
            PARALLEL=0
            shift
            ;;
        # End of options marker
        --)
            shift
            break
            ;;
        # Unknown options
        -* )
            printf 'Unknown option: %s\n' "$1" >&2
            show_help >&2
            exit 8
            ;;
        # Positional arguments (targets)
        * )
            break
            ;;
    esac
done

# ======================================================================
# Helpers
# ======================================================================

# Create global temporary directory for temporary files
# and cross-process communication in parallel mode
tmp_dir="$(mktemp -d)"

# Detect platform
case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*|Windows_NT)
        IS_WINDOWS=1
        ;;
    *)
        IS_WINDOWS=0
        ;;
esac

# ----------------------------------------------------------------------
# Exit, interrupt, and kill helpers
# ----------------------------------------------------------------------

# on_exit
#   Called on script exit to perform any necessary tasks.
#   It is registered to run on EXIT using trap to ensure it runs regardless of
#   how the script exits (e.g., normal completion, error, or interruption).
on_exit() {
    # Assemble the final log if needed in parallel mode,
    # making sure that the flush_logs function is defined
    [[ "$PARALLEL" -eq 1 && -n "$LOGFILE" ]] \
        && declare -F flush_logs >/dev/null \
        && flush_logs
    # Remove the temporary directory and its contents if it exists
    if [[ -n "$tmp_dir" && -d "$tmp_dir" ]]; then
        rm -rf "$tmp_dir"
    fi
}
# # Register the on_exit function to run on script exit
trap on_exit EXIT

# Define array for tool process IDs to make sure it exists,
# but it won't be used until the end and only if in parallel mode
TOOL_PIDS=()
# Track if the script has been interrupted
INTERRUPTED=0

# get_winpid MSYS_PID
#   Prints the native Windows PID for an MSYS/Cygwin PID (needed because
#   taskkill/wmic operate on Windows PIDs, not the PIDs bash reports via $!).
#   Called with the MSYS/Cygwin PID as $1
#   and prints the corresponding Windows PID.
#   Falls back to the given PID if the mapping isn't available.
get_winpid() {
    local pid="$1"
    if [[ -r "/proc/$pid/winpid" ]]; then
        cat "/proc/$pid/winpid"
    else
        printf '%s' "$pid"
    fi
}

# kill_descendants SIGNAL PARENT
#   Recursively kill child processes as a fallback
#   for when process-group kill is unavailable.
#   Called with the triggering signal (INT, TERM, etc.) as $1
#   and the parent process ID as $2.
kill_descendants() {
    local signal="$1" parent="$2" child
    # Check if pgrep is available, and return if not
    command -v pgrep >/dev/null 2>&1 || return 0
    # Recursively kill each child process
    while read -r child; do
        # Skip if the child is empty (no more children)
        [[ -n "$child" ]] || continue
        # Call this function on the child
        kill_descendants "$signal" "$child"
        # Kill the child
        kill "-$signal" "$child" 2>/dev/null || true
    done < <(pgrep -P "$parent" 2>/dev/null)
}

# win_kill_tree_wmic WINDOWS_PID
#   Kills the process with the given process ID and all its descendants.
#   Called with the Windows process ID of the process to kill.
#   Used as a fallback when taskkill is not available.
win_kill_tree_wmic() {
    local wpid="$1" child
    # Recursively kill each child process
    while read -r child; do
        # Remove CRLF and header row from wmic
        child="${child//[$'\r\n ']/}"
        # Skip "ProcessId"/blank lines
        [[ "$child" =~ ^[0-9]+$ ]] || continue
        # Skip itself (for now)
        [[ "$child" == "$wpid" ]] && continue
        # Kill the child
        win_kill_tree_wmic "$child"
    done < <( \
        wmic process where "(ParentProcessId=$wpid)" get ProcessId 2>/dev/null \
    )
    # Kill the process itself
    wmic process where "ProcessId=$wpid" delete >/dev/null 2>&1 || true
}

# kill_tree SIGNAL PID
#   Kills the process with the given process ID and all its descendants.
#   Called with the process ID of the process to kill.
#   This function is platform-aware.
kill_tree() {
    local signal="$1" pid="$2"
    # Windows branch
    if [[ "$IS_WINDOWS" -eq 1 ]]; then
        # Get the corresponding Windows process ID
        local wpid
        wpid="$(get_winpid "$pid")"
        # If taskkill is available, use it
        if command -v taskkill >/dev/null 2>&1; then
            # No native "signal" in taskkill, but //T=tree and //F=force,
            # so we use F for KILL and otherwise omit it
            if [[ "$signal" == 'KILL' ]]; then
                taskkill //PID "$wpid" //T //F >/dev/null 2>&1 || true
            else
                taskkill //PID "$wpid" //T >/dev/null 2>&1 || true
            fi
        # Otherwise, use wmic if available
        elif command -v wmic >/dev/null 2>&1; then
            win_kill_tree_wmic "$wpid"
        # Fall back to direct kill as last resolt
        else
            kill "-$signal" "$pid" 2>/dev/null || true
        fi
    # POSIX branch
    else
        # Try to kill the process group first
        if ! kill "-$signal" "-$pid" 2>/dev/null; then
            # If that fails, fall back to recursive method
            kill_descendants "$signal" "$pid"
            # Finally, kill the process itself
            kill "-$signal" "$pid" 2>/dev/null || true
        fi
    fi
}

# stop_tools SIGNAL
#   Stops any running tools.
#   Called with the triggering signal (INT, TERM, etc.) as $1.
stop_tools() {
    local signal="${1:-TERM}" pid
    # Kill each tool process
    for pid in "${TOOL_PIDS[@]}"; do
        # Skip if the process is no longer running
        kill -0 "$pid" 2>/dev/null || continue
        # Kill the tool's process and its descendants
        kill_tree "$signal" "$pid"
    done
}

# on_interrupt SIG_NAME SIG_NUM
#   Called on script interruption (e.g., Ctrl+C) to stop any running tools.
#   Called with the signal name as $1 and the signal number as $2.
#   Registered to run on INT or TERM signals.
on_interrupt() {
    local sig_name="$1" sig_num="$2"
    # Return early if already interrupted
    [[ "$INTERRUPTED" -eq 1 ]] && return 0
    # Set interruption flag
    INTERRUPTED=1
    local msg="\nInterrupted ($sig_name): Stopping running tools...\n"
    # If handle_output is defined, call it to print the interruption message
    if declare -F 'handle_output' >/dev/null; then
        handle_output "$msg" 16 'main'
    # Otherwise, fall back to direct print to stderr
    else
        printf '%b' "$msg" >&2
    fi
    # Try to stop the tools gracefully with TERM first, then use KILL if needed
    stop_tools 'TERM'
    local pid alive deadline=$(( SECONDS + 3 ))
    # Check to see if all processes have been killed until deadline
    while (( SECONDS < deadline )); do
        alive=0
        # Check if each tool is still alive
        for pid in "${TOOL_PIDS[@]}"; do
            if kill -0 "$pid" 2>/dev/null; then
                # If tool is still alive, skip to next iteration
                alive=1
                break
            fi
        done
        # If all tools have been killed, exit the loop
        (( alive )) || break
        # Otherwise, wait a short period
        sleep 0.2
    done
    # Retry stopping tools using KILL to force-kill stragglers
    stop_tools 'KILL'
    # Run the exit trap
    exit $(( 128 + sig_num ))
}

# Register the on_interrupt function to run on INT or TERM
trap 'on_interrupt INT 2' 'INT'
trap 'on_interrupt TERM 15' 'TERM'

# ----------------------------------------------------------------------
# Math helpers
# ----------------------------------------------------------------------

# min X Y
#   Returns the minimum of two numbers.
#   Called with the two numbers as $1 and $2 and prints the minimum.
min() { printf '%s' "$(( $1 < $2 ? $1 : $2 ))"; }

# The max function is not currently used,
# but it is left here if needed in the future.
# max X Y
#   Returns the maximum of two numbers.
#   Called with the two numbers as $1 and $2 and prints the maximum.
# max() { printf '%s' "$(( $1 > $2 ? $1 : $2 ))"; }

# calculate_runtime START_TIME END_TIME [DECIMAL_PLACES]
#   Calculates runtime in seconds between two timestamps.
#   Called with the start time as $1, the end time as $2,
#   and optionally the number of decimal places to use as $3.
#   Prints the result, using three decimal places by default.
calculate_runtime() {
    local start_time="$1" end_time="$2" decimal_places="${3:-3}"
    # Default to 3 decimal places if not provided
    [[ -z "$decimal_places" ]] && decimal_places=3
    # Use awk to calculate the difference
    # and format it to the specified decimal places
    local runtime
    runtime="$(
        awk -v start="$start_time" -v end="$end_time" -v dp="$decimal_places" \
        'BEGIN { printf "%.*f", dp, end - start }'
    )"
    printf '%s' "$runtime"
}

# ----------------------------------------------------------------------
# Logging and output helpers
# ----------------------------------------------------------------------

# Handle log file setup
if [[ -z "$LOGFILE" ]]; then
    # Set FULL_OUTPUT_FILE to 0 if file output is disabled
    # so we know that the log file exists if it is 1
    FULL_OUTPUT_FILE=0
else
    # If LOGFILE is set, create any necessary parent directories
    mkdir -p "$(dirname "$LOGFILE")"
    # If LOGFILE exists, create a temporary backup with the last run's results
    # if specified; otherwise, if it exists, it will just be overwritten
    if [[ $PRESERVE_PREV_LOG -eq 1 && -f "$LOGFILE" ]]; then
        LAST_LOG_BACKUP="${LOGFILE}.prev"
        cp "$LOGFILE" "$LAST_LOG_BACKUP"
    # If it doesn't exist, create an empty file to ensure it exists for later
    else
        touch "$LOGFILE"
    fi
    # Wipe LOGFILE so we start fresh regardless of prior state
    : > "$LOGFILE"
fi

# strip_empty_lines TEXT
#   Strips empty lines from the given text and prints the result.
#   Called with the text to process as $1.
#   This function automatically handles Windows-style line endings ('\r\n').
strip_empty_lines() { printf '%s' "$1" | awk '/^\r?$/ {next} {print}'; }

BACKSLASH_PAIR_PLACEHOLDER='__BACKSLASH_PAIR__'

# escape_single_backslashes STRING [EXCLUDE_ARRAY]
#   Escapes single backslashes in a string by replacing each single backslash
#   with a double backslash and prints the resulting string.
#   Called with the string to process as $1 and optionally
#   an array of strings to exclude from escaping as $2.
#   This is useful for Windows paths to ensure they are correctly interpreted
#   when passed to tools that may treat backslashes as escape characters.
#   The EXCLUDE_ARRAY is useful for keeping sequences like "\n" intact.
escape_single_backslashes() {
    local str="$1"
    local -a _default_exclude=()
    local -n _exclude_array="${2:-_default_exclude}"
    # Step 1: Replace double backslashes with a placeholder
    local result
    result="${str//\\\\/$BACKSLASH_PAIR_PLACEHOLDER}"
    # Step 2: Replace each array element in EXCLUDE_ARRAY with a placeholder
    local exclude_placeholders=()
    local exclude
    for exclude in "${_exclude_array[@]}"; do
        # Create a unique placeholder for each excluded string
        # by using the excluded string itself in the placeholder name
        local placeholder
        placeholder="$(
            printf \
                '__BACKSLASH_%s__' "$(printf '%s' "${exclude:1:"${#exclude}"}")"
        )"
        # Replace the excluded string with the placeholder in the result
        result="${result//"$exclude"/$placeholder}"
        exclude_placeholders+=("$placeholder")
    done
    # Step 3: Replace remaining single backslashes with double backslashes
    result="${result//\\/\\\\}"
    # Step 4: Replace the double backslash placeholder with double backslashes
    result="${result//$BACKSLASH_PAIR_PLACEHOLDER/\\\\}"
    # Step 5: Replace the excluded string placeholders with the original values
    local i
    for i in "${!_exclude_array[@]}"; do
        result="${result//"${exclude_placeholders[i]}"/"${_exclude_array[i]}"}"
    done
    # Print the result for capture
    printf '%s' "$result"
}

# Define string to separate ruff-lint output
# with --statistics from the full output
RUFF_LINT_OUTPUT_SEP='---RUFF-LINT-OUTPUT-SEPARATION-MARKER---'

# extract_ruff_lint_stats_lines RUFF_OUTPUT
#   Extracts and prints only the statistics lines from ruff output.
#   Called with the full ruff output as $1, where the full ruff output
#   is either a single run with --statistics when full output is disabled
#   or the combined output of a run without --statistics
#   followed by a run with --statistics when full output is enabled,
#   where it is assumed that one or more empty lines separate the two.
extract_ruff_lint_stats_lines() { \
    printf '%s' "$1" | awk "/$RUFF_LINT_OUTPUT_SEP/{exit} 1"; \
}

# extract_bandit_issue_lines BANDIT_OUTPUT
#   Extracts and prints only the issue lines from bandit output.
#   Called with the full bandit output as $1.
#   This function assumes that the output has already had any empty lines
#   stripped, that the issue lines start with the line saying "Test results:",
#   that the next section starts with an empty line followed by a line
#   saying "Code scanned:", and that the output ends with the
#   "Files skipped (X):" section, where files that were supposed to be scanned
#   but were skipped are listed along with the reasons why they were skipped.
#   This section is also extracted and appended to the issue lines if non-empty.
extract_bandit_issue_lines() {
    # Extract the lines between
    # "Test results:" (inclusive) and "Code scanned:" (exclusive)
    local BANDIT_RESULT
    BANDIT_RESULT="$(
        printf '%s' "$1" \
        | awk -v start='Test results:' -v end='Code scanned:' '
            !found && $0 == start { found=1 }
            found && $0 == end    { exit }
            found {
                buf[++n] = $0
                if (n > 1) print buf[n-1]
            }
        '
    )"
    # Remove the "Test results:" header line
    BANDIT_RESULT="$(printf '%s' "$BANDIT_RESULT" | tail -n +2)"
    local bandit_last_line
    bandit_last_line="${BANDIT_RESULT##*$'\n'}"
    # Add the syntax error report for skipped files if present
    if [[ "$bandit_last_line" != 'Files skipped (0):' ]] \
            && [[ -n "$(printf '%s' "$1" | grep 'syntax error')" ]]; then
        # Get the lines from Bandit's output reporting skipped files
        # (last section, goes from "Files skipped (X):" header to end)
        local BANDIT_SKIPPED_LINES
        BANDIT_SKIPPED_LINES="$(
            printf '%s' "$1" | awk '/Files skipped/{found=1} found'
        )"
        # Only add a newline if there were other issues found
        [[ -n "$BANDIT_RESULT" ]] && BANDIT_RESULT+='\n'
        # Append the syntax error report for skipped files to the result
        BANDIT_RESULT+="$BANDIT_SKIPPED_LINES"
    fi
    # If no issues were found, the extracted portion will be empty,
    # so set a success message mimicking Bandit's "No issues identified." output
    [[ -z "$BANDIT_RESULT" ]] \
        && BANDIT_RESULT='No issues identified.'
    # Print result for handle_output to capture
    printf '%s' "$BANDIT_RESULT"
}

# extract_pydoclint_issue_lines PYDOCLINT_OUTPUT
#   Extracts and prints only the issue lines from pydoclint output.
#   Called with the full pydoclint output as $1.
#   This function assumes that the issue lines start one line above
#   the first line that begins with whitespace.
#   If no such lines are found, then it is assumed that there were no issues
#   and a message indicating that is printed instead.
extract_pydoclint_issue_lines() {
    local PYDOCLINT_RESULT
    PYDOCLINT_RESULT="$(
        printf '%s' "$1" | awk '
            /^[[:space:]]/ && !found { print prev; found=1 }
            found  { print; next }
                { prev=$0 }
        '
    )"
    PYDOCLINT_RESULT="$(strip_empty_lines "$PYDOCLINT_RESULT")"
    # If no issues were found, the extracted portion will be empty,
    # so set a success message mimicking pydoclint's "No violations" output
    if [[ -z "$PYDOCLINT_RESULT" ]]; then
        PYDOCLINT_RESULT="No violations"
    fi
    # Print result for handle_output to capture
    printf '%s' "$PYDOCLINT_RESULT"
}

# extract_pytest_summary_lines()
#   Extracts and prints only the summary lines from pytest output.
#   Called with the full pytest output as $1.
#   This function assumes that the summary output starts with a line that
#   begins with "===...", has "short test summary info", and ends with "...==="
#   and runs until the end of the output, including the final summary line.
#   If no such lines are found, then it is assumed that all tests passed
#   and only the info from the final summary line is printed instead.
extract_pytest_summary_lines() {
    local PYTEST_RESULT
    PYTEST_RESULT="$(
        printf '%s' "$1" | awk '
            /^=+ short test summary info =+/ { found=1 }
            found { print; next }
        '
    )"
    # If no summary lines were found, the extracted portion will be empty,
    # so just grab info from the final summary line
    if [[ -z "$PYTEST_RESULT" ]]; then
        PYTEST_RESULT="$(
            printf '%s' "$1" | awk '
                /=+.*=+/ { last=$0 }
                END { print last }
            '
        )"
    fi
    # Print result for handle_output to capture
    printf '%s' "$PYTEST_RESULT"
}

# Track if any output has been printed yet for quiet mode formatting purposes
QUIET_FILE_OUTPUT_OCCURRED=0
QUIET_CONSOLE_OUTPUT_OCCURRED=0

# handle_output MESSAGE SEVERITY [STAGE]
#   Directs output to the correct destination(s)
#   based on the message severity and output configuration.
#   Called with the message as $1, the message severity as $2,
#   and optionally the stage name for which the message is intended as $3
#   to allow specific handling of output for each stage if needed,
#   where the message severity is an integer representing
#   the severity or event code associated with the message
#   (e.g., 0 for informational messages, 1 for issues found, 2 for tool failure,
#   8 for bad options given, 16 for script-related errors).
#   Messages should already be pre-formatted with newlines
#   and other escape sequences as needed, except for messages
#   requiring tool-specific output extraction/handling.
#   If file output is enabled, the message is appended to the
#   log file specified by LOGFILE. If console output is enabled,
#   the message is printed to stdout if the severity is 0
#   and to stderr if the severity is greater than 0.
#   Version and help messages always go straight to console
#   and do not flow through this function.
handle_output() {
    local message="$1" severity="$2" stage="${3:-}"
    # Perform tool-specific handling
    # (console_msg is only updated if the console version of a message needs to
    # be different from the file version; otherwise, message is used for both)
    local console_msg=''
    if [[ -n "$stage" ]]; then
        case "$stage" in
            ruff-lint-full)
                if [[ "$RUFF_FULL_OUTPUT" -eq 0 ]]; then
                    console_msg="$(extract_ruff_lint_stats_lines "$message")"
                    # If the extracted message is different from the original
                    # and full output is needed for the file,
                    # then we need to replace the separating string marker
                    # between the main output and the statistics output
                    # with a newline so that the formatting is correct
                    if [[ "$console_msg" != "$message" ]] \
                            && [[ "$FULL_OUTPUT_FILE" -eq 1 ]]; then
                        message="$(
                            printf '%s' "${1/$RUFF_LINT_OUTPUT_SEP/\\n}"
                        )"
                    # Otherwise, the extracted message is the same
                    # as the original or the file is also supposed
                    # to get the extracted version (all full output disabled),
                    # so the extracted version is correct in both cases
                    else
                        message="$console_msg"
                    fi
                fi
                # Add newlines to each message
                message+='\n'
                console_msg+='\n'
                # Set stage name to just "ruff-lint" for proper handling below
                stage='ruff-lint'
                ;;
            bandit-full)
                if [[ "$BANDIT_FULL_OUTPUT" -eq 0 ]]; then
                    console_msg="$(extract_bandit_issue_lines "$message")"
                    # Also use the extracted message for the file
                    # if full output is disabled for the file
                    [[ "$FULL_OUTPUT_FILE" -eq 0 ]] && message="$console_msg"
                fi
                # Add newlines to each message
                message+='\n'
                console_msg+='\n'
                # Set stage name to just "bandit" for proper handling below
                stage='bandit'
                ;;
            pydoclint-full)
                if [[ "$PYDOCLINT_FULL_OUTPUT" -eq 0 ]]; then
                    console_msg="$(extract_pydoclint_issue_lines "$message")"
                    # Also use the extracted message for the file
                    # if full output is disabled for the file
                    [[ "$FULL_OUTPUT_FILE" -eq 0 ]] && message="$console_msg"
                fi
                # Add newlines to each message
                message+='\n'
                console_msg+='\n'
                # Set stage name to just "pydoclint" for proper handling below
                stage='pydoclint'
                ;;
            pytest-full)
                if [[ "$PYTEST_FULL_OUTPUT" -eq 0 ]]; then
                    console_msg="$(extract_pytest_summary_lines "$message")"
                    # Also use the extracted message for the file
                    # if full output is disabled for the file
                    [[ "$FULL_OUTPUT_FILE" -eq 0 ]] && message="$console_msg"
                fi
                # Add newlines to each message
                message+='\n'
                console_msg+='\n'
                # Set stage name to just "pytest" for proper handling below
                stage='pytest'
                ;;
            *)
                # For other tools/stages, no special handling is needed for now,
                # but this case statement can be expanded in the future
                # to add tool-/stage-specific output processing as needed.
                ;;
        esac
    fi
    # Output to a log file if LOGFILE is set and the severity is
    # non-zero or quiet mode is not enabled for file output
    if [[ -n "$LOGFILE" ]] \
        && [[ "$severity" -ne 0 || "$QUIET_FILE" -eq 0 ]]; then
        local file_msg="$message"
        # Handle quiet mode output tracking/formatting
        if [[ "$QUIET_FILE" -eq 1 ]]; then
            # Use a signal file to indicate that
            # quiet output has occurred in parallel mode
            if [[ "$PARALLEL" -eq 1 ]]; then
                # Create the signal file if it doesn't exist yet
                if [[ ! -f "${tmp_dir}/quiet_file_output_occurred" ]]; then
                    touch "${tmp_dir}/quiet_file_output_occurred"
                # Otherwise, add a leading newline to the message
                else
                    file_msg="\n$file_msg"
                fi
            # Use global variables to track quiet output in non-parallel mode
            else
                # Flip tracker if file output has occurred in quiet mode
                if [[ "$QUIET_FILE_OUTPUT_OCCURRED" -eq 0 ]]; then
                    QUIET_FILE_OUTPUT_OCCURRED=1
                # Otherwise, add a leading newline to the message
                else
                    file_msg="\n$file_msg"
                fi
            fi
        fi
        # Use individual log files per stage in parallel mode
        if [[ "$PARALLEL" -eq 1 ]]; then
            # Use a temporary file for the stage if provided
            if [[ -n "$stage" ]] && [[ ! "$stage" == 'main' ]]; then
                local stage_logfile="${tmp_dir}/${stage}.log"
                printf '%b' "$file_msg" >> "$stage_logfile"
            # Otherwise, use the main log file
            else
                printf '%b' "$file_msg" >> "$LOGFILE"
            fi
        # Use direct appends in non-parallel mode
        else
            # Append message to log file using printf to handle escape sequences
            printf '%b' "$file_msg" >> "$LOGFILE"
        fi
    fi
    # Done with file, so we can set message to console_msg
    # if a different version is needed for console output purposes
    [[ -n "$console_msg" ]] && message="$console_msg"
    # Output to console if console output is enabled and the severity is
    # non-zero or quiet mode is not enabled for console output
    if [[ "$CONSOLE" -eq 1 ]] \
            && [[ "$severity" -ne 0 || "$QUIET_CONSOLE" -eq 0 ]]; then
        # Handle quiet mode output tracking/formatting
        if [[ "$QUIET_CONSOLE" -eq 1 ]]; then
            # Use a signal file to indicate that
            # quiet output has occurred in parallel mode
            if [[ "$PARALLEL" -eq 1 ]]; then
                # Create the signal file if it doesn't exist yet
                if [[ ! -f "${tmp_dir}/quiet_console_output_occurred" ]]; then
                    touch "${tmp_dir}/quiet_console_output_occurred"
                # Otherwise, add a leading newline to the message
                else
                    message="\n$message"
                fi
            # Use global variables to track quiet output in non-parallel mode
            else
                # Flip tracker if console output has occurred in quiet mode
                if [[ "$QUIET_CONSOLE_OUTPUT_OCCURRED" -eq 0 ]]; then
                    QUIET_CONSOLE_OUTPUT_OCCURRED=1
                # Otherwise, add a leading newline to the message
                else
                    message="\n$message"
                fi
            fi
        fi
        # Use stdout if severity is below 8; otherwise, use stderr
        # (severity 8 and above indicates an error from this script itself,
        # such as bad options given or an unexpected state reached,
        # so it should go to stderr, whereas informational output
        # and individual tool issues/errors can go to stdout)
        if [[ "$severity" -lt 8 ]]; then
            printf '%b' "$message"
        else
            printf '%b' "$message" >&2
        fi
    fi
}

# report_runtime START_TIME STAGE_NAME
#   Reports the runtime of a stage to the console and/or log file.
#   Called with the start time as $1 and the stage name as $2.
#   The runtime is calculated as the difference between the current time
#   and the start time, and is printed in seconds with three decimal places.
report_runtime() {
    local start_time="$1" stage_name="$2"
    local runtime
    runtime="$(calculate_runtime "$start_time" "$(now)" 3)"
    local msg="Ran in $runtime seconds\n"
    handle_output "$msg" 0 "$stage_name"
}

# ----------------------------------------------------------------------
# Tool resolution and execution helpers
# ----------------------------------------------------------------------

# expand_ruff TOOLS
#   Expands "ruff" into "ruff-format" and "ruff-lint" in a comma-separated list.
#   Called with the comma-separated list as $1 and prints the expanded list.
#   If "ruff" is not present, the original list is printed unchanged.
expand_ruff() {
    result=''
    parse_comma_list "$1" 'TOOL_ARRAY'
    for tool in "${TOOL_ARRAY[@]}"; do
        if [[ "$tool" == 'ruff' ]]; then
            result+="${result:+,}ruff-format,ruff-lint"
        else
            result+="${result:+,}$tool"
        fi
    done
    printf '%s' "$result"
}

# check_cmd PATH
#   Verifies a tool exists and is executable at the given path.
#   Called with the path to the tool to check as $1.
#   Prints a warning if the tool was explicitly asked for with -o/--only
#   and is not found or not executable at the given path, unless in quiet mode.
#   Returns 1 if the tool does not exist and 0 if it does.
check_cmd() {
    local cmd_path="$1"
    if [ ! -x "$cmd_path" ]; then
        # Print warning if -o/--only used and not in quiet mode
        if [[ -n "$ONLY_TOOLS" ]]; then
            local msg
            msg="Warning: $(basename "$cmd_path") "
            msg+='was explicitly included with -o/--only '
            msg+="but was not found or not executable at $cmd_path\n"
            handle_output "$msg" 0 'main'
        fi
        return 1
    fi
    return 0
}

# Track if any tool reports issues or errors for exit code purposes.
# This script uses the following bit-encoded exit code convention:
# -  0: No issues found and no errors occurred
# -  1: Issues found but no errors occurred
# -  2: Tool execution failed due to bad options or other user errors
# -  4: Failed test while running pytest
# -  8: Bad option(s) given
# - 16: Error from this script (e.g., bad state reached)
# The final exit code is the sum of all event codes occurring during execution.
EXIT_CODE=0
EXIT_1_OCCURRED=0
EXIT_2_OCCURRED=0
EXIT_4_OCCURRED=0
EXIT_8_OCCURRED=0
EXIT_16_OCCURRED=0
# Lists of tools with issues or errors for reporting purposes
TOOLS_WITH_ISSUES=''
TOOLS_WITH_ERRORS=''

# update_exit_code EVENT_CODE [TOOL]
#   Updates the global EXIT_CODE to reflect the occurrence
#   of an event with the given code.
#   Called with the event code as $1 (e.g., 1 for issues found,
#   2 for tool execution failure, 8 for bad options, etc.)
#   and optionally the tool name as $2.
#   Updates EXIT_CODE to be the sum of itself and the given event code
#   if that event code has not yet occurred in the script;
#   otherwise, the exit code is unchanged.
update_exit_code() {
    local event_code="$1" tool="${2:-}"
    # In parallel mode, use signal files to track if event codes have occurred
    if [[ "$PARALLEL" -eq 1 ]]; then
        local filename="exit_${event_code}_occurred"
        [[ -f "$tmp_dir/$filename" ]] || touch "$tmp_dir/$filename"
    # In non-parallel mode, use global variables to track event code occurrence
    else
        # For each possible event code, check if the passed code matches and
        # increment the global EXIT_CODE if that code has not already occurred
        case "$event_code" in
            0)
                # No issues or errors occurred; do nothing
                ;;
            1)
                if [[ "$EXIT_1_OCCURRED" -eq 0 ]]; then
                    EXIT_CODE=$(( EXIT_CODE + 1 ))
                    EXIT_1_OCCURRED=1
                fi
                ;;
            2)
                if [[ "$EXIT_2_OCCURRED" -eq 0 ]]; then
                    EXIT_CODE=$(( EXIT_CODE + 2 ))
                    EXIT_2_OCCURRED=1
                fi
                ;;
            4)
                if [[ "$EXIT_4_OCCURRED" -eq 0 ]]; then
                    EXIT_CODE=$(( EXIT_CODE + 4 ))
                    EXIT_4_OCCURRED=1
                fi
                ;;
            8)
                if [[ "$EXIT_8_OCCURRED" -eq 0 ]]; then
                    EXIT_CODE=$(( EXIT_CODE + 8 ))
                    EXIT_8_OCCURRED=1
                fi
                ;;
            16)
                if [[ "$EXIT_16_OCCURRED" -eq 0 ]]; then
                    EXIT_CODE=$(( EXIT_CODE + 16 ))
                    EXIT_16_OCCURRED=1
                fi
                ;;
            *)
                local msg="Error: Invalid event code $event_code "
                msg+='passed to update_exit_code\n'
                handle_output "$msg" 16 'main'
                exit 16
                ;;
        esac
    fi
    # Update problem tool trackers if a tool name was provided
    if [[ -n "$tool" ]]; then
        # Use signal files if in parallel mode
        if [[ "$PARALLEL" -eq 1 ]]; then
            # Create a signal file for the tool with issues if event code is 1
            if [[ "$event_code" -eq 1 ]]; then
                touch "$tmp_dir/${tool}.iss"
            # Create a signal file for the tool with errors if event code is 2
            elif [[ "$event_code" -eq 2 ]]; then
                touch "$tmp_dir/${tool}.err"
            fi
        # Otherwise, just update the lists of tools with issues or errors
        else
            # Add to the issues list if event code is 1 (issues found)
            # and tool not already in list
            if [[ \
                "$event_code" -eq 1 && "$TOOLS_WITH_ISSUES" != *"$tool"* \
            ]]; then
                TOOLS_WITH_ISSUES+="${TOOLS_WITH_ISSUES:+, }$tool"
            # Add to the errors list if event code is 2 (tool execution failure)
            # and tool not already in list
            elif [[ \
                "$event_code" -eq 2 && "$TOOLS_WITH_ERRORS" != *"$tool"* \
            ]]; then
                TOOLS_WITH_ERRORS+="${TOOLS_WITH_ERRORS:+, }$tool"
            fi
        fi
    fi

}

# ----------------------------------------------------------------------
# Post-run helpers
# ----------------------------------------------------------------------

# flush_logs [STAGE]
#   Flushes logs from the temporary directory to the main log file
#   when file logging is enabled and in parallel mode.
#   Called with an optional stage name as $1 to flush only that stage's log.
flush_logs() {
    local stage="${1:-}"
    # Return early if not using file logging or not in parallel mode
    [[ -z "$LOGFILE" || "$PARALLEL" -eq 0 ]] && return 0
    # Make sure the temporary directory exists before trying to flush any logs
    if [[ ! -d "$tmp_dir" ]]; then
        printf 'Error: Temporary log directory not found: %s\n' "$tmp_dir" >&2
        return 16
    fi
    # Handle the case where a specific stage's log is requested
    if [[ -n "$stage" ]]; then
        local stage_logfile="$tmp_dir/$stage.log"
        # If the stage log file exists, append its contents to the main log
        if [[ -f "$stage_logfile" ]]; then
            cat "$stage_logfile" >> "$LOGFILE"
            # Remove the stage log file after appending to avoid duplication
            rm -f "$stage_logfile"
        # Otherwise, emit a warning if not in quiet mode
        # (if calling this function, we expect there to be messages to flush,
        # so if not, treat it as a tool run failure and log a warning;
        # in quiet mode, no messages logged is a good thing)
        elif [[ "$QUIET_FILE" -eq 0 ]]; then
            handle_output \
                "Warning: No log file found for stage: $stage\n" 0 "$stage"
            flush_logs 'main'
        fi
        # Return early since we only wanted to flush logs for this stage
        return 0
    fi
    # Define order to flush the files in
    local ASSEMBLY_ORDER=(
        'pre-run.log'
        'ruff-format.log'
        'ruff-lint.log'
        'mypy.log'
        'pyright.log'
        'pylint.log'
        'bandit.log'
        'pydoclint.log'
        'post-run.log'
    )
    # For each file in the assembly order, if it exists,
    # append its contents to the final log file
    local filename
    for filename in "${ASSEMBLY_ORDER[@]}"; do
        local filepath="$tmp_dir/$filename"
        [[ -f "$filepath" ]] && cat "$filepath" >> "$LOGFILE"
    done
}

# get_exit_code
#   Prints the final exit code for the script based on event code occurrence.
#   In non-parallel mode, it simply prints the value of EXIT_CODE.
#   In parallel mode, it checks for the existence of signal files created by
#   update_exit_code to determine which event codes occurred,
#   sums the corresponding codes, and prints the final exit code.
get_exit_code() {
    if [[ "$PARALLEL" -eq 1 ]]; then
        local exit_code=0
        for code in 1 2 4 8 16; do
            if [[ -f "$tmp_dir/exit_${code}_occurred" ]]; then
                exit_code=$(( exit_code + code ))
            fi
        done
        printf '%s' "$exit_code"
    else
        printf '%s' "$EXIT_CODE"
    fi
}

# ======================================================================
# Determine active tool set
# ======================================================================

# Expand plain "ruff" into "ruff-format" and "ruff-lint" for each tool list
INCLUDE_TOOLS="$( expand_ruff "$INCLUDE_TOOLS" )"
ONLY_TOOLS="$( expand_ruff "$ONLY_TOOLS" )"
EXCLUDE_TOOLS="$( expand_ruff "$EXCLUDE_TOOLS" )"

# Resolution priority (lower = weaker, higher = stronger):
#   default < -i/--include < -a/--all < -o/--only < -e/--exclude
ALL_TOOLS=(ruff-format ruff-lint mypy pyright pylint bandit pydoclint)
DEFAULT_TOOLS=(ruff-format ruff-lint mypy pyright)
declare -A RUN_TOOL

# Stage 1: seed from default set or all tools (when -a/--all was passed).
#          -i/--include adds to the default set but is overridden by -a.
if [[ "$RUN_ALL" -eq 1 ]]; then
    for c in "${ALL_TOOLS[@]}"; do RUN_TOOL[$c]=1; done
else
    for c in "${ALL_TOOLS[@]}"; do RUN_TOOL[$c]=0; done
    for c in "${DEFAULT_TOOLS[@]}"; do RUN_TOOL[$c]=1; done
    # -i: union with the default set
    if [[ -n "$INCLUDE_TOOLS" ]]; then
        parse_comma_list "$INCLUDE_TOOLS" 'inc'
        for c in "${inc[@]}"; do
            # Handle pytest separately
            if [[ "$c" == 'pytest' ]]; then
                PYTEST=1
            # Otherwise, mark the tool to be run
            else
                RUN_TOOL[$c]=1
            fi
        done
    fi
fi

# Stage 2: -o/--only replaces whatever was set in stage 1.
if [[ -n "$ONLY_TOOLS" ]]; then
    for c in "${ALL_TOOLS[@]}"; do RUN_TOOL[$c]=0; done
    parse_comma_list "$ONLY_TOOLS" 'only'
    for c in "${only[@]}"; do RUN_TOOL[$c]=1; done
fi

# Stage 3: -e/--exclude removes tools regardless of all other flags.
if [[ -n "$EXCLUDE_TOOLS" ]]; then
    parse_comma_list "$EXCLUDE_TOOLS" 'exc'
    for c in "${exc[@]}"; do RUN_TOOL[$c]=0; done
fi

# Stage 4: collect the final ordered list for display and iteration.
tools_to_run=()
n_non_format_tools=0
for c in "${ALL_TOOLS[@]}"; do
    if [[ "${RUN_TOOL[$c]}" -eq 1 ]]; then
        tools_to_run+=("$c")
        [[ "$c" != 'ruff-format' ]] && ((n_non_format_tools++))
    fi
done
# Add pytest if it is running
if [[ "$PYTEST" -eq 1 ]]; then
    tools_to_run+=('pytest')
    ((n_non_format_tools++))
fi

# ======================================================================
# Resolve targets
# ======================================================================

# Use positional arguments as targets when provided; otherwise fall back to
# the conventional project layout. Non-existent defaults are silently skipped.
if [[ "$#" -gt 0 ]]; then
    targets=("$@")
else
    # Resolve the main source directory
    PARTIAL_PROJECT_NAME_1="${PROJECT_NAME%%-*}"
    # Handle project names with and without a dash ('-') in them
    if [[ "$PROJECT_NAME" == *'-'* ]]; then
        # Extract the portion after the first dash and then the portion
        # before the next dash (if any) to get the second partial name
        PARTIAL_PROJECT_NAME_2_PLUS="${PROJECT_NAME#*-}"
        _tmp="$PARTIAL_PROJECT_NAME_2_PLUS"
        PARTIAL_PROJECT_NAME_2="${_tmp%%-*}"
    else
        # No '-' in the name, so match cut's empty 2nd/2nd-plus fields
        PARTIAL_PROJECT_NAME_2_PLUS=''
        PARTIAL_PROJECT_NAME_2=''
    fi
    # Build candidate source directory list, stripping empty partial names
    # so they can't expand to "/" (root) or produce duplicates
    CANDIDATE_SOURCE_DIRS=("src/$PROJECT_NAME/" "$PROJECT_NAME/")
    if [[ -n "$PARTIAL_PROJECT_NAME_2_PLUS" ]]; then
        CANDIDATE_SOURCE_DIRS+=(
            "src/$PARTIAL_PROJECT_NAME_2_PLUS/"
            "$PARTIAL_PROJECT_NAME_2_PLUS/"
        )
    fi
    if [[ -n "$PARTIAL_PROJECT_NAME_2" ]]; then
        CANDIDATE_SOURCE_DIRS+=(
            "src/$PARTIAL_PROJECT_NAME_2/"
            "$PARTIAL_PROJECT_NAME_2/"
        )
    fi
    if [[ -n "$PARTIAL_PROJECT_NAME_1" ]]; then
        CANDIDATE_SOURCE_DIRS+=(
            "src/$PARTIAL_PROJECT_NAME_1/"
            "$PARTIAL_PROJECT_NAME_1/"
        )
    fi
    CANDIDATE_SOURCE_DIRS+=('src/')
    # Search for the first existing source directory in the candidate list
    SOURCE_DIR=''
    for candidate in "${CANDIDATE_SOURCE_DIRS[@]}"; do
        if [[ -e "$candidate" ]]; then
            SOURCE_DIR="$candidate"
            break
        fi
    done
    # Resolve the test directory
    CANDIDATE_TEST_DIRS=(
        'tests/'
        'test/'
        'src/tests/'
        'src/test/'
    )
    TEST_DIR=''
    for candidate in "${CANDIDATE_TEST_DIRS[@]}"; do
        if [[ -e "$candidate" ]]; then
            TEST_DIR="$candidate"
            break
        fi
    done
    # Resolve the docs demo directory
    CANDIDATE_DOCS_DEMO_DIRS=(
        'docsrc/source/demos/'
        'docs/source/demos/'
        'doc/demos/'
        'docs/demos/'
    )
    DOCS_DEMO_DIR=''
    for candidate in "${CANDIDATE_DOCS_DEMO_DIRS[@]}"; do
        if [[ -e "$candidate" ]]; then
            DOCS_DEMO_DIR="$candidate"
            break
        fi
    done
    # Determine the final list of default targets
    default_targets=()
    [[ -n "$SOURCE_DIR" ]] && default_targets+=("$SOURCE_DIR")
    [[ -n "$TEST_DIR" ]] && default_targets+=("$TEST_DIR")
    [[ -n "$DOCS_DEMO_DIR" ]] && default_targets+=("$DOCS_DEMO_DIR")
    # Fall back to using project root if no other default targets found
    [[ -z "$SOURCE_DIR" ]] \
        && [[ -z "$TEST_DIR" ]] \
        && [[ -z "$DOCS_DEMO_DIR" ]] \
        && default_targets+=(".")
    # Resolve the final list of targets, ensuring they exist
    targets=()
    for target in "${default_targets[@]}"; do
        [[ -e "$target" ]] && targets+=("$target")
    done
    if [[ "${#targets[@]}" -eq 0 ]]; then
        handle_output \
            'Error: No default targets found; nothing to do.\n' 16 'main'
        exit 16
    fi
fi

# ======================================================================
# Virtual environment handling
# ======================================================================

# ----------------------------------------------------------------------
# Resolve virtual environment path
# ----------------------------------------------------------------------

# If --venv was not provided, select a platform-appropriate default:
#   Windows (Git Bash / MSYS2 / Cygwin): ~/venvs/<project>/.venv
#   Unix / macOS:                        .venv (project root)
if [[ -z "$VIRTUAL_ENV" ]]; then
    if [[ "$IS_WINDOWS" -eq 1 ]]; then
        VIRTUAL_ENV="$HOME/venvs/$PROJECT_NAME/.venv"
    else
        VIRTUAL_ENV='.venv'
    fi
fi

# ----------------------------------------------------------------------
# Detect venv executable subdirectory
# ----------------------------------------------------------------------

# Virtual environments use 'bin' on Unix/macOS and 'Scripts' on Windows.
if [ -f "$VIRTUAL_ENV/bin/activate" ]; then
    SECOND_DIR='bin'
elif [ -f "$VIRTUAL_ENV/Scripts/activate" ]; then
    SECOND_DIR='Scripts'
else
    handle_output \
        "Error: No virtualenv activation script found under $VIRTUAL_ENV\n" \
        16 \
        'main'
    exit 16
fi

# Default ruff Python version to the minor version of the virtual
# environment's Python, if not explicitly set by the user
if [[ -z "$RUFF_PYTHON" ]]; then
    if check_cmd "$VIRTUAL_ENV/$SECOND_DIR/python"; then
        PYTHON_VERSION_OUTPUT="$(
            "$VIRTUAL_ENV/$SECOND_DIR/python" --version 2>&1
        )"
        PYTHON_VERSION_EXIT="$?"
        if [[ "$PYTHON_VERSION_EXIT" -eq 0 ]]; then
            # Extract the minor version number (e.g., "3.12.4" -> "12")
            if [[ \
                "$PYTHON_VERSION_OUTPUT" \
                =~ Python[[:space:]]+([0-9]+)\.([0-9]+)\.[0-9]+ \
            ]]; then
                PYTHON_MINOR_VERSION="${BASH_REMATCH[2]}"
                RUFF_PYTHON="$PYTHON_MINOR_VERSION"
            else
                if [[ "${RUN_TOOL[ruff-lint]}" -eq 1 ]]; then
                    msg='Warning: Unable to parse Python version from output: '
                    msg+="$PYTHON_VERSION_OUTPUT\nDefaulting to Python version "
                    msg+="$DEFAULT_RUFF_PYTHON for ruff linting\n"
                    handle_output "$msg" 0 'main'
                fi
                RUFF_PYTHON="$DEFAULT_RUFF_PYTHON"
            fi
        else
            if [[ "${RUN_TOOL[ruff-lint]}" -eq 1 ]]; then
                msg='Warning: Failed to run python to get version '
                msg+="(exit code $PYTHON_VERSION_EXIT): "
                msg+="$PYTHON_VERSION_OUTPUT\nDefaulting to Python version"
                msg+="$DEFAULT_RUFF_PYTHON for ruff linting\n"
                handle_output "$msg" 0 'main'
            fi
            RUFF_PYTHON="$DEFAULT_RUFF_PYTHON"
        fi
    else
        if [[ "${RUN_TOOL[ruff-lint]}" -eq 1 ]]; then
            msg='Warning: No python executable found in virtualenv at '
            msg+="$VIRTUAL_ENV/$SECOND_DIR/python\n"
            msg+='Unable to detect Python version; defaulting to Python '
            msg+="version $DEFAULT_RUFF_PYTHON for ruff linting\n"
            handle_output "$msg" 0 'main'
        fi
        RUFF_PYTHON="$DEFAULT_RUFF_PYTHON"
    fi
fi

# ======================================================================
# Tool functions
# ======================================================================

# ----------------------------------------------------------------------
# Ruff formatting (including opt-out import sorting)
# ----------------------------------------------------------------------
# _ruff_format
#   Runs ruff formatting on the specified targets and captures the output.
_ruff_format() {
    RUFF_FORMAT_START_TIME="$(now)"
    # Make sure ruff is available
    if ! check_cmd "$VIRTUAL_ENV/$SECOND_DIR/ruff"; then return 1; fi
    # Display header if not in quiet mode
    handle_output '\nRunning ruff formatting...\n' 0 'ruff-format'
    # Add log messages to the main log file if in parallel mode
    [[ -n "$LOGFILE" && "$PARALLEL" -eq 1 ]] && flush_logs 'ruff-format'
    # Build command for formatting with configuration options
    ruff_format_cmd=("$VIRTUAL_ENV/$SECOND_DIR/ruff" 'format')
    ruff_format_cmd+=("${RUFF_FORMAT_OPTS[@]}")
    # Run formatting and capture result
    # (Everything written to either stdout (success) or stderr (failure))
    RUFF_FORMAT_OUTPUT="$(
        "${ruff_format_cmd[@]}" "${targets[@]}" 2>&1
    )"
    # Exits with code 0 if all files were already properly formatted
    # or were successfully reformatted and exits with code 2
    # if it gets a bad option or finds an unformattable file
    RUFF_FORMAT_EXIT="$?"
    # Default event code to 0 and change to 2 if exit code is non-zero
    RUFF_FORMAT_EVENT_CODE=0
    [[ "$RUFF_FORMAT_EXIT" -ne 0 ]] && RUFF_FORMAT_EVENT_CODE=2
    # Standardize by stripping empty lines
    RUFF_FORMAT_OUTPUT="$(strip_empty_lines "$RUFF_FORMAT_OUTPUT")"
    # Escape single backslashes on Windows
    [[ "$IS_WINDOWS" -eq 1 ]] \
        && RUFF_FORMAT_OUTPUT="$(
        escape_single_backslashes "$RUFF_FORMAT_OUTPUT"
    )"
    handle_output \
        "$RUFF_FORMAT_OUTPUT\n" "$RUFF_FORMAT_EVENT_CODE" 'ruff-format'
    update_exit_code "$RUFF_FORMAT_EVENT_CODE" 'ruff-format'
    # Add log messages to the main log file if in parallel mode
    [[ -n "$LOGFILE" && "$PARALLEL" -eq 1 ]] && flush_logs 'ruff-format'
    # Return early if import sorting is disabled
    if [[ "$RUFF_SORT" -eq 0 ]]; then
        report_runtime "$RUFF_FORMAT_START_TIME" 'ruff-format'
        [[ -n "$LOGFILE" && "$PARALLEL" -eq 1 ]] && flush_logs 'ruff-format'
        return 0
    fi
    # Build command for import sorting with configuration options
    ruff_sort_cmd=("$VIRTUAL_ENV/$SECOND_DIR/ruff" 'check' '--select=I' '--fix')
    ruff_sort_cmd+=("${RUFF_SORT_OPTS[@]}")
    # Run import sorting and capture result
    RUFF_SORT_OUTPUT="$(
        "${ruff_sort_cmd[@]}" "${targets[@]}" 2>&1
    )"
    # Exits with code 0 if all imports were already properly sorted
    # or were successfully sorted, exits with code 1 if it finds
    # an unsortable file, and exits with code 2 if it gets a bad option
    RUFF_SORT_EXIT="$?"
    # Default event code to 0 and change to 2 if exit code is non-zero
    RUFF_SORT_EVENT_CODE=0
    [[ "$RUFF_SORT_EXIT" -ne 0 ]] && RUFF_SORT_EVENT_CODE=2
    # Standardize by stripping empty lines
    RUFF_SORT_OUTPUT="$(strip_empty_lines "$RUFF_SORT_OUTPUT")"
    # Escape single backslashes on Windows
    [[ "$IS_WINDOWS" -eq 1 ]] \
        && RUFF_SORT_OUTPUT="$(escape_single_backslashes "$RUFF_SORT_OUTPUT")"
    handle_output \
        "$RUFF_SORT_OUTPUT\n" "$RUFF_SORT_EVENT_CODE" 'ruff-format'
    # Update the exit code if the sort event code is greater than the
    # format event code (e.g., if format succeeded but sort failed) so that the
    # final exit code reflects the most severe event that occurred
    if [[ "$RUFF_SORT_EVENT_CODE" -gt "$RUFF_FORMAT_EVENT_CODE" ]]; then
        update_exit_code "$RUFF_SORT_EVENT_CODE" 'ruff-format'
    fi
    report_runtime "$RUFF_FORMAT_START_TIME" 'ruff-format'
    # Add log messages to the main log file if in parallel mode
    [[ -n "$LOGFILE" && "$PARALLEL" -eq 1 ]] && flush_logs 'ruff-format'
}

# ----------------------------------------------------------------------
# Ruff linting
# ----------------------------------------------------------------------
# _ruff_lint
#   Runs ruff linting on the specified targets and captures the output.
_ruff_lint() {
    RUFF_LINT_START_TIME="$(now)"
    # Make sure ruff is available
    if ! check_cmd "$VIRTUAL_ENV/$SECOND_DIR/ruff"; then return 1; fi
    # Display header if not in quiet mode
    [[ "$PARALLEL" -eq 1 ]] && handle_output '\nRuff linting:\n' 0 'ruff-lint'
    [[ "$PARALLEL" -eq 0 ]] \
        && handle_output '\nRunning ruff linting...\n' 0 'ruff-lint'
    # Build command with configuration options
    ruff_lint_cmd=(
        "$VIRTUAL_ENV/$SECOND_DIR/ruff"
        'check'
        "--config=$CONFIG_FILE"
        "--target-version=py3$RUFF_PYTHON"
    )
    [[ "$RUFF_PREVIEW" -eq 1 ]] && ruff_lint_cmd+=('--preview')
    ruff_lint_cmd+=("${RUFF_LINT_OPTS[@]}")
    # Run linting and capture result
    # (If it runs successfully, it writes to stdout, even if issues found;
    # if it fails to run, it writes to stderr and exits with non-zero code;
    # it also exits with a non-zero code if any issues are found.
    # Always runs with --statistics on the first pass. A repeat without it
    # is done later if the full output is requested and issues are found)
    RUFF_LINT_OUTPUT="$(
        "${ruff_lint_cmd[@]}" '--statistics' "${targets[@]}" 2>&1
    )"
    # Exits with code 0 if no issues are found, exits with code 1 if
    # any issues are found (including an invalid Python file),
    # and exits with code 2 if it gets a bad option
    RUFF_LINT_EXIT="$?"
    RUFF_LINT_EVENT_CODE="$RUFF_LINT_EXIT"
    # Standardize by stripping empty lines
    RUFF_LINT_OUTPUT="$(strip_empty_lines "$RUFF_LINT_OUTPUT")"
    # Escape single backslashes on Windows
    [[ "$IS_WINDOWS" -eq 1 ]] \
        && RUFF_LINT_OUTPUT="$(escape_single_backslashes "$RUFF_LINT_OUTPUT")"
    # Handle result based on exit code of the first run:
    # - 0: no issues found, so report success message and return early
    # - 1: issues found, so if full output requested, run a second time
    #      without --statistics to get the full output;
    #      otherwise, report the statistics output from the first run and return
    # - 2: failed to run, so report the error output and return early
    if [[ "$RUFF_LINT_EXIT" -eq 0 ]]; then
        # Report success message mimicking the Ruff standard "no issues" output
        # on success when quiet mode is not enabled to signal success to user
        handle_output 'All checks passed!\n' 0 'ruff-lint'
        report_runtime "$RUFF_LINT_START_TIME" 'ruff-lint'
        # No need for a second run since there are no issues, so return early
        return 0
    elif [[ "$RUFF_LINT_EXIT" -eq 2 ]]; then
        # Report the error output if it failed to run
        handle_output "$RUFF_LINT_OUTPUT\n" "$RUFF_LINT_EVENT_CODE" 'ruff-lint'
        update_exit_code "$RUFF_LINT_EVENT_CODE" 'ruff-lint'
        report_runtime "$RUFF_LINT_START_TIME" 'ruff-lint'
        # Skip the second run and return early since it will likely fail again
        return "$RUFF_LINT_EVENT_CODE"
    fi
    # Generate full output with a second run if issues were found and
    # full output was requested (FULL_OUTPUT_FILE=1 implies log file exists)
    if [[ "$RUFF_FULL_OUTPUT" -eq 1 || "$FULL_OUTPUT_FILE" -eq 1 ]]; then
        # Run a second time without --statistics to get the full output
        RUFF_LINT_FULL_OUTPUT="$(
            "${ruff_lint_cmd[@]}" "${targets[@]}" 2>&1
        )"
        # Check that the exit code is still the same as the first run
        RUFF_LINT_2ND_EXIT="$?"
        if [[ "$RUFF_LINT_2ND_EXIT" -ne "$RUFF_LINT_EXIT" ]]; then
            local msg='Warning: Ruff linting exit code changed between runs: '
            msg+="first run exit code was $RUFF_LINT_EXIT, "
            msg+="second run exit code was $RUFF_LINT_2ND_EXIT\n"
            handle_output "$msg" 0 'ruff-lint'
        fi
        # Standardize by stripping empty lines
        RUFF_LINT_FULL_OUTPUT="$(strip_empty_lines "$RUFF_LINT_FULL_OUTPUT")"
        # Escape single backslashes on Windows
        [[ "$IS_WINDOWS" -eq 1 ]] \
            && RUFF_LINT_FULL_OUTPUT="$(
                escape_single_backslashes "$RUFF_LINT_FULL_OUTPUT"
            )"
        # Append the new output to the first, separated by a marker string
        # used by the extractor function to separate them
        RUFF_LINT_OUTPUT="$RUFF_LINT_OUTPUT"
        RUFF_LINT_OUTPUT+="$RUFF_LINT_OUTPUT_SEP$RUFF_LINT_FULL_OUTPUT"
    fi
    # Report the final output
    handle_output "$RUFF_LINT_OUTPUT" "$RUFF_LINT_EVENT_CODE" 'ruff-lint-full'
    update_exit_code "$RUFF_LINT_EVENT_CODE" 'ruff-lint'
    report_runtime "$RUFF_LINT_START_TIME" 'ruff-lint'
}

# ----------------------------------------------------------------------
# Mypy - static type checking
# ----------------------------------------------------------------------
# _mypy
#   Runs mypy in either regular or daemon mode on the specified targets.
_mypy() {
    MYPY_START_TIME="$(now)"
    # Make sure (d)mypy is available
    if [[ "$DMYPY" -eq 1 ]]; then
        if ! check_cmd "$VIRTUAL_ENV/$SECOND_DIR/dmypy"; then return 1; fi
    else
        if ! check_cmd "$VIRTUAL_ENV/$SECOND_DIR/mypy"; then return 1; fi
    fi
    # Display header if not in quiet mode
    [[ "$PARALLEL" -eq 1 ]] && handle_output '\nMypy:\n' 0 'mypy'
    [[ "$PARALLEL" -eq 0 ]] && handle_output '\nRunning mypy...\n' 0 'mypy'
    # Determine valid targets (mypy requires at least one .py/.pyi file)
    mypy_targets=()
    for target in "${targets[@]}"; do
        if find "$target" -name '*.py' -o -name '*.pyi' \
                2>/dev/null | grep -q .; then
            mypy_targets+=("$target")
        else
            handle_output \
                "Skipping mypy for $target: no .py or .pyi files found.\n" \
                0 \
                'mypy'
        fi
    done
    # Return early and warn if no valid targets found and not in quiet mode
    # or if mypy was explicitly requested with -o/--only
    if [[ "${#mypy_targets[@]}" -eq 0 ]]; then
        # Treat "no targets" as a failure to run (event code 2) if it was
        # explicitly requested with -o/--only; otherwise, use event code 0 since
        # there were technically no issues and the user may have expected this
        if [[ "$ONLY_TOOLS" == *'mypy'* ]]; then
            MYPY_SKIP_EVENT_CODE=2
        else
            MYPY_SKIP_EVENT_CODE=0
        fi
        # Report "no targets" result
        handle_output \
            'No valid targets for mypy; skipping.\n' \
            "$MYPY_SKIP_EVENT_CODE" \
            'mypy'
        update_exit_code "$MYPY_SKIP_EVENT_CODE" 'mypy'
        report_runtime "$MYPY_START_TIME" 'mypy'
        return "$MYPY_SKIP_EVENT_CODE"
    fi
    # Run mypy in specified mode and capture result
    # Stop daemon if daemon mode is enabled and a restart was requested
    if [[ "$DMYPY" -eq 1 ]] && [[ "$DMYPY_RESTART" -eq 1 ]]; then
        DMYPY_STOP_RESULT="$($VIRTUAL_ENV/$SECOND_DIR/dmypy stop 2>&1)"
        # Exits with code 0 if the daemon was stopped successfully,
        # exits with code 1 if the daemon was not running,
        # and exits with code 2 if it gets a bad option
        DMYPY_STOP_EXIT="$?"
        # Report result if not in quiet mode; do not report non-zero exit in
        # quiet mode because it is likely benign (daemon wasn't already running)
        handle_output "$DMYPY_STOP_RESULT\n" 0 'mypy'
    fi
    # Run mypy in daemon mode if specified
    if [[ "$DMYPY" -eq 1 ]]; then
        # Build command for daemon start with configuration options
        dmypy_start_cmd=("$VIRTUAL_ENV/$SECOND_DIR/dmypy" 'start')
        dmypy_start_cmd+=("${DMYPY_START_OPTS[@]}")
        dmypy_start_cmd+=('--' "--config-file=$CONFIG_FILE")
        # Run dmypy start command and capture result
        DMYPY_START_RESULT="$(
            "${dmypy_start_cmd[@]}" 2>&1
        )"
        # Exits with code 0 if the daemon was started successfully,
        # exits with code 1 if the daemon is already running,
        # and exits with code 2 if it gets a bad option
        DMYPY_START_EXIT="$?"
        # Report result if not in quiet mode or if daemon failed to start
        # (dmypy reports exit code 1 if daemon is already running, so we
        # check the actual error message to avoid false positives in quiet mode)
        if [[ "$DMYPY_START_EXIT" -eq 1 ]] \
                && [[ "$DMYPY_START_RESULT" != 'Daemon is still alive' ]]; then
            handle_output "$DMYPY_START_RESULT\n" 0 'mypy'
            # On failure, toggle daemon mode off to enable non-daemon fallback
            handle_output 'Attempting fallback to non-daemon mode...\n' 0 'mypy'
            # Make sure regular mypy is available
            if ! check_cmd "$VIRTUAL_ENV/$SECOND_DIR/mypy"; then
                report_runtime "$MYPY_START_TIME" 'mypy'
                return 1
            fi
            DMYPY=0
        else
            handle_output "$DMYPY_START_RESULT\n" 0 'mypy'
        fi
        # Make sure fallback wasn't toggled
        if [[ "$DMYPY" -eq 1 ]]; then
            # Build command for daemon mode check with configuration options
            dmypy_check_cmd=("$VIRTUAL_ENV/$SECOND_DIR/dmypy" 'check')
            dmypy_check_cmd+=("${DMYPY_CHECK_OPTS[@]}")
            # Run the check command using the running daemon and capture result
            MYPY_OUTPUT="$(
                "${dmypy_check_cmd[@]}" "${mypy_targets[@]}" 2>&1
            )"
            # Exits with code 0 if no issues are found, exits with code 1 if
            # any issues are found, and exits with code 2 if
            # it finds an invalid Python file or gets a bad option
            MYPY_EXIT="$?"
            MYPY_EVENT_CODE="$MYPY_EXIT"
        fi
    fi
    # Run in non-daemon mode if specified or fallback set and capture result
    if [[ "$DMYPY" -eq 0 ]]; then
        # Build command for non-daemon mode with configuration options
        mypy_cmd=(
            "$VIRTUAL_ENV/$SECOND_DIR/mypy"
            "--config-file=$CONFIG_FILE"
            "${MYPY_OPTS[@]}"
        )
        # Run mypy in non-daemon mode and capture result
        MYPY_OUTPUT="$(
            "${mypy_cmd[@]}" "${mypy_targets[@]}" 2>&1
        )"
        # Exits with code 0 if no issues are found, exits with code 1 if
        # any issues are found, and exits with code 2 if
        # it finds an invalid Python file or gets a bad option
        MYPY_EXIT="$?"
    fi
    # Mypy may exit non-zero on warnings for things like unused configs,
    # which is not wanted in quiet mode, especially if only running on a
    # subset of files, so check output for the "Success: no issues found"
    # line and suppress the output if found and in quiet mode
    # (We only care about suppressing output in the "non-zero exit with no
    # actual issues" case when quiet mode is enabled, since in non-quiet mode,
    # the message will be output regardless (the only difference is
    # stdout vs stderr for console output, which is less important
    # than only emitting on actual issues in quiet mode).)
    if [[ "$MYPY_OUTPUT" == *'Success: no issues found in'* ]]; then
        MYPY_EVENT_CODE=0
    else
        MYPY_EVENT_CODE="$MYPY_EXIT"
    fi
    # Standardize by stripping empty lines
    MYPY_OUTPUT="$(strip_empty_lines "$MYPY_OUTPUT")"
    # Escape single backslashes on Windows
    [[ "$IS_WINDOWS" -eq 1 ]] \
        && MYPY_OUTPUT="$(escape_single_backslashes "$MYPY_OUTPUT")"
    # Report result
    handle_output "$MYPY_OUTPUT\n" "$MYPY_EVENT_CODE" 'mypy'
    update_exit_code "$MYPY_EVENT_CODE" 'mypy'
    report_runtime "$MYPY_START_TIME" 'mypy'
}

# ----------------------------------------------------------------------
# Pyright - static type checking and analysis
# ----------------------------------------------------------------------
# _pyright
#   Runs pyright on the specified targets and captures the output.
_pyright() {
    PYRIGHT_START_TIME="$(now)"
    # Make sure pyright is available
    if ! check_cmd "$VIRTUAL_ENV/$SECOND_DIR/pyright"; then return 1; fi
    # Display header if not in quiet mode
    [[ "$PARALLEL" -eq 1 ]] && handle_output '\nPyright:\n' 0 'pyright'
    [[ "$PARALLEL" -eq 0 ]] \
        && handle_output '\nRunning pyright...\n' 0 'pyright'
    # Create temporary files to hold stdout and stderr
    pyright_outfile="$tmp_dir/pyright_output.txt"
    pyright_errfile="$tmp_dir/pyright_error.txt"
    # Build command
    pyright_cmd=(
        "$VIRTUAL_ENV/$SECOND_DIR/pyright"
        "--project=$CONFIG_FILE"
        "--pythonpath=$VIRTUAL_ENV/$SECOND_DIR/python"
        "${PYRIGHT_OPTS[@]}"
    )
    # Run pyright and capture result to separate stdout and stderr files
    "${pyright_cmd[@]}" "${targets[@]}" \
        > "$pyright_outfile" 2> "$pyright_errfile"
    # Exits with code 0 if no issues are found, exits with code 1
    # if any issues are found (including an invalid Python file),
    # and exits with code 4 if it gets a bad option
    # (It may emit a version update notice, but it doesn't affect the exit code)
    PYRIGHT_EXIT="$?"
    # Cap the event code at 2 to map Pyright's exit codes to our convention
    # (0=no issues, 1=issues found, 2=tool execution failure)
    PYRIGHT_EVENT_CODE="$(min "$PYRIGHT_EXIT" 2)"
    # Report issues from Pyright's stdout if issues found or not in quiet mode
    if [[ -s "$pyright_outfile" ]]; then
        PYRIGHT_STD_OUTPUT="$(strip_empty_lines "$(cat "$pyright_outfile")")"
        # Escape single backslashes on Windows
        [[ "$IS_WINDOWS" -eq 1 ]] \
            && PYRIGHT_STD_OUTPUT="$(
                escape_single_backslashes "$PYRIGHT_STD_OUTPUT"
            )"
        handle_output \
            "$PYRIGHT_STD_OUTPUT\n" "$PYRIGHT_EVENT_CODE" 'pyright'
    fi
    # Report results from stderr if exit code non-zero
    # and stderr is non-empty (should only be the case on failure to run)
    if [[ "$PYRIGHT_EXIT" -ne 0 ]] && [[ -s "$pyright_errfile" ]]; then
        # Possibly add a newline only if no issues were found
        # so that we keep the Pyright output together
        # (Use non-zero severity to get past quiet mode check in handle_output)
        [[ "$PYRIGHT_EVENT_CODE" -eq 1 ]] && handle_output '\n' 1 'pyright'
        PYRIGHT_ERR_OUTPUT="$(strip_empty_lines "$(cat "$pyright_errfile")")"
        # Escape single backslashes on Windows
        [[ "$IS_WINDOWS" -eq 1 ]] \
            && PYRIGHT_ERR_OUTPUT="$(
                escape_single_backslashes "$PYRIGHT_ERR_OUTPUT"
            )"
        handle_output \
            "$PYRIGHT_ERR_OUTPUT\n" "$PYRIGHT_EVENT_CODE" 'pyright'
    fi
    update_exit_code "$PYRIGHT_EVENT_CODE" 'pyright'
    report_runtime "$PYRIGHT_START_TIME" 'pyright'
}

# ----------------------------------------------------------------------
# Pylint - comprehensive linting
# ----------------------------------------------------------------------
# _pylint
#   Runs pylint on the specified targets and captures the output.
_pylint() {
    PYLINT_START_TIME="$(now)"
    # Make sure pylint is available
    if ! check_cmd "$VIRTUAL_ENV/$SECOND_DIR/pylint"; then return 1; fi
    [[ "$PARALLEL" -eq 1 ]] && handle_output '\nPylint:\n' 0 'pylint'
    [[ "$PARALLEL" -eq 0 ]] && handle_output '\nRunning pylint...\n' 0 'pylint'
    # Build command with configuration options
    pylint_cmd=("$VIRTUAL_ENV/$SECOND_DIR/pylint" "${PYLINT_OPTS[@]}")
    # Run Pylint and capture result
    PYLINT_OUTPUT="$(
        "${pylint_cmd[@]}" "${targets[@]}" 2>&1
    )"
    # Exits with bit-encoded values. 0=no issues, 1=fatal message issued,
    # 2=error message issued, 4=warning message issued,
    # 8=refactor message issued, 16=convention message issued, 32=usage error.
    PYLINT_EXIT="$?"
    # Map Pylint's exit codes to our convention:
    # - If exit code is 0, then no issues found (event code 0)
    # - If exit code is 32, then tool execution failure (event code 2)
    # - Otherwise, issues found (event code 1)
    PYLINT_EVENT_CODE="$(
        if [[ "$PYLINT_EXIT" -eq 0 ]]; then
            printf '0'
        elif [[ "$PYLINT_EXIT" -eq 32 ]]; then
            printf '2'
        else
            printf '1'
        fi
    )"
    # Get the result line (empty if Pylint failed or no code was analyzed
    # (this is different from no target files, which shouldn't happen))
    PYLINT_RESULT_REGEX='Your code has been rated at [0-9]+\.[0-9]+/10'
    [[ "$PYLINT_OUTPUT" =~ $PYLINT_RESULT_REGEX ]] \
        && PYLINT_RESULT_LINE="$BASH_REMATCH" \
        || PYLINT_RESULT_LINE=''
    # Define line to check for no issues found (only beginning of line)
    NO_PYLINT_ISSUES_LINE='Your code has been rated at 10.00/10'
    # Clean up the results for display
    if [[ -z "$PYLINT_RESULT_LINE" ]]; then
        # If no code was found, the output is empty, so add a message to clarify
        PYLINT_RESULT='Pylint ran successfully but found no code to analyze.'
    elif [[ "$PYLINT_RESULT_LINE" == "$NO_PYLINT_ISSUES_LINE"* ]]; then
        # Strip unnecessary blank line and '---' line above the result line
        # by just using the result line instead of the full output
        PYLINT_RESULT="$PYLINT_RESULT_LINE"
    else
        # An issue was found or it failed to run, so use the whole output
        PYLINT_RESULT="$(strip_empty_lines "$PYLINT_OUTPUT")"
        # Escape single backslashes on Windows
        [[ "$IS_WINDOWS" -eq 1 ]] \
            && PYLINT_RESULT="$(escape_single_backslashes "$PYLINT_RESULT")"
    fi
    # Report result
    handle_output "$PYLINT_RESULT\n" "$PYLINT_EVENT_CODE" 'pylint'
    update_exit_code "$PYLINT_EVENT_CODE" 'pylint'
    report_runtime "$PYLINT_START_TIME" 'pylint'
}

# ----------------------------------------------------------------------
# Bandit - security vulnerability scanning
# ----------------------------------------------------------------------
# _bandit
#   Runs bandit on the specified targets and captures the output.
_bandit() {
    BANDIT_START_TIME="$(now)"
    # Make sure bandit is available
    if ! check_cmd "$VIRTUAL_ENV/$SECOND_DIR/bandit"; then return 1; fi
    # Display header if not in quiet mode
    [[ "$PARALLEL" -eq 1 ]] && handle_output '\nBandit:\n' 0 'bandit'
    [[ "$PARALLEL" -eq 0 ]] && handle_output '\nRunning bandit...\n' 0 'bandit'
    # Build command with configuration options
    bandit_cmd=(
        "$VIRTUAL_ENV/$SECOND_DIR/bandit"
        "--configfile=$CONFIG_FILE"
        '--recursive'
        "${BANDIT_OPTS[@]}"
    )
    # Run bandit and capture result
    BANDIT_OUTPUT="$(
        "${bandit_cmd[@]}" "${targets[@]}" 2>&1
    )"
    # Exits with code 0 if no issues are found, exits with code 1 if
    # any issues are found, and exits with code 2 if it gets a bad option.
    # If an invalid Python file is found, it skips the file and can still
    # return with code 0 if all other files have no issues.
    BANDIT_EXIT="$?"
    # Check that no files were skipped due to invalid Python files;
    # if any were, manually set exit code to 100 to indicate a special case
    BANDIT_LAST_LINE="${BANDIT_OUTPUT##*$'\n'}"
    if [[ "$BANDIT_LAST_LINE" != 'Files skipped (0):' ]] \
            && [[ \
                -n "$(printf '%s' "$BANDIT_OUTPUT" | grep 'syntax error')" \
            ]]; then
        BANDIT_EXIT=100
    fi
    # Map the exit code to our convention to account for 100 -> 1 special case
    if [[ "$BANDIT_EXIT" -eq 100 ]]; then
        BANDIT_EVENT_CODE=1
    else
        BANDIT_EVENT_CODE="$BANDIT_EXIT"
    fi
    # Standardize by stripping empty lines
    BANDIT_OUTPUT="$(strip_empty_lines "$BANDIT_OUTPUT")"
    # Escape single backslashes on Windows
    [[ "$IS_WINDOWS" -eq 1 ]] \
        && BANDIT_OUTPUT="$(escape_single_backslashes "$BANDIT_OUTPUT")"
    # Report result
    handle_output "$BANDIT_OUTPUT" "$BANDIT_EVENT_CODE" 'bandit-full'
    update_exit_code "$BANDIT_EVENT_CODE" 'bandit'
    report_runtime "$BANDIT_START_TIME" 'bandit'
}

# ----------------------------------------------------------------------
# Pydoclint - docstring checking
# ----------------------------------------------------------------------
# _pydoclint
#   Runs pydoclint on the specified targets and captures the output.
_pydoclint() {
    PYDOCLINT_START_TIME="$(now)"
    # Make sure pydoclint is available
    if ! check_cmd "$VIRTUAL_ENV/$SECOND_DIR/pydoclint"; then return 1; fi
    # Display header if not in quiet mode
    [[ "$PARALLEL" -eq 1 ]] && handle_output '\nPydoclint:\n' 0 'pydoclint'
    [[ "$PARALLEL" -eq 0 ]] \
        && handle_output '\nRunning pydoclint...\n' 0 'pydoclint'
    # Build command with configuration options
    pydoclint_cmd=(
        "$VIRTUAL_ENV/$SECOND_DIR/pydoclint"
        "--config=$CONFIG_FILE"
        "--style=$PYDOCLINT_STYLE"
    )
    [[ "$PYDOCLINT_SKIP_SHORT" -eq 0 ]] \
        && pydoclint_cmd+=('--skip-checking-short-docstrings=False')

    # Determine baseline handling based on
    # auto-baseline and baseline file options

    # Case 1: Baseline file is "no"/"none" (case-insensitive),
    #         allowing users to explicitly disable baseline usage;
    #         auto-baseline setting is ignored
    if [[ \
        "${PYDOCLINT_BASELINE_FILE,,}" == "n" \
        || "${PYDOCLINT_BASELINE_FILE,,}" == "no" \
        || "${PYDOCLINT_BASELINE_FILE,,}" == "none" \
    ]]; then
        # Use an empty temporary file as the baseline
        # to effectively disable baseline comparison
        PYDOCLINT_BASELINE_FILE="$(mktemp "$tmp_dir/pydoclint-baseline-XXXXXX")"
    # Case 2: Auto-baseline is off and a baseline file is provided
    elif [[ "$PYDOCLINT_AUTO_BASELINE" -eq 0 ]] \
            && [[ -n "$PYDOCLINT_BASELINE_FILE" ]]; then
        # Check for existence of the provided baseline file;
        # if not found, print a warning and proceed without a baseline
        if [ ! -f "$PYDOCLINT_BASELINE_FILE" ]; then
            local msg="Warning: Baseline file $PYDOCLINT_BASELINE_FILE "
            msg+='not found; proceeding without a baseline.\n'
            handle_output "$msg" 0 'pydoclint'
            # Use same empty temporary file approach as for
            # explicit disables to disable baseline comparison
            PYDOCLINT_BASELINE_FILE="$(
                mktemp "$tmp_dir/pydoclint-baseline-XXXXXX"
            )"
        fi
    # Case 3: Auto-baseline is on and a baseline file is provided
    elif [[ "$PYDOCLINT_AUTO_BASELINE" -eq 1 ]] \
            && [[ -n "$PYDOCLINT_BASELINE_FILE" ]]; then
        # Check for existence of the provided baseline file;
        # if not found, generate one on this run
        if [ ! -f "$PYDOCLINT_BASELINE_FILE" ]; then
            pydoclint_cmd+=('--generate-baseline=True')
        fi
    # Case 4: Auto-baseline is on and no baseline file provided
    elif [[ "$PYDOCLINT_AUTO_BASELINE" -eq 1 ]] \
            && [[ -z "$PYDOCLINT_BASELINE_FILE" ]]; then
        # Check for existence of any default baseline files
        # and use the first one found, if any;
        # if none found, generate one on this run
        if [ -f '.pydoclint-baseline.txt' ]; then
            PYDOCLINT_BASELINE_FILE='.pydoclint-baseline.txt'
        elif [ -f 'pydoclint-baseline.txt' ]; then
            PYDOCLINT_BASELINE_FILE='pydoclint-baseline.txt'
        elif [ -f '.pydoclint-baseline' ]; then
            PYDOCLINT_BASELINE_FILE='.pydoclint-baseline'
        else
            # If no baseline file exists, generate one on this run
            pydoclint_cmd+=('--generate-baseline=True')
            # Set default baseline file name for subsequent runs to find
            PYDOCLINT_BASELINE_FILE="$PYDOCLINT_FALLBACK_BASELINE_FILE"
        fi
    # Case 5: If here, auto-baseline is off and no baseline file provided;
    #         nothing is needed (falls back to config file, then no baseline)
    fi
    # Add the baseline file option to the command if applicable
    [[ -n "$PYDOCLINT_BASELINE_FILE" ]] \
        && pydoclint_cmd+=("--baseline=$PYDOCLINT_BASELINE_FILE")

    # Add any additional specified options
    pydoclint_cmd+=("${PYDOCLINT_OPTS[@]}")

    # Run Pydoclint and capture result
    PYDOCLINT_OUTPUT="$(
        "${pydoclint_cmd[@]}" "${targets[@]}" 2>&1
    )"
    PYDOCLINT_EXIT="$?"
    # Exits with code 0 if no issues are found, exits with code 1 if
    # any issues are found (including if it finds an invalid Python file),
    # and exits with code 2 if it gets a bad option
    PYDOCLINT_EVENT_CODE="$PYDOCLINT_EXIT"
    # Standardize by stripping empty lines
    PYDOCLINT_OUTPUT="$(strip_empty_lines "$PYDOCLINT_OUTPUT")"
    # Escape single backslashes on Windows
    [[ "$IS_WINDOWS" -eq 1 ]] \
        && PYDOCLINT_OUTPUT="$(escape_single_backslashes "$PYDOCLINT_OUTPUT")"
    # Report result
    handle_output "$PYDOCLINT_OUTPUT" "$PYDOCLINT_EVENT_CODE" 'pydoclint-full'
    update_exit_code "$PYDOCLINT_EVENT_CODE" 'pydoclint'
    report_runtime "$PYDOCLINT_START_TIME" 'pydoclint'
}

# ----------------------------------------------------------------------
# Pytest - testing framework
# ----------------------------------------------------------------------
# _pytest
#   Runs pytest and captures the output.
_pytest() {
    PYTEST_START_TIME="$(now)"
    # Make sure pytest is available
    if ! check_cmd "$VIRTUAL_ENV/$SECOND_DIR/pytest"; then return 1; fi
    # Display header if not in quiet mode
    [[ "$PARALLEL" -eq 1 ]] && handle_output '\nPytest:\n' 0 'pytest'
    [[ "$PARALLEL" -eq 0 ]] \
        && handle_output '\nRunning pytest...\n' 0 'pytest'
    # Create temporary files to hold stdout and stderr
    pytest_outfile="$tmp_dir/pytest_output.txt"
    pytest_errfile="$tmp_dir/pytest_error.txt"
    # Build command
    pytest_cmd=(
        "$VIRTUAL_ENV/$SECOND_DIR/pytest" "${PYTEST_OPTS[@]}"
    )
    # Add explicit targets if provided; otherwise, uses implicit discovery
    if [[ "${#PYTEST_TARGETS[@]}" -gt 0 ]]; then
        pytest_cmd+=("${PYTEST_TARGETS[@]}")
    fi
    # Run pytest and capture result to separate stdout and stderr files
    "${pytest_cmd[@]}" 2> "$pytest_errfile" > "$pytest_outfile"
    # Exits with code 0 if all tests passed, exits with code 1 if
    # any tests failed or errors occurred (e.g., found invalid Python file),
    # exits with code 4 if it gets a bad option, and exits with code 5 if no
    # tests were collected. (It may emit warnings such as no-data-collected,
    # but they don't affect the exit code)
    PYTEST_EXIT="$?"
    # Cap the event code at 2 to map Pytest's exit codes to our convention
    # (0=all tests passed, 1=tests failed,
    # 2=tool execution failure (including no tests collected))
    PYTEST_EVENT_CODE="$(min "$PYTEST_EXIT" 2)"
    # Set event code to 4 if there were test failures
    [[ "$PYTEST_EVENT_CODE" -eq 1 ]] && PYTEST_EVENT_CODE=4
    # Report issues from Pytest's stdout if issues found or not in quiet mode
    if [[ -s "$pytest_outfile" ]]; then
        PYTEST_STD_OUTPUT="$(strip_empty_lines "$(cat "$pytest_outfile")")"
        # Escape single backslashes on Windows
        [[ "$IS_WINDOWS" -eq 1 ]] \
            && PYTEST_STD_OUTPUT="$(
                escape_single_backslashes "$PYTEST_STD_OUTPUT"
            )"
        handle_output \
            "$PYTEST_STD_OUTPUT\n" "$PYTEST_EVENT_CODE" 'pytest-full'
    fi
    # Report results from stderr if exit code non-zero
    # and stderr is non-empty (should only be the case on failure to run)
    if [[ "$PYTEST_EXIT" -ne 0 ]] && [[ -s "$pytest_errfile" ]]; then
        # Possibly add a newline only if no issues were found
        # so that we keep the Pytest output together
        # (Use non-zero severity to get past quiet mode check in handle_output)
        [[ "$PYTEST_EVENT_CODE" -eq 4 ]] && handle_output '\n' 1 'pytest'
        PYTEST_ERR_OUTPUT="$(strip_empty_lines "$(cat "$pytest_errfile")")"
        # Escape single backslashes on Windows
        [[ "$IS_WINDOWS" -eq 1 ]] \
            && PYTEST_ERR_OUTPUT="$(
                escape_single_backslashes "$PYTEST_ERR_OUTPUT"
            )"
        handle_output \
            "$PYTEST_ERR_OUTPUT\n" "$PYTEST_EVENT_CODE" 'pytest'
    fi
    update_exit_code "$PYTEST_EVENT_CODE" 'pytest'
    report_runtime "$PYTEST_START_TIME" 'pytest'
}

# ======================================================================
# Run tools
# ======================================================================

# Display run metadata when not in quiet mode
PARALLEL_STATUS="$(
    [[ "$PARALLEL" -eq 1 ]] && printf 'enabled' || printf 'disabled'
)"
init_msg='Running Python dev tools...\n'
init_msg+="    Project: $PROJECT_NAME\n"
init_msg+="    Virtual env: $VIRTUAL_ENV\n"
init_msg+="    Config file: $CONFIG_FILE\n"
init_msg+="    Parallel mode: $PARALLEL_STATUS\n"
init_msg+="    Targets: ${targets[*]}\n"
init_msg+="    Start time: $PRETTY_START_TIME\n"
init_msg+="    Tools to run: ${tools_to_run[*]}\n"
handle_output "$init_msg" 0 'pre-run'
# Add log message to main log file if in parallel mode
[[ -n "$LOGFILE" && "$PARALLEL" -eq 1 ]] && flush_logs 'pre-run'

# Disable parallel mode for actual run if less than two non-ruff-format tools
[[ "$n_non_format_tools" -lt 2 ]] && PARALLEL=0

# If running Ruff formatting, run it separately first since
# it modifies files and we want the other tools to see the formatted code
# (the function handles its own output)
[[ "${RUN_TOOL[ruff-format]}" -eq 1 ]] && _ruff_format

# Output a status message about tools running in parallel if not in quiet mode
tool_expr=''
if [[ "$PARALLEL" -eq 1 ]]; then
    # Get list of remaining tools for display
    tool_list=''
    for tool in "${ALL_TOOLS[@]}"; do
        [[ "$tool" != 'ruff-format' ]] \
            && [[ "${RUN_TOOL[$tool]}" -eq 1 ]] \
            && tool_list+="${tool_list:+, }$tool"
    done
    # Add pytest separately if it is running
    if [[ "$PYTEST" -eq 1 ]]; then
        tool_list+="${tool_list:+, }pytest"
    fi
    # Format the list of tools with commas and "and" for display
    last_tool="${tool_list##*, }"
    prev_tools="${tool_list%,*}"
    [[ "$n_non_format_tools" -eq 2 ]] \
        && tool_expr="$prev_tools and $last_tool"
    [[ "$n_non_format_tools" -gt 2 ]] \
        && tool_expr="$prev_tools, and $last_tool"
    handle_output "\nRunning $tool_expr in parallel...\n" 0 'main'
fi

# Run remaining tools in parallel if enabled
if [[ "$PARALLEL" -eq 1 ]]; then
    # Enable job control to allow each process to start a new process group;
    # this way, we can kill each process without running the exit handler early
    # by resetting the SIGINT and SIGTERM traps to default for each child
    set -m
    if [[ "${RUN_TOOL[ruff-lint]}" -eq 1 ]]; then
        ( trap - INT TERM EXIT; _ruff_lint ) \
            > "$tmp_dir/ruff-lint.console" 2>&1 &
        ruff_lint_pid="$!"
        TOOL_PIDS+=("$ruff_lint_pid")
    fi
    if [[ "${RUN_TOOL[mypy]}" -eq 1 ]]; then
        ( trap - INT TERM EXIT; _mypy ) > "$tmp_dir/mypy.console" 2>&1 &
        mypy_pid="$!"
        TOOL_PIDS+=("$mypy_pid")
    fi
    if [[ "${RUN_TOOL[pyright]}" -eq 1 ]]; then
        ( trap - INT TERM EXIT; _pyright ) > "$tmp_dir/pyright.console" 2>&1 &
        pyright_pid="$!"
        TOOL_PIDS+=("$pyright_pid")
    fi
    if [[ "${RUN_TOOL[pylint]}" -eq 1 ]]; then
        ( trap - INT TERM EXIT; _pylint ) > "$tmp_dir/pylint.console" 2>&1 &
        pylint_pid="$!"
        TOOL_PIDS+=("$pylint_pid")
    fi
    if [[ "${RUN_TOOL[bandit]}" -eq 1 ]]; then
        ( trap - INT TERM EXIT; _bandit ) > "$tmp_dir/bandit.console" 2>&1 &
        bandit_pid="$!"
        TOOL_PIDS+=("$bandit_pid")
    fi
    if [[ "${RUN_TOOL[pydoclint]}" -eq 1 ]]; then
        ( trap - INT TERM EXIT; _pydoclint ) \
            > "$tmp_dir/pydoclint.console" 2>&1 &
        pydoclint_pid="$!"
        TOOL_PIDS+=("$pydoclint_pid")
    fi
    if [[ "$PYTEST" -eq 1 ]]; then
        ( trap - INT TERM EXIT; _pytest ) > "$tmp_dir/pytest.console" 2>&1 &
        pytest_pid="$!"
        TOOL_PIDS+=("$pytest_pid")
    fi
    # Disable job control after starting all tool processes
    set +m
    # Wait for all tool processes to finish
    for pid in "${TOOL_PIDS[@]}"; do
        wait "$pid"
    done
    # Display captured output from each tool in the order of ALL_TOOLS
    for tool in "${ALL_TOOLS[@]}"; do
        if [[ "$tool" != 'ruff-format' ]] \
                && [[ "${RUN_TOOL[$tool]}" -eq 1 ]]; then
            if [[ -f "$tmp_dir/$tool.console" ]]; then
                cat "$tmp_dir/$tool.console"
            else
                handle_output \
                    "Error: Output file for $tool not found.\n" 16 "$tool"
                update_exit_code 16 "$tool"
            fi
        fi
    done
    # Handle pytest output separately
    if [[ "$PYTEST" -eq 1 ]]; then
        if [[ -f "$tmp_dir/pytest.console" ]]; then
            cat "$tmp_dir/pytest.console"
        else
            handle_output \
                "Error: Output file for pytest not found.\n" 16 'pytest'
            update_exit_code 16 'pytest'
        fi
    fi
# Otherwise, run remaining tools in series
else
    [[ "${RUN_TOOL[ruff-lint]}" -eq 1 ]] && _ruff_lint
    [[ "${RUN_TOOL[mypy]}" -eq 1 ]] && _mypy
    [[ "${RUN_TOOL[pyright]}" -eq 1 ]] && _pyright
    [[ "${RUN_TOOL[pylint]}" -eq 1 ]] && _pylint
    [[ "${RUN_TOOL[bandit]}" -eq 1 ]] && _bandit
    [[ "${RUN_TOOL[pydoclint]}" -eq 1 ]] && _pydoclint
    [[ "$PYTEST" -eq 1 ]] && _pytest
fi

# Build a final summary message
end_msg=''

# Determine which tools reported issues or errors for the final summary
# (only for parallel mode; in non-parallel mode, we already have the lists)
if [[ "$PARALLEL" -eq 1 ]]; then
    # For each tool, check the temp directory for the signal files
    for tool in "${ALL_TOOLS[@]}"; do
        if [[ "${RUN_TOOL[$tool]}" -eq 1 ]]; then
            [[ -f "$tmp_dir/$tool.iss" ]] \
                && TOOLS_WITH_ISSUES+="${TOOLS_WITH_ISSUES:+, }$tool"
            [[ -f "$tmp_dir/$tool.err" ]] \
                && TOOLS_WITH_ERRORS+="${TOOLS_WITH_ERRORS:+, }$tool"
        fi
    done
    # Handle Pytest separately
    if [[ "$PYTEST" -eq 1 ]]; then
        [[ -f "$tmp_dir/pytest.iss" ]] \
            && TOOLS_WITH_ISSUES+="${TOOLS_WITH_ISSUES:+, }pytest"
        [[ -f "$tmp_dir/pytest.err" ]] \
            && TOOLS_WITH_ERRORS+="${TOOLS_WITH_ERRORS:+, }pytest"
    fi
fi
# Add the lists of tools with issues or errors to the final summary message
[[ -n "$TOOLS_WITH_ISSUES" ]] \
    && end_msg+="\nTools reporting issues: $TOOLS_WITH_ISSUES"
[[ -n "$TOOLS_WITH_ERRORS" ]]\
    && end_msg+="\nTools reporting errors: $TOOLS_WITH_ERRORS"

# Display final summary message
TOTAL_TIME="$(calculate_runtime "$START_TIME" "$(now)")"
end_msg+="\nFinished running dev tools in $TOTAL_TIME seconds.\n"
handle_output "$end_msg" 0 'post-run'

# Report exit code based on tool results and possible errors
EXIT_CODE="$(get_exit_code)"
exit "$EXIT_CODE"
# The on_exit function is called automatically by the trap on script exit
