"""
[Microsub][0] server and client apps.

[0]: https://indieweb.org/Microsub-spec

"""

from understory import web
from understory.web import tx

from .. import websub


server = web.application("MicrosubServer", mount_prefix="sub", db=False)
templates = web.templates(__name__)


def wrap_server(handler, app):
    """Ensure server links are in head of root document."""
    tx.db.define(
        "following",
        feed_id="TEXT UNIQUE",
        url="TEXT",
        callback_url="TEXT",
        added="DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
    )
    tx.sub = LocalClient()
    yield
    if tx.request.uri.path == "" and tx.response.body:
        doc = web.parse(tx.response.body)
        try:
            head = doc.select("head")[0]
        except IndexError:
            pass
        else:
            head.append("<link rel=microsub href=/sub>")
            tx.response.body = doc.html
        web.header("Link", '</sub>; rel="microsub"', add=True)


class LocalClient:
    """."""

    def search(self, query):
        """
        Return a list of feeds associated with given query.

        If query is a URL, fetch it and look for feeds (inline and external).

        """
        # TODO Use canopy.garden for discovery.
        # TODO If query is a keyword, make suggestions.
        url = query
        if not url.startswith(("http://", "https://")):
            url = f"http://{url}"
        resource = tx.cache.add(url)
        feeds = []
        if resource.feed["entries"]:
            feed = {"type": "feed", "url": url, "name": "Unknown"}
            if resource.card:
                feed["name"] = resource.card["name"][0]
                try:
                    feed["photo"] = resource.card["photo"]
                except KeyError:
                    pass
            feeds.append(feed)
        for url in resource.mf2json["rels"].get("feed", []):
            feed = {"type": "feed", "url": url, "name": "Unknown"}
            subresource = tx.cache.add(url)
            if subresource.card:
                feed["name"] = subresource.card["name"][0]
                try:
                    feed["photo"] = subresource.card["photo"]
                except KeyError:
                    pass
            feeds.append(feed)
        return feeds

    def preview(self, url):
        """Return as much information about the URL as possible."""
        resource = tx.cache.add(url)
        items = []
        for entry in resource.feed["entries"]:
            item = {"type": "entry"}
            if "published" in entry:
                item["published"] = entry["published"]
            if "url" in entry:
                item["url"] = entry["url"]
            if "content" in entry:
                item["content"] = {
                    "html": entry["content"],
                    "text": entry["content-plain"],
                }
            if "category" in entry:
                item["category"] = entry["category"]
            if "photo" in entry:
                item["photo"] = entry["photo"]
            if "syndication" in entry:
                item["syndication"] = entry["syndication"]
            items.append(item)
        return {"items": items}

    def follow(self, url):
        """Start following the feed at given url."""
        feed_id = web.nbrandom(9)
        callback_url = f"{tx.origin}/hub/{feed_id}"
        tx.db.insert("following", url=url, feed_id=feed_id, callback_url=callback_url)
        web.enqueue(websub.subscribe, url, callback_url)

    @property
    def following(self):
        """Return the feeds you're currently following."""
        return [{"type": "feed", "url": f["url"]} for f in tx.db.select("following")]


@server.route(r"")
class MicrosubServer:
    """Implement a Microsub endpoint."""

    def get(self):
        """Complete a Microsub transaction or return an activity summary."""
        try:
            form = web.form("action", channel="default")
        except web.BadRequest:
            following = tx.sub.following
            return templates.activity(following)
        if form.action == "follow":
            response = {"items": tx.sub.following}
        elif form.action == "timeline":
            response = {"items": []}
        web.header("Content-Type", "application/json")
        return response

    def post(self):
        """Complete a Microsub transaction."""
        form = web.form("action", channel="default")
        if form.action == "channels":
            pass
        elif form.action == "search":
            response = {"results": tx.sub.search(form.query)}
        elif form.action == "preview":
            response = tx.sub.preview(form.url)
        elif form.action == "follow":
            tx.sub.follow(form.url)
            response = {"items": tx.sub.following}
        elif form.action == "unfollow":
            pass
        elif form.action == "timeline":
            pass
        elif form.action == "mute":
            pass
        elif form.action == "unmute":
            pass
        elif form.action == "block":
            pass
        elif form.action == "unblock":
            pass
        web.header("Content-Type", "application/json")
        return response


@server.route(r"search")
class MicrosubServerSearch:
    """."""

    def get(self):
        """Return search results for given `q`."""
        form = web.form("q")
        return templates.search(form.q, tx.sub.search(form.q))


@server.route(r"preview")
class MicrosubServerPreview:
    """."""

    def get(self):
        """Return a preview of given `url`."""
        form = web.form("url")
        return templates.preview(form.url, tx.sub.preview(form.url))
