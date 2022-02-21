"""
[Webmention][0] receiver and sender.

> Webmention is a simple way to notify any URL when you mention it on
> your site. From the receiver's perspective, it's a way to request
> notifications when other sites mention it. 

[0]: https://w3.org/TR/webmention

"""

# TODO https://indieweb.org/Salmention
# TODO https://indieweb.org/Vouch

from understory import web

app = web.application(
    __name__,
    prefix="mentions",
    args={"mention_id": r"\w+"},
    model={
        "received_mentions": {  # others mentioning you
            "mention_id": "TEXT",
            "mentioned": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "source": "TEXT",
            "target": "TEXT",
            "data": "JSON",
        },
        "sent_mentions": {  # you mentioning others
            "mention_id": "TEXT",
            "mentioned": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "source": "TEXT",
            "target": "TEXT",
            "response": "JSON",
        },
    },
)


def receive(source, target) -> None:
    """
    Receive a webmention for `target` on behalf of `source`.

    """
    # TODO re-queue failures w/ a logarithmic backoff
    mention_id = web.tx.webmention.store_received_mention(source, target)
    # mention_data = {}
    source_doc = web.tx.cache[source]
    source = source_doc.url.rstrip("/")
    mention = source_doc.mention(target).data  # TODO dict(..) inst .data
    web.tx.db.update(
        "mentions", what="data = ?", where="mention_id = ?", vals=[mention, mention_id]
    )
    return

    # XXX source_data = mf.parse(source_doc.text, url=source)
    # XXX source_repr = mf.util.representative_card(source_data, source)
    # XXX if not source_repr:
    # XXX     raise web.BadRequest("No representative h-card found at source.")

    # XXX ZZZ path = web.uri(target).path
    # XXX ZZZ plural, _, resource_path = path.partition("/")
    # XXX ZZZ try:
    # XXX ZZZ     t = get_type(plural)
    # XXX ZZZ     resource = get_resource(t.s, resource_path)
    # XXX ZZZ except (TypeError, ResourceNotFound):
    # XXX ZZZ     resource = None

    # cache.put(source_url, parse=True)  # , html=source_doc.text)
    # source = interpret(source_url)
    # mention_data["source"] = source

    # # TODO ensure links are in page as with likes below
    # if "entry" in source:
    #     entry = source["entry"]
    #     entry_type = entry["-type"]
    #     if resource:
    #         if entry_type == "photo":
    #             print("photo post")
    #         elif entry_type == "associate":
    #             store("associations", path, source_url, mention_id)
    #         elif entry_type == "like":
    #             for like_of in entry["like-of"]:
    #                 if like_of["url"] == target:
    #                     store("likes", path, source_url, mention_id)
    #         elif entry_type == "vote":
    #             vote_on = entry["vote-on"][0]
    #             if vote_on["url"] == target:
    #                 store("votes", path, source_url, mention_id)
    #         elif entry_type == "note" and t.s == "code":
    #             t.utility(resource["-id"]).add_issue(source_url, entry,
    #                                                  mention_id)
    #         elif entry_type in ("note", "image") and \
    #                                t.s in ("note", "image"):
    #             if "in-reply-to" in entry:
    #                 for in_reply_to in entry["in-reply-to"]:
    #                     if in_reply_to["url"] == target:
    #                         store("replies", path, source_url, mention_id)
    #                 # bubble up mention if resource itself is a reply
    #                 if "in-reply-to" in resource:
    #                     send(path, resource["in-reply-to"])
    #     else:
    #         if entry_type == "follow":
    #             store("follows", path, source_url, mention_id)
    #         elif entry_type == "associate":
    #             store("associations", path, source_url, mention_id)
    # else:
    #     store("generic", path, source_url, mention_id)

    # mention_data["confirmed"] = time.time()
    # web.tx.kv["mentioned"][mention_id] = pickle.dumps(mention_data)

    # TODO web.tx.kv.db.publish(f"{web.tx.host.identity}:resources:{path}",
    # TODO                  f"<section class=h-entry>a {entry_type}</section>")
    #               str(web.tx.view.entry_template(entry, resource,
    #                                      t.view.type(entry, resource))))

    # # check if networking request
    # source_followees = source_data["rels"].get("followee", [])
    # source_followers = source_data["rels"].get("follower", [])
    # print()
    # print("ees", source_followees)
    # print("ers", source_followers)
    # if "code" in form:
    #     print("code", form.code)
    # print()
    # if "https://{}".format(web.tx.host.name) in source_followees:
    #     # TODO private webmention for initial follow
    #     # TODO public webmention for public follow
    #     # TODO check first private then public
    #     # TODO represent & reciprocate follow accordingly
    #     root_url = web.uri(source_repr["properties"]["url"][0], secure=True)
    #     person = get_person(root_url.minimized)
    #     rel = web.tx.db.select("person__person",
    #                        where="from_id = 1 AND to_id = ?",
    #                        vals=[person["id"]])[0]
    #     if rel:
    #         web.tx.db.update("person__person", what="private = 0",
    #                      where="from_id = 1 AND to_id = ?",
    #                      vals=[person["id"]])
    #         # TODO send return mention to notify if publicize
    #     return "okay"
    #     root_data = mf.parse(url=root_url)
    #     root_repr = mf.util.representative_card(root_data, root_url)
    #     if not root_repr:
    #         raise web.BadRequest("No representative h-card found "
    #                              "at source's root.")
    #     name = root_repr["properties"]["name"][0]
    #     try:
    #         email = root_repr["properties"]["email"][0]
    #     except IndexError:
    #         email = ""
    #     pubkey = ""
    #     person_feed = mf.util.interpret_feed(root_data, source_url)
    #     person_feed_license = root_data["rels"]["license"][0]
    #     add_person(name, root_url, email, pubkey, person_feed["name"],
    #                person_feed_license, "follower")


