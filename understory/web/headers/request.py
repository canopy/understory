"""

"""

# XXX import configparser
# XXX import os
import re

import httpagentparser
import mimeparse

from . import util

__all__ = [
    "Accept",
    "AcceptCharset",
    "AcceptEncoding",
    "AcceptLanguage",
    "Authorization",
    "Cookie",
    "Expect",
    "From",
    "Host",
    "IfMatch",
    "IfModifiedSince",
    "IfNoneMatch",
    "IfRange",
    "IfUnmodifiedSince",
    "KeepAlive",
    "MaxForwards",
    "ProxyAuthorization",
    "Range",
    "Referer",
    "TE",
    "UserAgent",
    "XBehavioralAdOptOut",
    "XDoNotTrack",
    "XForwardedFor",
    "XRequestedWith",
]


class Request(util.Header):

    """"""


class _Accept(Request):

    """"""

    def parse(self):
        acceptables = []
        noq = 1
        for acceptable in self.header.split(","):
            value, _, params = acceptable.strip().lower().partition(";")
            parameters = {}
            if params.strip():
                for param in params.split(";"):
                    k, _, v = param.partition("=")
                    parameters[k.strip()] = v.strip()
            noq -= 0.00001
            q = float(parameters.pop("q", noq))
            acceptables.append((q, (value.strip(), parameters)))
        self.acceptables = [
            self.type(a[0], _q, **a[1]) for _q, a in list(reversed(sorted(acceptables)))
        ]

    class _Acceptable:

        """"""

        def __init__(self, value, quality, **params):
            self.value = value.lower()
            self.quality = quality
            self.params = {k.lower(): v.lower() for k, v in params.items()}
            self.parse()

        def __repr__(self):
            return repr(self.value)


class Accept(_Accept):

    """
    The "Accept" request-header field can be used by user agents to specify
    response media types that are acceptable. Accept header fields can be
    used to indicate that the request is specifically limited to a small
    set of desired types, as in the case of a request for an in-line image.

        >>> header = '''text/*;q=0.3, text/html;q=0.7, text/html;level=1,
        ...             text/html;level=2;q=0.4, */*;q=0.5'''
        >>> accept = Accept(header)
        >>> accept.acceptables
        ['text/html', 'text/html', '*/*', 'text/html', 'text/*']
        >>> type(accept.acceptables[0])
        <class 'web.headers.request.Accept.Media'>

    # TODO >>> accept.best_match(["image/png", "text/plain", "text/html"])
    # TODO 'text/html'

    """

    def best_match(self, supported):
        return mimeparse.best_match(supported, self.header)

    class Media(_Accept._Acceptable):

        """"""

        def parse(self):
            self.canonical = self.value

    type = Media

    _meta = "TYPE"


class AcceptCharset(_Accept):

    """
    The "Accept-Charset" request-header field can be used by user agents
    to indicate what response character sets are acceptable. This field
    allows clients capable of understanding more comprehensive or
    special-purpose character sets to signal that capability to a server
    which is capable of representing documents in those character sets.

    """

    class Charset(_Accept._Acceptable):

        """"""

        def parse(self):
            self.canonical = self.value

    type = Charset

    _meta = "CHARSET"


class AcceptEncoding(_Accept):

    """"""

    # def best_match(self, supported):
    #   acceptable = [p.lower().strip() for p in self.header.split(",")]
    #   for encoding in supported:
    #     if encoding in acceptable:
    #       return encoding
    #   raise http.NotAcceptable("asdf")

    class Encoding(_Accept._Acceptable):

        """"""

        def parse(self):
            self.canonical = self.value

    type = Encoding

    _meta = "ENCODING"


class AcceptLanguage(_Accept):

    """"""

    class Language(_Accept._Acceptable):

        """"""

        def parse(self):
            self.canonical = self.value

    type = Language

    _meta = "LANGUAGE"


class Authorization(Request):

    """"""

    def __str__(self):
        return self.header.removeprefix("Bearer ")

    _meta = ""


class Cookie(Request):

    """"""

    def parse(self):
        self.morsels = {}
        for morsel in self.header.split(";"):
            k, _, v = morsel.lstrip().partition("=")
            self.morsels[k] = v

    def get(self, key, default=None):
        return self.morsels.get(key, default)


