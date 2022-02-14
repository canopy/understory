"""."""

import datetime
import json
import pathlib
import re
import time

import lxml.html
import microformats as mf
import pyscreenshot
import pyvirtualdisplay
import requests
import selenium
from requests.exceptions import ConnectionError, SSLError
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from understory import solarized, sql, uri, web

__all__ = [
    "post",
    "get",
    "put",
    "delete",
    "parse",
    "browser",
    "firefox",
    "cache",
    "discover_link",
    "download",
    "ConnectionError",
    "SSLError",
]

displays = []
browsers = []

tor_proxies = {"http": "socks5h://localhost:9150", "https": "socks5h://localhost:9150"}


def discover_link(target, name):
    """
    Fetch target and discover link `name` in HTML rels or HTTP Link header.

    Skip HEAD request; use GET and attempt to cache.

    """
    try:
        _, response = web.tx.cache[target]
    except AttributeError:
        response = get(target)
    try:
        link = _get_header_link(response.headers, name)[0]
        if link.startswith("/"):
            endpoint = uri.parse(target)
            endpoint.path = link
        else:
            endpoint = uri.parse(link)
    except IndexError:
        try:
            endpoint = uri.parse(response.mf2json["rels"].get(name, [])[0])
        except IndexError:
            endpoint = None
    return endpoint


def _get_header_link(headers: dict, search_rel: str):
    try:
        header = headers["Link"]
    except KeyError:
        return []
    links = []
    for link in header.split(","):
        resource, _, rel = link.partition(";")
        match = re.match("""rel=['"](.+)['"]""", rel.strip())
        if match and match.groups()[0] == search_rel:
            links.append(resource.strip(" <>"))
    return links


def download(url, filepath, chunk_size=1024):
    """Download url to filepath."""
    response = request("GET", url, stream=True)
    with pathlib.Path(filepath).open("wb") as fp:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                fp.write(chunk)
    return response


def request(method, url, session=None, **kwargs):
    """
    Return the response to dereferencing given `url` using given `method`.

    Attempts to use HTTPS when accessing non-onion domains. Proxies
    through Tor when accessing onion services. Optionally pass typical
    `requests.Request` arguments as `kwargs`.

    """
    url = uri.parse(url)
    preferred = "https"
    if url.suffix == "onion":
        kwargs["proxies"] = tor_proxies
        preferred = "http"
    context = session if session else requests
    # try:
    #     response = context.request(
    #         method, f"{preferred}://{url.minimized}", verify=False, **kwargs
    #     )
    # except (requests.exceptions.SSLError, requests.exceptions.ConnectionError):
    #     if url.suffix != "onion":
    #         try:
    response = context.request(method, url, **kwargs)
    #         except (requests.exceptions.SSLError, requests.exceptions.ConnectionError):
    #             raise RequestFailed()
    return response


class RequestFailed(Exception):
    """A request has failed."""


def post(url, **kwargs):
    """Post to the web."""
    return Transaction(url, "post", **kwargs)


def get(url, **kwargs):
    """Get from the web."""
    return Transaction(url, "get", **kwargs)


def put(url, **kwargs):
    """Put to the web."""
    return Transaction(url, "put", **kwargs)


def delete(url, **kwargs):
    """Delete from the web."""
    return Transaction(url, "delete", **kwargs)


