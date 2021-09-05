""""""

from understory import web
from understory.web import tx

app = web.application(
    __name__,
    prefix="pub/subscribers",
    model={
        "followers": {
            "followed": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "topic_url": "TEXT",
            "callback_url": "TEXT",
        }
    },
)

subscription_lease = 60 * 60 * 24 * 90


def publish(topic_url, callback_url):
    """"""
    callback_url
    for channel in topic_url:
        pass
    web.post(callback_url)


def wrap(handler, app):
    """Ensure server links are in head of root document."""
    yield
    # TODO limit to subscribables
    if tx.request.uri.path == "" and tx.response.body:
        doc = web.parse(tx.response.body)
        try:
            head = doc.select("head")[0]
        except IndexError:
            pass
        else:
            head.append(f"<link rel=self href=/{tx.request.uri.path}>")
            head.append("<link rel=hub href=/hub>")
            tx.response.body = doc.html
        web.header("Link", f'/<{tx.request.uri.path}>; rel="self"', add=True)
        web.header("Link", '</hub>; rel="hub"', add=True)


@app.control(r"")
class Hub:
    """."""

    def get(self):
        return templates.hub(tx.db.select("followers"))

    def post(self):
        mode = web.form("hub.mode")["hub.mode"]
        if mode != "subscribe":
            raise web.BadRequest(
                "hub only supports subscription; " '`hub.mode` must be "subscribe"'
            )
        form = web.form("hub.topic", "hub.callback")
        # TODO raise web.BadRequest("topic not found")
        web.enqueue(verify_subscription, form["hub.topic"], form["hub.callback"])
        raise web.Accepted("subscription request accepted")


def verify_subscription(topic_url, callback_url):
    """Verify subscription request and add follower to database."""
    verification_data = {
        "hub.mode": "subscribe",
        "hub.topic": topic_url,
        "hub.challenge": web.nbrandom(32),
        "hub.lease_seconds": subscription_lease,
    }
    response = web.get(callback_url, params=verification_data)
    if response.text != verification_data["hub.challenge"]:
        return
    tx.db.insert(
        "followers",
        topic_url=web.uri(topic_url).path,
        callback_url=str(web.uri(callback_url)),
    )
