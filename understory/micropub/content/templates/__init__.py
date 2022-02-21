from pprint import pformat

import pendulum
from understory import micropub, web
from understory.mf import discover_post_type
from understory.micropub.readability import Readability
from understory.web import tx

__all__ = [
    "discover_post_type",
    "pformat",
    "pendulum",
    "tx",
    "post_mkdn",
    "Readability",
]


def post_mkdn(content):
    return web.mkdn(content, globals=micropub.markdown_globals)