class Cache:
    """A dictionary-like cache of the web."""

    model = sql.model(
        "WebCache",
        resources={
            "origin": "TEXT",
            "path": "TEXT",
            "data": "JSON",
            "headers": "JSON",
            "title": "TEXT",
            "html": "TEXT",
            "UNIQUE": "(origin, path)",
        },
        search={
            "origin": "",
            "path": "",
            "text": "",
            "FTS": True,
        },
    )

    def __init__(self, origin=None, db=None):
        self.origin = origin
        if not db:
            db = sql.db("cache.db", self.model)
        self.db = db

    def add(self, url):
        url = self._make_url(url)
        resource = get(url)
        try:
            title = resource.dom.select("title")[0].text
        except IndexError:
            title = None
        try:
            self.db.insert(
                "resources",
                origin=url.origin,
                path=url.path,
                data=resource.mf2json.data,
                headers=dict(resource.headers),
                title=title,
                html=resource.text,
            )
            self.db.insert(
                "search",
                origin=url.origin,
                path=url.path,
                text=str(resource.mf2json.data),
            )
        except self.db.IntegrityError:
            self.db.update(
                "resources",
                data=resource.mf2json.data,
                headers=dict(resource.headers),
                title=title,
                html=resource.text,
                where="origin = ? AND path = ?",
                vals=[url.origin, url.path],
            )
            self.db.update(
                "search",
                origin=url.origin,
                path=url.path,
                text=str(resource.mf2json.data),
                where="origin = ? AND path = ?",
                vals=[url.origin, url.path],
            )
        return url, resource

    def search(self, query):
        return self.db.select(
            "search AS s",
            what="r.*, s.text",
            where="search MATCH ?",
            vals=[query],
            join="resources AS r ON r.origin = s.origin AND r.path = s.path",
            order="rank",
        )

    @property
    def domains(self):
        return [
            (uri.parse(r["origin"]), r["data"])
            for r in self.db.select(
                "resources", what="origin, data", order="origin ASC", group="origin"
            )
        ]

    def forget_domain(self, domain):
        return self.db.delete(
            "resources",
            where="origin = ? OR origin = ?",
            vals=[f"https://{domain}", f"http://{domain}"],
        )

    def get_pages(self, domain):
        return self.db.select(
            "resources",
            where="origin = ? OR origin = ?",
            vals=[f"https://{domain}", f"http://{domain}"],
            order="path ASC",
        )

    # XXX @property
    # XXX def graph(self):
    # XXX     network = nx.DiGraph()
    # XXX     for url, resource in self.cache.items():  # TODO iterate over db items
    # XXX         # print(resource.links)
    # XXX         network.add_node(url)
    # XXX     return nx.draw(network, with_labels=True)

    def _make_url(self, url):
        if self.origin:
            url = f"{self.origin}/{url}"
        return uri.parse(url)

    def __getitem__(self, resource_url):
        try:
            url = self._make_url(resource_url)
            resource_data = self.db.select(
                "resources",
                where="origin = ? AND path = ?",
                vals=[url.origin, url.path],
            )[0]
            resource = Transaction(url, fetch=False)
            resource.headers = resource_data["headers"]  # TODO case-insen
            resource.text = resource_data["html"]
        except (AttributeError, IndexError):
            url, resource = self.add(resource_url)
        return url, resource


cache = Cache


class Transaction:
    """."""

    def __init__(
        self, url, method="get", fetch=True, session=None, headers=None, **kwargs
    ):
        self.url = str(url)
        if fetch:
            # XXX handler = getattr(requests, method)
            # XXX self.response = handler(apply_dns(self.url), **kwargs)
            _headers = {
                "accept": "text/html;q=0.9,*/*;q=0.8",
                "user-agent": (
                    "Mozilla/5.0 (X11; Linux x86_64; rv:92.0) "
                    "Gecko/20100101 Firefox/92.0"
                ),
            }
            if headers:
                _headers.update(headers)
            self.response = request(
                method, self.url, session=session, headers=_headers, **kwargs
            )
            self.status = self.response.status_code
            self.text = self.response.text
            self.headers = self.response.headers

    @property
    def location(self):
        location = self.headers["location"]
        if location.startswith("/"):
            new_url = uri.parse(self.response.url)
            new_url.path = location
            location = str(new_url)
        return location

    @property
    def links(self):
        return self.response.links

    @property
    def dom(self):
        return parse(self.text)

    @property
    def json(self):
        return json.loads(self.text)

    @property
    def mf2json(self):
        return Semantics(mf.parse(str(self.text), self.url))

    @property
    def card(self):
        return Semantics(mf.representative_card(self.mf2json.data, source_url=self.url))

    @property
    def feed(self):
        return Semantics(mf.interpret_feed(self.mf2json.data, source_url=self.url))

    @property
    def entry(self):
        return Semantics(mf.interpret_entry(self.mf2json.data, source_url=self.url))

    @property
    def event(self):
        return Semantics(mf.interpret_event(self.mf2json.data, source_url=self.url))

    def mention(self, *target_urls):
        return Semantics(mf.interpret_comment(self.mf2json.data, self.url, target_urls))

    # @property
    # def jf2(self):
    #     return Semantics(mf.interpret_feed(self.mf2json.data,
    #                                        source_url=self.url))


