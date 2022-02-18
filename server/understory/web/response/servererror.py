"""

"""

from .util import Status

__all__ = ["ServerError", "InternalServerError", "NotImplemented", "ServiceUnavailable"]


class ServerError(Status):

    """5xx -- the server failed to fulfill an apparently valid request"""


class InternalServerError(ServerError):

    """
    500

    """


class NotImplemented(ServerError):

    """
    501

    """


class ServiceUnavailable(ServerError):

    """
    503

    """
