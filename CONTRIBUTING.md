# Contributing

Information and guidelines about contributing to `snaplog`.

## Developer installation

Developers wishing to work on `snaplog` should clone the GitHub repository using `git clone https://github.com/DannyCollinson/snaplog.git` and create a branch for development using `git branch <branch-name>`, where `<branch-name>` is your desired branch name. Branch naming conventions are described in the **Releases and Branching** section below.

The easiest way to get started is to create a Python virtual environment using `venv`, which we will walk through here, but feel free to use your favorite alternative environment and package management tools (in which case, skip to the next paragraph). To use `venv`, run `python -m venv .venv` from the project root directory, which will create the environment within the `.venv` directory. Activate the environment using `source .venv/bin/activate` (`source .venv/Scripts/activate` if on Windows).

Once your environment is set up, install `snaplog` as an editable package using `pip install -e .[dev]`. This will make the `snaplog` package available in the environment, as well as install the development tools required for `snaplog`.

## Formatting

Code should be formatted by `ruff format .` and `ruff check --select I --fix .` with the configurations set in `pyproject.toml`. All other options should be set to the default. No line should exceed 80 characters; long strings and comments should be split into multiple lines.

Docstrings should be included for all modules, functions and classes, written using Google-style with type hints. No docstring line should exceed 72 characters; long lines should be broken into multiple lines, and long type hints or code snippets within docstrings should be formatted according to `ruff format`.

## Typing

Code should be type-checked using `mypy` and `pyright` with the configurations set in `pyproject.toml`. Overrides of unavoidable typing issues are allowed. All functions should be fully type-hinted.

## Style

Code should attempt to reflect the codebase's existing style as much as possible. Names for functions, variables, etc. should generally prioritize clarity over brevity. Code should prioritize performance, but it should also aim to maximize clarity.

Comments should explain what each non-self-explanatory code section or tricky line is doing in plain language above the code in question, once again balancing clarity and brevity.

Blank lines should be used to break up logical sections of code within functions, but independently-functioning logical sections should be broken into separate functions where feasible.

Code should be checked for style using `pylint src/snaplog tests` and `ruff check --config pyproject.toml` and analyzed with `pyright -p pyproject.toml src/snaplog tests`. Configurations for all are set in `pyproject.toml`. The utmost effort should be made to address all issues, but unavoidable issues can be ignored with `#pylint: disable=X`, `# noqa: X`, and/or `pyright: ignore[X]` comments as applicable, shortening to the code for `X` or even dropping `=X`for `pylint` or dropping `[X]` for `pyright` when line length constrants dictate. As much as possible, try to keep these exceptions as local as possible (ideally inline) instead of file-wide (i.e., placed at the top of the file).

## Docs
Docstrings should use Google-style docstrings with typing included. No line in a docstring should exceed 72 characters. Documentation is built using Sphinx and hosted via [GitHub Pages](https://dannycollinson.github.io/snaplog). Configuration for the docs can be found in `docsrc/source/conf.py`.

Docstrings should be checked using the command `pydoclint --style=google --skip-checking-short-docstrings=True src/snaplog tests`.

## Releases and Branching

Releases will be created on GitHub with a version number tag and pushed to PyPI. Releases occur on an as-needed and as-ready basis and use semantic versioning. Small individual bug fixes and tweaks that do not change the public API will update the patch number (i.e., the third number in the version). More substantial bug fixes and tweaks and those that modify the public API will update the minor version number (i.e., the second number). Large updates in package capabilities and large changes in the public API will update the major version number (i.e., the first number).

The `trunk` branch is the definitive/release branch, and all contributions should be made via pull request from a development or other branch. The `docs` branch is used as the source for the [GitHub Pages site](https://dannycollinson.github.io/snaplog) and should mirror the `trunk` branch except for including the built docs, which should not be included in the `trunk` branch.

Development branch naming conventions are loose, but try to stick to using a `patch/<dev_name>/<patch_name>` format for small fixes and changes reflecting an update at the patch number level, a `feature/<dev_name>/<feature_name>` format for larger updates at the minor version number level, and a `major/<dev_name>/<v#>` format for major version number bumps. As the original author and primary maintainer, Danny Collinosn reserves the right to use the `dev/danny` branch as an all-purpose branch.

## Testing

Testing should be done using `pytest` with `pytest-cov` using the configurations set in `pyproject.toml`. Excepting the case of emergency bug fixes, all tests must pass and the test suite must acheive 100% line and branch coverage before updates will be incorporated into `trunk`. The `test` directory structure should mirror the `src/snaplog` directory structure as closely as possible unless where strict adherence would lead to files of 1000+ lines, in which case subdivisions can be made. Tests should be logically grouped within each file where possible. In accordance with `pytest` standards, a `conftest.py` file can contain reusable fixtures available for all tests.

The `src/snaplog`, `tests`, and `docsrc/source/demos` directories should also be scanned for vulnerabilities with `bandit`. You should run the following command: `bandit -c pyproject.toml -r tests src/snaplog docsrc/source/demos`.

## More

If you have any questions, are interested in learning more about the package, or want to work on `snaplog`, then don't hesitate to create an [issue on GitHub](https://github.com/DannyCollinson/snaplog/issues)!
