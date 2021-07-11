"""
HTTP headers

"""

from . import entity, general, request, response

__all__ = ["get_header", "Headers"]


def get_header(header, value=None):
    """ """
    header = header.lower().replace("_", "").replace("-", "")
    for header_type in (entity, general, request, response):
        for search_name in header_type.__all__:
            if search_name.lower() == header:
                return getattr(header_type, search_name)(value)
    return value


def _title_case(header):
    """

    >>> _title_case("accept_Encoding")
    'Accept-Encoding'

    """
    # TODO re.split on -, _, whitespace, or camelcase
    return "-".join(part.capitalize() for part in header.split("_"))


class Headers(dict):

    """
    a dot-mapping optimized to hold HTTP header objects

        >>> h = Headers(**{"content_type": "text/plain", "CONTENT-LENGTH": "555"})
        >>> h["content-type"]
        text/plain
        >>> h["content-length"]
        555
        >>> h.content_type
        text/plain
        >>> type(h.content_type)
        <class 'web.headers.entity.ContentType'>

    """

    def __init__(self, **headers):
        for header, value in headers.items():
            self[header] = value

    @classmethod
    def from_lines(cls, lines):
        """
        return a `Headers` object based upon iterable of `header` strings

            >>> header_lines = '''
            ... Date: Mon, 27 Jul 2009 12:28:53 GMT
            ... Server: Apache
            ... Last-Modified: Wed, 22 Jul 2009 19:15:56 GMT
            ... ETag: "34aa387-d-1568eb00"
            ... Accept-Ranges: bytes
            ... Content-Length: 14
            ... Vary: Accept-Encoding
            ... Content-Type: text/plain
            ...
            ... '''
            >>> headers = Headers.from_lines(header_lines)

        """
        headers = cls()
        for line in lines.splitlines():
            name, _, value = (part.strip() for part in line.partition(":"))
            headers[name] = value
        return headers

    # @property
    # def request(self):
    #     headers = {}
    #     for k, v in self.__dict__.items():
    #         if issubclass(v.__class__, (Request, Entity, General)):
    #             headers[_title_case(k)] = str(v)
    #     return headers

    @property
    def response(self):
        # FIXME Set-Cookie broke this function
        headers = {}
        for k, v in self.__dict__.items():
            # if v.__class__.__name__ in ["SetCookie"]:
            #     headers[_title_case(k)] = v.header
            if issubclass(
                v.__class__, (response.Response, entity.Entity, general.General)
            ):
                headers[_title_case(k)] = str(v)
        return headers

    @property
    def wsgi(self):
        headers = []
        for name, value in self.__dict__.items():
            name = _title_case(name)
            # XXX if name in ["Set-Cookie"]:
            # XXX     headers.extend((name, val) for val in value.header)
            # XXX else:
            if isinstance(value, list):
                for item in value:
                    headers.append((name, str(item)))
            else:
                headers.append((name, str(value)))
        return headers

    def get(self, header, default=None):
        return getattr(self, header, default)

    def __getitem__(self, header):
        header = header.lower().replace("_", "-")
        return super(Headers, self).__getitem__(header)

    def __setitem__(self, header, value):
        header = header.lower().replace("_", "-")
        obj = get_header(header, value)
        self.__dict__[header] = obj
        super(Headers, self).__setitem__(header, obj)

    def __getattr__(self, header):
        try:
            return self[header]
        except KeyError:
            raise AttributeError(header)

    def __setattr__(self, header, value):
        self[header] = value

    def __contains__(self, header):
        header = header.lower().replace("_", "-")
        return header in self.__dict__

    # def __repr__(self):
    #     return repr({_title_case(k): v for k, v in sorted(self.items())})
