"""

"""

from .util import Status

__all__ = [
    "ClientError",
    "BadRequest",
    "Unauthorized",
    "PaymentRequired",
    "Forbidden",
    "NotFound",
    "MethodNotAllowed",
    "NotAcceptable",
    "ProxyAuthenticationRequired",
    "RequestTimeout",
    "Conflict",
    "Gone",
    "LengthRequired",
    "PreconditionFailed",
    "RequestEntityTooLarge",
    "RequestURITooLong",
    "UnsupportedMediaType",
    "RequestedRangeNotSatisfiable",
    "ExpectationFailed",
    "PeaceLoveUnityRespect",
    "UpgradeRequired",
    "PreconditionRequired",
    "TooManyRequests",
    "RequestHeaderFieldsTooLarge",
    "NoResponse",
    "UnavailableForLegalReasons",
    "ClientClosedRequest",
]


class ClientError(Status):

    """4xx -- the request contains bad syntax or cannot be fulfilled"""


class BadRequest(ClientError):

    """
    400

    """


class Unauthorized(ClientError):

    """
    401

    """


class PaymentRequired(ClientError):

    """
    402

    """


class Forbidden(ClientError):

    """
    403

    """


class NotFound(ClientError):

    """
    404

    """


class MethodNotAllowed(ClientError):

    """
    405

    """


class NotAcceptable(ClientError):

    """
    406

    """


class ProxyAuthenticationRequired(ClientError):

    """
    407

    """


class RequestTimeout(ClientError):

    """
    408

    """


class Conflict(ClientError):

    """
    409

    """


class Gone(ClientError):

    """
    410

    """


class LengthRequired(ClientError):

    """
    411

    """


class PreconditionFailed(ClientError):

    """
    412

    """


class RequestEntityTooLarge(ClientError):

    """
    413

    """


class RequestURITooLong(ClientError):

    """
    414

    """


class UnsupportedMediaType(ClientError):

    """
    415

    """


class RequestedRangeNotSatisfiable(ClientError):

    """
    416

    """


class ExpectationFailed(ClientError):

    """
    417

    """


class PeaceLoveUnityRespect(ClientError):

    """
    420

    """


class UpgradeRequired(ClientError):

    """
    426

    """


class PreconditionRequired(ClientError):

    """
    428

    """


class TooManyRequests(ClientError):

    """
    429

    """


class RequestHeaderFieldsTooLarge(ClientError):

    """
    431

    """


class NoResponse(ClientError):

    """
    444

    """


class UnavailableForLegalReasons(ClientError):

    """
    451

    """


class ClientClosedRequest(ClientError):

    """
    499

    """
