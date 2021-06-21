"""Mountable IndieWeb apps and helper functions."""

import pathlib

from understory import mm, web
from understory.web import framework as fw
from understory.web import tx

from . import indieauth, micropub, microsub, webmention, websub

__all__ = [
    "indieauth",
    "micropub",
    "microsub",
    "webmention",
    "websub",
    "content",
    "cache",
]


content = fw.application(
    "Content",
    db=False,
    year=r"\d{4}",
    month=r"\d{2}",
    day=r"\d{2}",
    post=web.nb60_re + r"{,4}",
    slug=r"[\w_-]+",
)
cache = fw.application("Cache", db=False, mount_prefix="admin/cache", resource=r".+")
templates = mm.templates(__name__)


@content.route(r"")
class Homepage:
    def get(self):
        return templates.content.homepage(indieauth.get_owner(), [])


@content.route(r"understory.js")
class UnderstoryJS:
    def get(self):
        web.header("Content-Type", "application/javascript")
        with (pathlib.Path(__file__).parent / "understory.js").open() as fp:
            return fp.read()


@content.route(r"{year}/{month}/{day}/{post}(/{slug})?")
class Permalink:
    """An individual entry."""

    def get(self):
        resource = tx.pub.read(tx.request.uri.path)["resource"]
        if resource["visibility"] == "private" and not tx.user.session:
            raise web.Unauthorized(f"/auth?return_to={tx.request.uri.path}")
        # mentions = web.indie.webmention.get_mentions(str(tx.request.uri))
        return templates.content.entry(resource)  # , mentions)


@cache.route(r"")
class Cache:
    def get(self):
        return templates.cache.index(fw.tx.db.select("cache"))


@cache.route(r"{resource}")
class Resource:
    def get(self):
        resource = fw.tx.db.select(
            "cache",
            where="url = ? OR url = ?",
            vals=[f"https://{self.resource}", f"http://{self.resource}"],
        )[0]
        return templates.cache.resource(resource)
