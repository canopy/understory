"""."""

import datetime
import io
import json
import re
import time

import lxml.html
import networkx as nx
import pyscreenshot
import pyvirtualdisplay
import requests
import selenium
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from understory import mf, solarized, sql, uri, web

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
]

displays = []
browsers = []

tor_proxies = {"http": "socks5h://localhost:9050", "https": "socks5h://localhost:9050"}


def discover_link(target, name):
    """
    Fetch target and discover link `name` in HTML rels or HTTP Link header.

    Skip HEAD request; use GET and attempt to cache.

    """
    try:
        response = web.tx.cache[target]
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
    with filepath.open("wb") as fp:
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
    response = context.request(method, f"http://{url.minimized}", **kwargs)
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
    def __init__(self, domain=None, db=None):
        self.cache = {}
        if domain:
            self.domain = domain
        if db:
            self.db = db
        else:
            self.db = sql.db("cache.db")
        self.db.define(
            "cache", url="TEXT UNIQUE", html="TEXT", headers="JSON", data="JSON"
        )

    def format_url(self, url):
        try:
            url = f"{self.domain}/{url}"
        except AttributeError:
            url = url
        return url

    def add(self, url):
        url = self.format_url(url)
        resource = get(url)
        self.cache[url] = resource
        try:
            self.db.insert(
                "cache",
                url=url,
                html=resource.text,
                headers=dict(resource.headers),
                data=resource.mf2json.data,
            )
        except self.db.IntegrityError:
            self.db.update(
                "cache",
                html=resource.text,
                headers=dict(resource.headers),
                data=resource.mf2json.data,
                where="url = ?",
                vals=[url],
            )
        except AttributeError:
            pass
        return resource

    def __getitem__(self, resource_url):
        resource_url = str(resource_url)
        try:
            resource = self.cache[resource_url]
        except KeyError:
            try:
                url = self.format_url(resource_url)
                resource_data = self.db.select("cache", where="url = ?", vals=[url])[0]
                resource = Transaction(url, fetch=False)
                resource.headers = resource_data["headers"]  # TODO case-insen
                resource.text = resource_data["html"]
            except (AttributeError, IndexError):
                self.add(resource_url)
                resource = self.cache[resource_url]
        return resource

    @property
    def graph(self):
        network = nx.DiGraph()
        for url, resource in self.cache.items():
            # print(resource.links)
            network.add_node(url)
        return nx.draw(network, with_labels=True)


cache = Cache


class Transaction:
    """."""

    def __init__(self, url, method="get", fetch=True, session=None, **kwargs):
        self.url = str(uri.parse(str(url)))
        if fetch:
            # XXX handler = getattr(requests, method)
            # XXX self.response = handler(apply_dns(self.url), **kwargs)
            self.response = request(method, self.url, session=session, **kwargs)
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

    # TODO automatically add only if an: a or link
    @property
    def href(self):
        return self.element.attrib["href"]

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
        profile.add_extension(
            extension="/home/gaea/canopy/var/identities/"
            "6c189616-4fe1-4f3f-84dc-c4a13ee9b155/"
            "asteria/asteria-dev.xpi"
        )
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
