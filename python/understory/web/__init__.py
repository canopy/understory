"""
Tools for a metamodern web environment.

## User agent tools

Simple interface, simple automate.

## Web application framework

Simple interface, simple deploy.

"""

from dns import resolver as dns
from understory.mkdn import render as mkdn
from understory.mm import template, templates
from understory.uri import parse as uri

from .agent import *  # noqa
from .braid import *  # noqa
from .framework import *  # noqa
from .response import Status  # noqa
from .response import (OK, Accepted, BadRequest, Conflict, Created, Forbidden,
                       Found, Gone, MethodNotAllowed, MultiStatus, NoContent,
                       NotFound, PermanentRedirect, SeeOther, Unauthorized)

__all__ = [
    "dns",
    "mkdn",
    "template",
    "templates",
    "uri",
    "OK",  # responses
    "Accepted",
    "BadRequest",
    "Conflict",
    "Created",
    "Forbidden",
    "Found",
    "Gone",
    "MethodNotAllowed",
    "MultiStatus",
    "NoContent",
    "NotFound",
    "PermanentRedirect",
    "SeeOther",
    "Unauthorized",
]
