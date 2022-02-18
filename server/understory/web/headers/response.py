"""

"""

# TODO class ContentDisposition(Response):  # has httpbis spec w/ ad-hoc doc

from . import util

__all__ = [
    "AcceptRanges",
    "Age",
    "Etag",
    "Location",
    "ProxyAuthenticate",
    "RetryAfter",
    "SetCookie",
    "Server",
    "Vary",
    "WWWAuthenticate",
    "XPoweredBy",
]


class Response(util.Header):

    """"""


class AcceptRanges(Response):

    """"""


class Age(Response):

    """"""


class Etag(Response):

    """"""


class Location(Response):

    """"""


class ProxyAuthenticate(Response):

    """"""


class RetryAfter(Response):

    """"""


class SetCookie(Response):

    """"""

    def __init__(self, header):
        self.cookie = header

    def update(self, *args, **kwargs):
        print("!! GOT HERE (SET-COOKIE)")
        self.cookie.update(*args, **kwargs)

    @property
    def header(self):
        return "; ".join(
            m if m in ("Secure", "HttpOnly") else f"{m[0]}={m[1]}" for m in self.cookie
        )


class Server(Response):

    """"""


class Vary(Response):

    """"""


class WWWAuthenticate(Response):

    """"""


class XPoweredBy(Response):

    """"""
