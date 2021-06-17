"""Mountable IndieWeb apps and helper functions."""

from understory import mm
from understory.web import framework as fw

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


content = fw.application("Content", db=False, resource=r".+")
cache = fw.application("Cache", db=False, mount_prefix="admin/cache", resource=r".+")
tmpl = mm.templates(__name__)


@content.route(r"")
class Homepage:
    def get(self):
        return tmpl.content.homepage(indieauth.get_owner(), [])


@cache.route(r"")
class Cache:
    def get(self):
        return tmpl.cache.index(fw.tx.db.select("cache"))


@cache.route(r"{resource}")
class Resource:
    def get(self):
        resource = fw.tx.db.select(
            "cache",
            where="url = ? OR url = ?",
            vals=[f"https://{self.resource}", f"http://{self.resource}"],
        )[0]
        return tmpl.cache.resource(resource)
