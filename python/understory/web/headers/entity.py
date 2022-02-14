"""

"""

import calendar
import datetime
import email

from .util import Header

__all__ = [
    "Allow",
    "ContentEncoding",
    "ContentLanguage",
    "ContentLength",
    "ContentLocation",
    "ContentMD5",
    "ContentRange",
    "ContentType",
    "Expires",
    "LastModified",
]


def get_timestamp(dt, fmt="rfc822"):
    """
    return a string of datetime `dt` in common log format

        >>> get_timestamp(datetime.datetime(1970, 1, 1, 1, 1, 1))
        'Thu, 01 Jan 1970 01:01:01 GMT'

    """
    if dt is None:
        dt = datetime.UTC.localize(datetime.now())
    fmts = {"rfc822": "%a, %d %b %Y %H:%M:%S GMT", "ncsa": "%d/%b/%Y:%H:%M:%S %z"}
    return dt.strftime(fmts[fmt])


def parse_datetime(s):
    """
    parses a date/time stamp taken from an HTTP header

    """
    return datetime(*email.utils.parsedate(s)[:6])


class Entity(Header):

    """"""


class Allow(Entity):

    """"""


class ContentEncoding(Entity):

    """"""


class ContentLanguage(Entity):

    """"""


class ContentLength(Entity):

    """"""


class ContentLocation(Entity):

    """"""


class ContentMD5(Entity):

    """"""


class ContentRange(Entity):

    """"""


class ContentType(Entity):

    """"""

    @property
    def content_type(self):
        _content_type = str(self).partition(";")[0]
        if not _content_type:
            _content_type = "text/plain"
        return _content_type


class Expires(Entity):

    """
    formats an `Expires` header for `delta` from now

    `delta` is a `datetime.timedelta` object or a number of seconds.

    """

    def __init__(self, when):
        # FIXME either seconds a la TTL or datetime according to W3C
        now = datetime.datetime.utcnow()
        if isinstance(when, str):
            try:
                when = int(when)
            except ValueError:
                then = parse_datetime(when)
                when = calendar.timegm(then.utctimetuple()) - calendar.timegm(
                    now.utctimetuple()
                )
        if isinstance(when, int):
            when = datetime.timedelta(seconds=when)
        dt = now + when
        self.header = get_timestamp(dt=dt)


class LastModified(Entity):

    """"""

    # def __init__(self, when):
    #     self.header = util.format_datetime(when)
