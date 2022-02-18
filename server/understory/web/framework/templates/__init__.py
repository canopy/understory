"""Configuration and error templates."""

import inspect
from pprint import pformat

from understory.solarized import highlight
from understory.web.framework.util import tx

__all__ = ["inspect", "pformat", "highlight", "tx", "getsourcelines"]


def getsourcelines(obj):
    """Return number of lines of source used to implement obj."""
    try:
        return inspect.getsourcelines(obj)
    except IOError:
        return "", 0
