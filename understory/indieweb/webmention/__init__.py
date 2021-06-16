"""Webmention receiver app and sending helper."""

from understory import web
from understory.web import tx


receiver = web.application(
    "Webmention", mount_prefix="mentions", mention_id=r"\w+"  # db=False,
)
templates = web.templates(__name__)


def send(source, targets, private=False) -> None:
    """Send a webmention."""
    # TODO ask archive.org to cache
    if source.startswith("/"):
        source = f"{tx.request.uri.scheme}://{tx.request.uri.netloc}/{source}"
    source = str(web.uri(source))
    target = str(web.uri(target))
    endpoint = web.discover_link(target, "webmention")
    if not endpoint:
        print(f"no webmention endpoint at {target}")
        return
    payload = {"source": source, "target": target}
    if private:
        code = web.nbrandom(32)
        # TODO tx.kv["mention-tokens"][":".join((path, str(target)))] = code
        payload["code"] = code
    store_mention(source, target)
    web.post(endpoint, data=payload)
    # TODO check if received and/or displayed
    # TODO !!! endpoint.post(payload)
    # TODO tx.db.update("mentions", what="data = ?", where="mention_id = ?",
    # TODO              vals=[mention, mention_id])


def receive(source, target) -> None:
    """Receive a webmention."""
    mention_id = store_mention(source, target)
    # mention_data = {}
    source_doc = tx.cache[source]
    source = source_doc.url.rstrip("/")
    mention = source_doc.mention(target).data  # TODO dict(..) inst .data
    tx.db.update(
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
    # tx.kv["mentioned"][mention_id] = pickle.dumps(mention_data)

    # TODO tx.kv.db.publish(f"{tx.host.identity}:resources:{path}",
    # TODO                  f"<section class=h-entry>a {entry_type}</section>")
    #               str(tx.view.entry_template(entry, resource,
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
    # if "https://{}".format(tx.host.name) in source_followees:
    #     # TODO private webmention for initial follow
    #     # TODO public webmention for public follow
    #     # TODO check first private then public
    #     # TODO represent & reciprocate follow accordingly
    #     root_url = web.uri(source_repr["properties"]["url"][0], secure=True)
    #     person = get_person(root_url.minimized)
    #     rel = tx.db.select("person__person",
    #                        where="from_id = 1 AND to_id = ?",
    #                        vals=[person["id"]])[0]
    #     if rel:
    #         tx.db.update("person__person", what="private = 0",
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


def store_mention(source, target):
    mention_id = web.nbrandom(9)
    tx.db.insert("mentions", mention_id=mention_id, source=source, target=target)
    return mention_id


# def store(mention_type, path, source, mention_id) -> bool:
#     """
#     store a webmention
#
#     return True if it was added, false if it already exists
#
#     """
#     return tx.kv["mentions", path, mention_type].hset(source, mention_id)


def wrap(handler, app):
    """Ensure endpoint link in head of root document."""
    tx.db.define(
        "mentions",
        received="DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
        mention_id="TEXT",
        data="JSON",
        source="TEXT",
        target="TEXT",
    )
    # TODO sniff referer header for a mention
    # XXX print(f"REFERER: {tx.request.headers.get('Referer')}")
    yield
    if str(tx.response.headers.content_type) == "text/html":
        doc = web.parse(tx.response.body)
        try:
            head = doc.select("head")[0]
        except IndexError:
            pass
        else:
            head.append("<link rel=webmention href=/mentions>")
            tx.response.body = doc.html
        web.header("Link", '</mentions>; rel="webmention"', add=True)


receiver.wrap(wrap, "post")


def get_mentions(path):
    if path.startswith("/"):
        path = tx.origin + path
    return tx.db.select("mentions", where="target = ?", vals=[path])


@receiver.route(r"")
class Mentions:
    """."""

    def get(self):
        return templates.mentions(tx.db.select("mentions"))

    def post(self):
        form = web.form("source", "target")
        web.enqueue(receive, form.source, form.target)
        raise web.Accepted("webmention received")


@receiver.route(r"{mention_id}")
class Mention:
    """."""

    def get(self):
        """Details of the webmention, with status information in mf2."""
        mention = tx.db.select(
            "mentions", where="mention_id = ?", vals=[self.mention_id]
        )
        return templates.mention(mention)

    def post(self):
        """Details of the webmention."""
        raise web.Accepted("webmention received")
        # XXX f"{tx.host.name}/mentions/{mention_id}")
