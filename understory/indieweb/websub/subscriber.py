""""""

from understory import web
from understory.web import tx

app = web.application(
    __name__,
    prefix="sub/subscriptions",
    args={
        "subscription_id": r".+",
    },
)


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


@app.control(r"{subscription_id}")
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
