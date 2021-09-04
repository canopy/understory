"""
WebSub publisher and subscriber implementations.

> WebSub provides a common mechanism for communication between publishers
> of any kind of Web content and their subscribers, based on HTTP web hooks.
> Subscription requests are relayed through hubs, which validate and verify
> the request. Hubs then distribute new and updated content to subscribers
> when it becomes available. WebSub was previously known as PubSubHubbub. [0]

[0]: https://w3.org/TR/websub

"""

from understory import sql, web
from understory.web import tx

publisher_app = web.application(
    "WebSubPublisher", mount_prefix="pub/subscribers", subscription_id=r".+"
)
publisher_model = sql.model(
    "WebSubPublisher",
    0,
    followers={
        "followed": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "topic_url": "TEXT",
        "callback_url": "TEXT",
    },
)

subscriber_app = web.application(
    "WebSubSubscriber", mount_prefix="sub/subscriptions", subscription_id=r".+"
)

templates = web.templates(__name__)
subscription_lease = 60 * 60 * 24 * 90


def publish(topic_url, callback_url):
    """"""
    callback_url
    for channel in topic_url:
        pass
    web.post(callback_url)


def subscribe(url, callback_url):
    """Send subscription request."""
    topic_url = web.discover_link(url, "self")
    hub = web.discover_link(url, "hub")
    web.post(
        hub,
        data={
            "hub.mode": "subscribe",
            "hub.topic": str(topic_url),
            "hub.callback": callback_url,
        },
    )


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


def wrap_publisher(handler, app):
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


@publisher_app.route(r"")
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


@subscriber_app.route(r"{subscription_id}")
class Subscription:
    """."""

    def get(self):
        """Confirm subscription request."""
        form = web.form("hub.mode", "hub.topic", "hub.challenge", "hub.lease_seconds")
        # TODO verify the subscription
        return form["hub.challenge"]

    def post(self):
        """Check feed for updates (or store the fat ping)."""
        print(tx.request.body._data)
        return