@app.wrap
def connect_model(handler, main_app):
    """Connect the model to this transaction's database."""
    web.tx.webmention = app.model(web.tx.db)
    yield


@app.wrap
def linkify_head(handler, main_app):
    """Ensure receiver link is in head of current document."""
    yield
    if web.tx.request.uri.path in ("",):
        web.add_rel_links(webmention="/mentions")


@app.wrap
def track_referrers(handler, main_app):
    """Store the origin provided in any Referer request headers."""
    # TODO print(f"REFERER: {web.tx.request.headers.get('Referer')}")
    yield


@app.control(r"")
class Mentions:
    """."""

    def get(self):
        """Return a page of all mentions."""
        return app.view.index(
            web.tx.webmention.get_received_mentions(),
            web.tx.webmention.get_sent_mentions(),
        )

    def post(self):
        """"""
        form = web.form("source", "target")
        web.enqueue(receive, form.source, form.target)
        raise web.Accepted("webmention received")


@app.control(r"received")
class ReceivedMentions:
    """."""

    def get(self):
        """Details of the webmention, with status information in mf2."""
        return app.view.received.index(
            web.tx.webmention.get_received_mention_by_id(self.mention_id)
        )


@app.control(r"received/{mention_id}")
class ReceivedMention:
    """."""

    def get(self):
        """Details of the webmention, with status information in mf2."""
        return app.view.received.mention(
            web.tx.webmention.get_received_mention_by_id(self.mention_id)
        )

    def post(self):
        """Details of the webmention."""
        raise web.Accepted("webmention received")
        # XXX f"{web.tx.host.name}/mentions/{mention_id}")


@app.control(r"sent")
class SentMentions:
    """."""

    def get(self):
        """Details of the webmention, with status information in mf2."""
        return app.view.sent.index()


@app.model.control
def store_received_mention(db, source, target):
    mention_id = web.nbrandom(9)
    db.insert("received_mentions", mention_id=mention_id, source=source, target=target)
    return mention_id


@app.model.control
def get_received_mentions(db):
    """Return a list of all received mentions ordered by most recent."""
    return db.select("received_mentions", order="received DESC")


@app.model.control
def get_received_mention_by_id(db, mention_id):
    return db.select("received_mentions", where="mention_id = ?", vals=[mention_id])


@app.model.control
def get_received_mentions_by_path(db, url):
    return db.select("received_mentions", where="target = ?", vals=[url])


@app.model.control
def get_sent_mentions(db):
    """Return a list of all sent mentions ordered by most recent."""
    return db.select("sent_mentions", order="sent DESC")
