"""HTTP Success Responses (2xx)."""

from .util import Status

__all__ = [
    "Success",
    "OK",
    "Created",
    "Accepted",
    "NonAuthoritativeInformation",
    "NoContent",
    "ResetContent",
    "PartialContent",
    "MultiStatus",
    "Subscription",
]


class Success(Status):
    """The action was successfully received, understood, & accepted."""


class OK(Success):
    """200."""

    def __init__(self, body):
        """
        Pass the body unchanged.

        Use `raise OK(foo)` to explicitly end the transaction from anywhere.
        Otherwise just use `return foo` in controllers (eg. _get, _post, ..).

        """
        super(Success, self).__init__(body)


class Created(Success):
    """201."""

    def __init__(self, body, location):
        """Add a Location header for location."""
        # TODO send the actual header here instead of in app.__call__()
        self.location = location
        super(Created, self).__init__(body)


class Accepted(Success):
    """202."""


class NonAuthoritativeInformation(Success):
    """203."""


class NoContent(Success):
    """204."""

    def __init__(self):
        """Return a body of None."""
        super(Success, self).__init__(None)


class ResetContent(Success):
    """205."""


class PartialContent(Success):
    """206."""


class MultiStatus(Success):
    """207."""


class Subscription(Success):
    """209 Braid Subscription."""
