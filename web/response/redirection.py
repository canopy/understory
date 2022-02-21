"""

"""

from .util import Status

__all__ = [
    "Redirection",
    "MultipleChoices",
    "MovedPermanently",
    "Found",
    "SeeOther",
    "NotModified",
    "UseProxy",
    "TemporaryRedirect",
    "PermanentRedirect",
]


class Redirection(Status):

    """3xx -- further action must be taken in order to complete the request"""


class MultipleChoices(Redirection):

    """
    300

    """


class MovedPermanently(Redirection):

    """
    301

    """


class Found(Redirection):

    """
    302

    """


class SeeOther(Redirection):

    """
    303

    """


class NotModified(Redirection):

    """
    304

    """


class UseProxy(Redirection):

    """
    305

    """


class SwitchProxy(Redirection):

    """
    306 *DEPRECATED*

    """


class TemporaryRedirect(Redirection):

    """
    307

    """


class PermanentRedirect(Redirection):

    """
    308

    """