class Semantics:
    def __init__(self, data):
        self.data = data

    def __getitem__(self, item):
        return self.data[item]

    def __repr__(self):
        return JSONEncoder(indent=2).encode(self.data)  # , indent=2)
        # XXX return json.dumps(self.data, indent=2)

    def _repr_html_(self):
        return solarized.highlight(JSONEncoder(indent=2).encode(self.data), ".json")
        # XXX return solarized.highlight(json.dumps(self.data, indent=2),
        # ".json")

    def __bool__(self):
        return bool(self.data)


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uri.URI):
            return str(obj)
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


def parse(html):
    """Return a document object for given html."""
    return Document(html)


# XXX def apply_dns(url):
# XXX     if url.startswith("/"):
# XXX         return url
# XXX     url = uri.parse(url)
# XXX     if url.host == "alice.example":
# XXX         url = str(url).replace("http://alice.example", "http://127.0.0.1:8080")
# XXX     elif url.host == "bob.example":
# XXX         url = str(url).replace("http://bob.example", "http://127.0.0.1:8081")
# XXX     elif url.host == "hello.example":
# XXX         url = str(url).replace("http://hello.example", "http://127.0.0.1:8082")
# XXX     else:
# XXX         url = str(url)
# XXX     return url


# XXX def unapply_dns(url):
# XXX     url = uri.parse(url)
# XXX     if url.host == "127.0.0.1":
# XXX         if url.port == 8080:
# XXX             url = str(url).replace("http://127.0.0.1:8080", "http://alice.example")
# XXX         elif url.port == 8081:
# XXX             url = str(url).replace("http://127.0.0.1:8081", "http://bob.example")
# XXX         elif url.port == 8082:
# XXX             url = str(url).replace("http://127.0.0.1:8082", "http://hello.example")
# XXX     else:
# XXX         url = str(url)
# XXX     return url


class Document:

    # TODO with html as dom: -- manipulate dom -- on exit html is modified

    def __init__(self, html):
        self.doc = lxml.html.fromstring(str(html))

    def select(self, selector):
        els = []
        for el in self.doc.cssselect(selector):
            els.append(Element(el))
        return els

    @property
    def children(self):
        return self.doc.getchildren()

    @property
    def html(self):
        return lxml.html.tostring(self.doc).decode()


class Element:
    def __init__(self, element):
        self.element = element

    def append(self, *html):
        for _html in html:
            self.element.append(_make_element(_html))

    def select(self, selector):
        els = []
        for el in self.element.cssselect(selector):
            els.append(Element(el))
        return els

    def replace(self, html):
        self.element.getparent().replace(self.element, _make_element(html))

    @property
    def href(self):
        try:
            return self.element.attrib["href"]
        except KeyError:
            raise AttributeError("href")

    @property
    def text(self):
        return self.element.text_content()


def _make_element(html):
    el = lxml.html.fromstring(f"<DOUGIE>{html}</DOUGIE>")
    return el.cssselect("DOUGIE")[0].getchildren()[0]


class Browser:
    """"""

    def __init__(self, apps=None):
        self.session = requests.Session()

    def get(self, url, **kwargs):
        return Transaction(url, "GET", session=self.session, **kwargs)

    def post(self, url, **kwargs):
        return Transaction(url, "POST", session=self.session, **kwargs)


browser = Browser


