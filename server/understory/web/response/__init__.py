"""

"""

import inspect

from ..headers import Headers
from . import clienterror, informational, redirection, servererror, success
from .clienterror import *  # noqa
from .informational import *  # noqa
from .redirection import *  # noqa
from .servererror import *  # noqa
from .success import *  # noqa
from .util import Status

__all__ = ["Status"] + (
    informational.__all__
    + success.__all__
    + redirection.__all__
    + clienterror.__all__
    + servererror.__all__
)


def parse(response):
    """
    return status, headers and body after parsing given response

    """
    lines = iter(response.splitlines())
    status = parse_status(next(lines))
    headers = Headers.from_lines(lines)
    return status, headers, "\n".join(lines)


def parse_status(line):
    """
    return a parsed

        >>> parse_status("HTTP/1.1 200 OK")
        ('1.1', <class 'web.response.success.OK'>)

    """
    raw_version, _, raw_status = line.partition(" ")
    version = raw_version.partition("/")[2]
    status = get_status(raw_status.partition(" ")[0])
    return version, status


def get_status(code):
    """
    return a `Status` object for given status `code`

    """
    if inspect.isclass(code) and issubclass(code, Status):
        return code
    code = int(code)
    for name, obj in globals().items():
        if not inspect.isclass(obj) or not issubclass(obj, Status):
            continue
        try:
            if code == int(inspect.getdoc(obj).rstrip(".").partition(" ")[0]):
                return obj
        except ValueError:
            continue
    raise KeyError("cannot find a `Status` object for code {}".format(code))