class Expect(Request):

    """"""


class From(Request):

    """"""


class Host(Request):

    """"""

    # TODO support for IP addresses and lazy determination

    def parse(self):
        self.header = self.header.lower()
        self.name, _, port = self.header.partition(":")
        if port is None:
            port = "80"
        self.port = port

    @property
    def is_hostname(self):
        """"""
        if len(self.name) > 255:
            return False
        allowed = re.compile(r"^(?!-)[a-z\d-]{1,63}(?<!-)$")  # TODO raw ok?
        return all(allowed.match(l) for l in self.name.strip(".").split("."))


class IfMatch(Request):

    """"""


class IfModifiedSince(Request):

    """"""


class IfNoneMatch(Request):

    """"""


class IfRange(Request):

    """"""


class IfUnmodifiedSince(Request):

    """"""


class KeepAlive(Request):

    """"""


class MaxForwards(Request):

    """"""


class ProxyAuthorization(Request):

    """"""


class Range(Request):

    """"""


class Referer(Request):

    """"""


class TE(Request):

    """"""


class UserAgent(Request):

    """"""

    def parse(self):
        self.features = httpagentparser.simple_detect(self.header)

    # _agents = {}
    # _re_agents = {}
    # _defaults = None

    # def parse(self):
    #     if not self._agents:
    #         self._initialize_browscap()
    #     possibles = list(name for pattern, name in self._re_agents.items()
    #                      if pattern.match(self.header))
    #     self.features = self._defaults
    #     if possibles:
    #         self.features = self._agents[max(possibles,
    #                                          key=lambda n: len(n))]

    # @property
    # def is_js_compatible(self):
    #     return self.features["javascript"] == "true"

    # @classmethod
    # def _initialize_browscap(cls, path=None):
    #     if path is None:
    #         path = cls._get_filename()
    #     browscap = configparser.ConfigParser()
    #     if not browscap.read(path):
    #         return
    #     browscap.remove_section("GJK_Browscap_Version")
    #     defaults = dict(browscap.items("DefaultProperties"))
    #     browscap.remove_section("DefaultProperties")
    #     browscap.remove_section("*")  # TODO fall back to default browser
    #     families = {}
    #     for sect in browscap.sections():
    #         if browscap.get(sect, "Parent") == "DefaultProperties":
    #             families[sect] = dict(defaults, **dict(browscap.items(sect)))
    #             browscap.remove_section(sect)
    #     for sect in browscap.sections():
    #         parent = browscap.get(sect, "Parent")
    #         cls._agents[sect] = dict(families[parent],
    #                                  **dict(browscap.items(sect)))
    #         pattern = sect
    #         for unsafe in "().-":
    #             pattern = pattern.replace(unsafe, "\\" + unsafe)
    #         pattern = pattern.replace("?", ".").replace("*", ".*?")
    #         cls._re_agents[re.compile(r"^" + pattern + r"$")] = sect
    #     cls._defaults = defaults

    # @staticmethod
    # def _get_filename():
    #     return os.path.join(os.path.dirname(__file__), "browscap.ini")

    # @staticmethod
    # def _update_browscap():
    #     import httplib2
    #     agent = httplib2.Http()
    #     print("Updating browscap file..")

    #     uri = "http://browsers.garykeith.com/stream.asp?BrowsCapINI"
    #     print("Downloading from:", uri)
    #     content = agent.request(uri)[1]

    #     path = UserAgent._get_filename()
    #     print("Saving to:", path)
    #     with open(path, "w") as file:
    #         file.write(content)

    #     print("Success.")


# XXX UserAgent._initialize_browscap()


class XBehavioralAdOptOut(Request):

    """"""

    def __repr__(self):
        return repr(bool(self.header))


class XDoNotTrack(Request):

    """"""

    def __repr__(self):
        return repr(bool(self.header))


class XForwardedFor(Request):

    """"""


class XRequestedWith(Request):

    """"""

    @property
    def ajax(self):
        return self.header == "XMLHttpRequest"

    def __repr__(self):
        return repr(self.header)