class Firefox:
    """Firefox via Selenium."""

    By = By
    EC = expected_conditions

    def __init__(self, name=None, width=1024, height=768):
        if not len(displays):
            display = pyvirtualdisplay.Display(visible=False, size=(2048, 768))
            display.start()
            displays.append(display)
        profile = webdriver.FirefoxProfile()
        # profile.add_extension(
        #     extension="/home/gaea/canopy/var/identities/"
        #     "6c189616-4fe1-4f3f-84dc-c4a13ee9b155/"
        #     "asteria/asteria-dev.xpi"
        # )
        binary = "/home/gaea/firefox/firefox-bin"
        self.browser = webdriver.Firefox(firefox_profile=profile, firefox_binary=binary)
        count = len(browsers)
        browsers.append(self)
        self._top = 0
        self._left = count * 1024
        self._width = width
        self._height = height
        self._update_window()
        self.name = name
        self.shot_id = 0

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._width = value
        self._update_window()

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._height = value
        self._update_window()

    def _update_window(self):
        self.browser.set_window_rect(self._left, self._top, self._width, self._height)

    def go(self, *args, wait=0):
        if len(args) == 1:
            url = args[0]
        elif len(args) == 2:
            url = "/".join(args)
        # XXX url = apply_dns(url)
        self.browser.get(url)
        if wait:
            time.sleep(wait)
        return self
        # XXX self.browser.get(str(uri.parse(url)))

    def wait(self, *conditions, duration=20):
        for condition in conditions:
            time.sleep(0.1)
            wait = WebDriverWait(self.browser, duration)
            wait.until(condition)

    def wait_until_url_contains(self, url):
        # XXX self.wait(self.EC.url_contains(apply_dns(url)))
        self.wait(self.EC.url_contains(url))

    def select(self, selector):
        return self.browser.find_elements_by_css_selector(selector)

    def select_first(self, selector):
        return self.browser.find_element_by_css_selector(selector)

    def action(self):
        return ActionChains(self.browser)

    def shot(self, path):
        # TODO take in pieces & stitch together -- using way too much memory
        # self._height = self.browser.execute_script("return document.body."
        #                                            "scrollHeight;") + 100
        # self._update_window()
        self.browser.get_screenshot_as_file(str(path) + ".png")

    # XXX def shot_url(self):
    # XXX     base64 = self.browser.get_screenshot_as_base64()
    # XXX     return f"data:image/png;BASE64,{base64}"

    def shot_url(self):
        # XXX grab = pyscreenshot.grab(bbox=(0, 0, 920, 920)).tobytes()
        # XXX base64png = b"".join(base64.encodebytes(grab).splitlines())
        self.shot_id += 1
        filename = f"{self.name}-{self.shot_id}.png"
        placement = browsers.index(self)
        coords = (1024 * placement, 0, 1024 * (placement + 1), 768)
        # import sh
        # sh.Command("import")("-screen", "-window", "root", filename)
        # time.sleep(2)
        # sh.Command("import")("-window", "root", filename)
        # sh.convert(sh.xwd("-root", "-screen"), "xwd:-", f"png:{filename}")
        pyscreenshot.grab(bbox=coords).save(filename)
        return f"/IndieWeb/{filename}"

    def quit(self):
        try:
            self.browser.quit()
        except selenium.common.exceptions.WebDriverException:
            pass
        if displays:
            try:
                displays[0].stop()
            except KeyError:  # raising during multi-user testing
                pass

    def __getattr__(self, attr):
        return getattr(self.browser, attr)

    def _repr_html_(self):
        return f"<img class=screen src={self.shot_url()}>"
        # url = unapply_dns(self.current_url)
        # site_character = url.partition("//")[2].partition(".")[0]
        # TODO FIXME remove hard-coded IndieWeb..
        # return (f"<div class=screenshot>"
        #         f"<div class=browser><small>{self.name}'s "
        #         f"Browser</small></div>"
        #         f"<div class=tab><img src=/IndieWeb/{site_character}16.png>"
        #         f" {self.title}</div>"
        #         f"<div class=address><small><code>{url}</code></small></div>"
        #         f"<img class=screen src={self.shot_url()}></div>")


firefox = Firefox


# def shot(name, description):  # XXX , *browsers):
#     test_case = inspect.stack()[1].function
#     global shot_counter
#     shot_id = "{:03}".format(shot_counter)
#     dashed_name = name.replace(" ", "-")
#     for user, browser in sorted(browsers.items()):
#         shot_filename = "{}-{}-{}.png".format(shot_id, user, dashed_name)
#         height = browser.execute_script("return document.body.scrollHeight;")
#         browser.set_window_size(browser_width, height + 100)
#         browser.get_screenshot_as_file(str(build_dir / "features" /
#                                            shot_filename))
#     features.append((test_case, shot_id, dashed_name, name, description))
#     # XXX , shot_filename, [user for u in browsers.keys()]))
#     shot_counter += 1
