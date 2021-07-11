"""
Tools for a metamodern web environment.

## User agent tools

Simple interface, simple automate.

## Web application framework

Simple interface, simple deploy.

"""

import pendulum
from dns import resolver as dns
from hstspreload import in_hsts_preload
from requests.exceptions import ConnectionError

from understory import mf, mm
from understory.mkdn import render as mkdn
from understory.mm import Template as template  # noqa
from understory.mm import templates  # noqa
from understory.uri import parse as uri

from . import agent, braid, framework
from .agent import *  # noqa
from .braid import *  # noqa
from .framework import *  # noqa
from .response import Status  # noqa
from .response import (OK, Accepted, BadRequest, Conflict, Created, Forbidden,
                       Found, Gone, MethodNotAllowed, MultiStatus, NoContent,
                       NotFound, PermanentRedirect, SeeOther, Unauthorized)

# from .tasks import run_queue


__all__ = [
    "dns",
    "in_hsts_preload",
    "mf",
    "mkdn",
    "mm",
    "template",
    "templates",
    "pendulum",
    "indieauth",
    "micropub",
    "microsub",
    "webmention",
    "websub",
    "run_queue",
    "uri",
    "Created",
    "ConnectionError",
]
__all__ += agent.__all__ + braid.__all__ + framework.__all__  # noqa
