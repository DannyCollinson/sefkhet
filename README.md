# Sefkhet

`sefkhet` is a Python package that provides simple setup for complex logging.

![PyPI](https://img.shields.io/pypi/v/my-package.svg)

Check out the **[docs](https://dannycollinson.github.io/sefkhet)** for in-depth information on `sefkhet`, see the [demo](https://dannycollinson.github.io/sefkhet/demos/DEMO.html#) for a demonstration of the package's functionality, or read below for how to get started!

### Quick Links

- [Docs](https://dannycollinson.github.io/sefkhet)
    - [API Reference](https://dannycollinson.github.io/sefkhet/sefkhet.html#)
    - [Demo](https://dannycollinson.github.io/sefkhet/demos/DEMO.html#)
    - [Changelog](https://dannycollinson.github.io/sefkhet/CHANGELOG.html#)
- [GitHub](https://github.com/DannyCollinson/sefkhet)
    - [Issues](https://github.com/DannyCollinson/sefkhet/issues)
    - [Releases](https://github.com/DannyCollinson/sefkhet/releases)

## Installation

Installation is via PyPI. The exact command depends on your preferred package manager, but for `pip`, it's:

```sh
pip install sefkhet
```

## Quickstart

Below is a one-minute introduction to `sefkhet`. For more detailed information, check out the [demo notebook](https://dannycollinson.github.io/sefkhet/demos/DEMO.html#).

### Import

You can import the package using

```py3
import sefkhet
```


### `record`/`rec`

After import, you can immediately start logging with the default configuration using

```py3
sefkhet.record("I <3 sefkhet!")
# or
sefkhet.rec("I <3 sefkhet!")
```

Or, if you only need the `record`/`rec` function, you can do

```py3
from sefkhet import record

record("I <3 sefkhet!")
```


### `Scribe`

You can also use the `Scribe` class as follows:

```py3
scribe = sefkhet.Scribe()
# then
scribe.record("I <3 sefkhet!")
# or
scribe.rec("I <3 sefkhet!")
```


## Contributing

Check out the [Contributing Guide](https://dannycollinson.github.io/sefkhet/CONTRIBUTING.html#) or `CONTRIBUTING.md` for details about contributing!

If you come across any issues while using `sefkhet` or think of any features that you would like to see added, please let us know by creating a new [GitHub Issue](https://github.com/DannyCollinson/sefkhet/issues)!


## Help

If you have any questions about the package, you can refer to the [docs](https://dannycollinson.github.io/sefkhet) and [source code](https://github.com/DannyCollinson/sefkhet).

If you have questions that are still unanswered or run into any issues while using the package, please let us know by creating a new [GitHub Issue](https://github.com/DannyCollinson/sefkhet/issues).


## Thanks for checking out `sefkhet`!
###
