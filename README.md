# `snaplog`

![PyPI](https://img.shields.io/pypi/v/my-package.svg)

`snaplog` is a Python package that makes logging a snap.

Check out the **[docs](https://dannycollinson.github.io/snaplog)** for in-depth information on `snaplog`, see the [demo](https://dannycollinson.github.io/snaplog/demos/DEMO.ipynb) for a demonstration of the package's functionality, or read below for how to get started!

### Quick Links

- [Docs](https://dannycollinson.github.io/snaplog)
    - [API Reference](https://dannycollinson.github.io/snaplog/snaplog.html#)
    - [Demo](https://dannycollinson.github.io/snaplog/demos/DEMO.html#)
    - [Changelog](https://dannycollinson.github.io/snaplog/CHANGELOG.html#)
- [GitHub](https://github.com/DannyCollinson/snaplog)
    - [Issues](https://github.com/DannyCollinson/snaplog/issues)
    - [Releases](https://github.com/DannyCollinson/snaplog/releases)

## Installation

Installation is via PyPI. The exact command depends on your preferred package manager, but for `pip`, it's:

```sh
pip install snaplog
```

## Quickstart

Below is a one-minute introduction to `snaplog`. For more detailed information, check out the [demo notebook](https://dannycollinson.github.io/snaplog/demos/DEMO.html#).

### Import

You can import the package using

```py3
import snaplog
```


### `log`

After import, you can immediately start logging with the default configuration using

```py3
snaplog.log("I <3 snaplog!")
```

Or, if you only need the `log` function, you can do

```py3
from snaplog import log

log("I <3 snaplog!")
```


### `SnapLogger`

You can also use the `SnapLogger` class as follows:

```py3
logger = snaplog.SnapLogger()
logger.log("I <3 snaplog!")
```


## Contributing

Check out the [Contributing Guide](https://dannycollinson.github.io/snaplog/CONTRIBUTING.html#) or `CONTRIBUTING.md` for details about contributing!

If you come across any issues while using `snaplog` or think of any features that you would like to see added, please let us know by creating a new [GitHub Issue](https://github.com/DannyCollinson/snaplog/issues)!


## Help

If you have any questions about the package, you can refer to the [docs](https://dannycollinson.github.io/snaplog) and [source code](https://github.com/DannyCollinson/snaplog).

If you have questions that are still unanswered or run into any issues while using the package, please let us know by creating a new [GitHub Issue](https://github.com/DannyCollinson/snaplog/issues).


## Thanks for checking out `snaplog`!
##
