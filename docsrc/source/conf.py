"""Configuration file for the `Sphinx` documentation builder."""  # ruff: ignore[implicit-namespace-package]

# For the full list of built-in configuration values, see documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
from pathlib import Path


sys.path.insert(0, str(Path("../../src").resolve()))

from sefkhet import __version__  # pylint: disable=wrong-import-position


# -- Project information -----------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "sefkhet"
copyright = (  # pylint: disable=redefined-builtin # ruff: ignore[builtin-variable-shadowing]
    "2026, Danny Collinson"
)
author = "Danny Collinson"
version = __version__
release = version


# -- General configuration ---------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


templates_path = ["_templates"]
exclude_patterns: list[str] = []

today_fmt = "%Y-%m-%d"

nitpicky = True

# -- Extensions configuration ------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.githubpages",
    "myst_parser",
    "nbsphinx",
]

autosummary_generate = True

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_param = True
napoleon_use_keyword = True
napoleon_use_ivar = True
napoleon_use_rtype = False
napoleon_include_init_with_doc = True


# -- Options for HTML output -------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

html_theme_options = {
    "collapse_navigation": False,
    "style_nav_header_background": "#ffffff",
}

html_logo = "./_static/img/sefkhet-logo.png"
html_favicon = "./_static/img/sefkhet-favicon.ico"

html_last_updated_fmt = "%Y-%m-%d at %H:%M UTC"
html_last_updated_use_utc = True
