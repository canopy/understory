"""

"""

from .util import Status

__all__ = ["Informational", "Continue", "SwitchingProtocols"]


class Informational(Status):

    """1xx -- request received, continuing process"""


class Continue(Informational):

    """
    100 [Part II S 8.1.1][0]

    The client SHOULD continue with its request.This interim response is
    used to inform the client that the initial part of the request has
    been received and has not yet been rejected by the server. The client
    SHOULD continue by sending the remainder of the request or, if the
    request has already been completed, ignore this response. The server
    MUST send a final response after the request has been completed. See
    Section 7.2.3 of [Part1] for detailed discussion of the use and
    handling of this status code.

    [0]: http://tools.ietf.org/html/httpbis-p2-semantics#section-8.1.1

    """


class SwitchingProtocols(Informational):

    """101"""
