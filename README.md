# `sefkhet`

Sefkhet is a Python package that provides simple setup for complex logging.

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

## Notes

The package's name comes from the Egyptian goddess Seshat, who was alternatively known as Sefkhet-Abwy. According to [Wikipedia](https://en.wikipedia.org/wiki/Seshat):
> Seshat (Ancient Egyptian: 𓋇𓏏𓁐, lit. 'Female Scribe') was the ancient Egyptian goddess of writing, wisdom, and knowledge. She was seen as a scribe and record keeper. She was also credited with inventing writing. She became identified as the goddess of measurement, accounting, architecture, science, astronomy, mathematics, geometry, history and surveying.

She was typically depicted with a seven-pointed emblem above her head or on her headband, which also served as her emblem. This inspired the name Sefkhet-Abwy, which can be translated as "seven-horned".

The package's logo (𓏞) is the [hieroglyphic for "scribe's equipment"](https://en.wikipedia.org/wiki/Scribe_equipment_(hieroglyph)). It depicts a tube-like case to hold reeds to write with, a leather bag for storing inks, and a wooden scribal palette to mix inks on. It is sign Y3 on [Gardiner's sign list](https://en.wikipedia.org/wiki/Gardiner%27s_sign_list), and its codepoint is `0x133DE`.

## Thanks for checking out `sefkhet`!
###
