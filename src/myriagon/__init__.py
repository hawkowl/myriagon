import sys

from ._version import __version__

if sys.version_info[:3] < (3, 4):
    raise SystemExit("Myriagon requires Python 3.4+.")


__all__ = ["__version__"]
