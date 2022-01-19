import inspect
from json import loads as load_json
from pprint import pformat

__all__ = ["load_json", "pformat", "get_doc"]


def get_doc(obj):
    """Return a two-tuple of object's first line and rest of docstring."""
    docstring = obj.__doc__
    if not docstring:
        return "", ""
    return inspect.cleandoc(docstring).partition("\n\n")[::2]
