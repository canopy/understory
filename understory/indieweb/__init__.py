"""Mountable IndieWeb apps and helper functions."""

import pathlib

from understory import kv, mm, sql, web
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
people = fw.application("People", db=False, mount_prefix="people")
cache = fw.application("Cache", db=False, mount_prefix="admin/cache", resource=r".+")
templates = mm.templates(__name__)


def site(name: str, host: str = None, port: int = None) -> web.Application:
    def set_data_sources(handler, app):
        host = tx.request.uri.host  # TODO FIXME check for filename safety!!
        db = sql.db(f"{host}.db")
        tx.host.db = db
        tx.host.cache = web.cache(db=db)
        tx.host.kv = kv.db(host, ":", {"jobs": "list"})
        yield
        # TODO XXX if tx.request.uri.path == "" and tx.response.body:
        # TODO XXX     doc = web.parse(tx.response.body)
        # TODO XXX     try:
        # TODO XXX         head = doc.select("head")[0]
        # TODO XXX     except IndexError:
        # TODO XXX         tx.response.body = (
        # TODO XXX             f"<!doctype html><head></head>"
        # TODO XXX             f"<body>{tx.response.body}</body></html>"
        # TODO XXX         )

    return web.application(
        name,
        host=host,
        port=port,
        mounts=(
            web.framework.data_app,
            web.framework.debug_app,
            indieauth.server.profile,
            indieauth.server.app,
            indieauth.client.app,
            micropub.server,
            micropub.text_client,
            webmention.receiver,
            people,
            content,
        ),
        wrappers=(
            set_data_sources,
            web.resume_session,
            indieauth.server.wrap,
            indieauth.client.wrap,
            micropub.wrap_server,
            webmention.wrap_receiver,
        ),
    )


@people.route(r"")
class People:
    def get(self):
        return templates.people.index(
            indieauth.server.get_clients(), indieauth.client.get_users()
        )


@content.route(r"")
class Homepage:
    def get(self):
        return templates.content.homepage(indieauth.server.get_owner(), [])


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
    """"""

    resource = None

    def get(self):
        resource = fw.tx.db.select(
            "cache",
            where="url = ? OR url = ?",
            vals=[f"https://{self.resource}", f"http://{self.resource}"],
        )[0]
        return templates.cache.resource(resource)
