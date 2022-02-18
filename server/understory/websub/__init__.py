"""
[WebSub][0] publisher and subscriber.

> WebSub provides a common mechanism for communication between publishers
> of any kind of Web content and their subscribers, based on HTTP web hooks.
> Subscription requests are relayed through hubs, which validate and verify
> the request. Hubs then distribute new and updated content to subscribers
> when it becomes available. WebSub was previously known as PubSubHubbub. [0]

[0]: https://w3.org/TR/websub

"""

from understory import mf, web

app = web.application(
    __name__,
    prefix="subscriptions",
    args={"subscription_id": r".+"},
    model={
        "received_subscriptions": {  # others following you
            "received_subscription_id": "TEXT UNIQUE",
            "subscribed": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "topic_url": "TEXT UNIQUE",
            "callback_url": "TEXT",
        },
        "sent_subscriptions": {  # you following others
            "sent_subscription_id": "TEXT UNIQUE",
            "subscribed": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "topic_url": "TEXT UNIQUE",
            "callback_url": "TEXT UNIQUE",
            "verified": "INTEGER NOT NULL",
        },
        "incoming_posts": {"sent_subscription_id": "TEXT", "permalink": "TEXT"},
    },
)

subscription_lease = 60 * 60 * 24 * 90


def publish(hub_url, topic_url, resource):
    """"""
    for subscription in get_received_subscriptions_by_topic(web.tx.db, topic_url):
        if subscription["topic_url"] != topic_url:
            continue
        web.post(
            subscription["callback_url"],
            headers={
                "Content-Type": "text/html",
                "Link": ",".join(
                    (
                        f'<{hub_url}>; rel="hub"',
                        f'<{topic_url}>; rel="self"',
                    )
                ),
            },
            data=resource,
        ).text


def subscribe(subscription_prefix, topic_url):
    """Send subscription request."""
    self_url = web.discover_link(topic_url, "self")
    hub = web.discover_link(topic_url, "hub")
    callback_url = add_sent_subscription(web.tx.db, subscription_prefix, str(self_url))
    web.post(
        hub,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "hub.mode": "subscribe",
            "hub.topic": str(self_url),
            "hub.callback": callback_url,
        },
    )


def unsubscribe(subscription_id):
    # TODO send unsub request
    remove_sent_subscription(web.tx.db, subscription_id)


def verify_received_subscription(topic_url, callback_url):
    """Verify subscription request and add follower to database."""
    challenge = web.nbrandom(32)
    response = web.get(
        callback_url,
        params={
            "hub.mode": "subscribe",
            "hub.topic": topic_url,
            "hub.challenge": challenge,
            "hub.lease_seconds": subscription_lease,
        },
    )
    if response.text != challenge:
        raise web.BadRequest(
            "subscription verification response does not match challenge"
        )
    add_received_subscription(web.tx.db, topic_url, callback_url)


@app.wrap
def connect_model(handler, main_app):
    """Connect the model to this transaction's database."""
    web.tx.websub = app.model(web.tx.db)
    yield


@app.wrap
def linkify_head(handler, main_app):
    """Ensure hub and topic links are in head of current document."""
    # TODO limit to subscribables
    yield
    if web.tx.request.uri.path in ("",):
        web.add_rel_links(hub="/subscriptions")
        web.add_rel_links(self=f"/{web.tx.request.uri.path}")


@app.control(r"")
class Hub:
    """."""

    def get(self):
        return app.view.hub(
            web.tx.websub.get_sent_subscriptions(),
            web.tx.websub.get_received_subscriptions(),
        )

    def post(self):
        try:
            topic_url = web.form("topic_url").topic_url
        except web.BadRequest:
            pass
        else:
            web.enqueue(
                websub.subscribe, f"{web.tx.origin}/subscriptions/sent", topic_url
            )
            return app.view.sent.subscription_requested()
        mode = web.form("hub.mode")["hub.mode"]
        if mode != "subscribe":
            raise web.BadRequest(
                'hub only supports subscription; `hub.mode` must be "subscribe"'
            )
        form = web.form("hub.topic", "hub.callback")
        # TODO raise web.BadRequest("topic not found")
        web.enqueue(
            websub.verify_received_subscription, form["hub.topic"], form["hub.callback"]
        )
        raise web.Accepted("subscription request accepted")


@app.control(r"sent/{subscription_id}")
class SentSubscription:
    """."""

    def get(self):
        """Confirm subscription request."""
        try:
            action = web.form("action").action
        except web.BadRequest:
            pass
        else:
            if action == "unsubscribe":
                web.enqueue(websub.unsubscribe, self.subscription_id)
                return "unsubscribed"
            raise web.BadRequest("action must be `unsubscribe`")
        try:
            form = web.form(
                "hub.mode", "hub.topic", "hub.challenge", "hub.lease_seconds"
            )
        except web.BadRequest:
            pass
        else:
            web.tx.websub.verify_sent_subscription(
                form["hub.topic"],
                f"{web.tx.origin}/subscriptions/sent/{self.subscription_id}",
            )
            # TODO verify the subscription
            return form["hub.challenge"]
        return "sent sub"

    def post(self):
        """Check feed for updates (or store the fat ping)."""
        feed = mf.parse(web.tx.request.body._data)
        for entry in mf.interpret_feed(feed, "http://google.com")["entries"]:
            print(entry)
        return ""


@app.control(r"received/{subscription_id}")
class ReceivedSubscription:
    """."""

    def get(self):
        return app.view.sent.subscription(
            web.tx.websub.get_sent_subscription_by_id(self.subscription_id)
        )


@app.model.control
def add_sent_subscription(db, subscription_prefix, topic_url):
    while True:
        sent_subscription_id = web.nbrandom(5)
        callback_url = f"{subscription_prefix}/{sent_subscription_id}"
        try:
            db.insert(
                "sent_subscriptions",
                sent_subscription_id=sent_subscription_id,
                topic_url=topic_url,
                callback_url=callback_url,
                verified=0,
            )
        except db.IntegrityError:
            continue
        break
    return callback_url


@app.model.control
def verify_sent_subscription(db, topic_url, callback_url):
    with db.transaction as cur:
        cur.update(
            "sent_subscriptions",
            verified=1,
            where="topic_url = ? AND callback_url = ?",
            vals=[topic_url, callback_url],
        )


@app.model.control
def remove_sent_subscription(db, send_subscription_id):
    db.delete(
        "sent_subscriptions",
        where="sent_subscription_id = ?",
        vals=[send_subscription_id],
    )


@app.model.control
def get_sent_subscriptions(db):
    return db.select("sent_subscriptions")


@app.model.control
def get_sent_subscription_by_id(db, sent_subscription_id):
    return db.select(
        "sent_subscriptions",
        where="sent_subscription_id = ?",
        vals=[sent_subscription_id],
    )[0]


@app.model.control
def add_received_subscription(db, topic_url, callback_url):
    while True:
        received_subscription_id = web.nbrandom(5)
        try:
            db.insert(
                "received_subscriptions",
                received_subscription_id=received_subscription_id,
                topic_url=topic_url,
                callback_url=callback_url,
            )
        except db.IntegrityError:
            continue
        break


@app.model.control
def get_received_subscriptions(db):
    return db.select("received_subscriptions")


@app.model.control
def get_received_subscriptions_by_topic(db, topic_url):
    return db.select("received_subscriptions", where="topic_url = ?", vals=[topic_url])
