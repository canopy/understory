"""Micropub server app."""

import pathlib
import random

import pendulum
import sh
import vobject

from understory import web
from understory.web import tx

from .. import webmention

from .util import discover_post_type


server = web.application(
    "MicropubServer",
    mount_prefix="pub",
    db=False,
    channel=r".+",
    entry=r".+",
    nickname=r"[A-Za-z0-9-]+",
    filename=rf"{web.nb60_re}{{4}}.\w{{1,10}}",
)
content = web.application(
    "MicropubContent",
    db=False,
    year=r"\d{4}",
    month=r"\d{2}",
    day=r"\d{2}",
    seconds=web.nb60_re + r"{,4}",
    slug=r"[\w_-]+",
)
templates = web.templates(__name__)

# TODO supported_types = {"RSVP": ["in-reply-to", "rsvp"]}


def send(properties, endpoint=None, h="entry", token=None):
    """Send a Micropub request to a Micropub server."""
    # TODO FIXME what's in the session?
    if endpoint is None:
        endpoint = tx.user.session["micropub_endpoint"]
    response = web.post(
        endpoint,
        headers={"Authorization": f"Bearer {token}"},
        json={"type": [f"h-{h}"], "properties": properties},
    )
    return response.location, response.links


def define_table():
    """Define the `resources`, `media` and `syndication` tables."""
    tx.db.define(
        "resources", permalink="TEXT UNIQUE", version="TEXT UNIQUE", resource="JSON"
    )
    # TODO tx.db.define("updates")
    tx.db.define("media", mid="TEXT", sha256="TEXT UNIQUE", size="INTEGER")
    tx.db.define("syndication", destination="JSON NOT NULL")


def wrap_server(handler, app):
    """Ensure server links are in head of root document."""
    define_table()
    tx.pub = LocalClient()
    yield
    if tx.request.uri.path == "" and tx.response.body:
        doc = web.parse(tx.response.body)
        try:
            head = doc.select("head")[0]
        except IndexError:
            pass
        else:
            head.append("<link rel=micropub href=/pub>")
            tx.response.body = doc.html
        web.header("Link", '</pub>; rel="micropub"', add=True)


def route_unrouted(handler, app):
    """Handle channels."""
    for channel in tx.pub.get_channels():
        if channel["resource"]["url"][0] == f"/{tx.request.uri.path}":
            posts = tx.pub.get_posts_by_channel(channel["resource"]["uid"][0])
            web.header("Content-Type", "text/html")
            raise web.OK(templates.channel(channel, posts))
    yield


def generate_vcard(nickname):
    """"""
    card = tx.pub.get_card(nickname)
    vcard = vobject.vCard()
    vcard.add("prodid").value = "-//Canopy//understory 0.0.0//EN"
    vcard.add("uid").value = card["uid"][0]
    vcard.add("fn").value = card["name"][0]
    return vcard.serialize()

    # TODO # TODO if identity["type"] == "identity":
    # TODO n = card.add("n")
    # TODO names = {}
    # TODO for name_type in ("prefix", "given", "additional",
    #                        "family", "suffix"):
    # TODO     if identity[name_type]:
    # TODO         names[name_type] = identity[name_type].split(";")
    # TODO n.value = vobject.vcard.Name(**names)
    # TODO # TODO else:
    # TODO # TODO     card.add("n")
    # TODO # TODO     card.add("org").value = [identity["name"]]

    # TODO # TODO card.add("nickname").value = identity["name"]
    # TODO card.add("sort_string").value = identity["sort_string"]

    # TODO for number, types in identity["telephones"]:
    # TODO     entry = card.add("tel")
    # TODO     entry.value = number
    # TODO     if types:
    # TODO         entry.params["TYPE"] = types

    # TODO for url, types in identity["websites"]:
    # TODO     entry = card.add("url")
    # TODO     entry.value = url
    # TODO     if types:
    # TODO         entry.params["TYPE"] = types

    # TODO try:
    # TODO     photo_id = identity["photos"][0]
    # TODO except IndexError:
    # TODO     pass
    # TODO else:
    # TODO     photo_data = \
    # TODO         canopy.branches["images"].photos.get_photo_data(id=photo_id)
    # TODO     photo = card.add("photo")
    # TODO     photo.value = photo_data
    # TODO     photo.encoding_param = "b"
    # TODO     photo.type_param = "JPEG"

    # item_index = 0
    # for vals in card.contents.values():
    #     for val in vals:
    #         if val.group:
    #             item_index = int(val.group[4:])

    # for related, types in get_relationships(identity["id"]):
    #     uri = "https://{}/identities/{}/{}.vcf".format(tx.host.name,
    #                                                related["identifier"],
    #                                                related["slug"])
    #     rel = card.add("related")
    #     rel.value = uri
    #     rel.params["TYPE"] = types
    #     for type in types:
    #         group_name = "item{}".format(item_index)
    #         rel_name = card.add("x-abrelatednames")
    #         rel_name.value = related["name"]
    #         rel_name.group = group_name
    #         rel_uri = card.add("x-aburi")
    #         rel_uri.value = uri
    #         rel_uri.group = group_name
    #         rel_type = card.add("x-ablabel")
    #         rel_type.value = "_$!<{}>!$_".format(type)
    #         rel_type.group = group_name
    #         item_index += 1


class LocalClient:
    """A localized interface to the endpoint's backend."""

    def create(self, resource_type, **resource):
        """Create a resource."""
        for k, v in resource.items():
            if not isinstance(v, list):
                resource[k] = [v]
            flat_values = []
            for v in resource[k]:
                if isinstance(v, dict):
                    v = dict(**v["properties"], type=[v["type"][0].removeprefix("h-")])
                flat_values.append(v)
            resource[k] = flat_values

        # TODO --##--
        resource["published"] = [
            {"datetime": web.utcnow(), "timezone": "America/Los_Angeles"}
        ]
        for date_prop in ("published", "updated"):
            try:
                resource[date_prop][0]["datetime"] = pendulum.from_format(
                    resource[date_prop][0]["datetime"], "YYYY-MM-DDTHH:mm:ssZ"
                )
                # TODO assert `timezone` exists
            except KeyError:
                pass
        # if "published" in resource:
        #     resource["published"][0]["datetime"] = \
        #         pendulum.from_format(resource["published"][0]["datetime"],
        #                              "YYYY-MM-DDTHH:mm:ssZ")
        #     published = resource["published"]
        # else:
        #     published = [{"datetime": web.utcnow(),
        #                   "timezone": "America/Los_Angeles"}]
        # TODO --##--

        resource["visibility"] = resource.get("visibility", ["public"])
        # XXX resource["channel"] = resource.get("channel", [])
        mentions = []
        urls = resource.pop("url", [])
        if resource_type == "card":
            slug = resource.get("nickname", resource.get("name"))[0]
            urls.insert(0, f"/pub/cards/{web.textslug(slug)}")
        elif resource_type == "feed":
            name_slug = web.textslug(resource["name"][0])
            try:
                slug = resource["slug"][0]
            except KeyError:
                slug = name_slug
            resource.update(uid=[slug if slug else name_slug])
            resource.pop("channel", None)
            # XXX urls.insert(0, f"/{slug}")
        elif resource_type == "entry":
            #                                         REQUEST URL
            # 1) given: url=/xyz                        => look for exact match
            #     then: url=[/xyz, /2021/3/5...]
            # 2) given: channel=abc, slug=foo           => construct
            #     then: url=[/2021/3/5...]
            # 3) given: no slug                         => only via permalink
            #     then: url=[/2021/3/5...]
            post_type = discover_post_type(resource)
            slug = None
            if post_type == "article":
                slug = resource["name"][0]
            elif post_type == "bookmark":
                mentions.append(resource["bookmark-of"][0])
            elif post_type == "like":
                mentions.append(resource["like-of"][0])
            elif post_type == "rsvp":
                mentions.append(resource["in-reply-to"][0])
            # elif post_type == "identification":
            #     identifications = resource["identification-of"]
            #     identifications[0] = {"type": "cite",
            #                           **identifications[0]["properties"]}
            #     textslug = identifications[0]["name"]
            #     mentions.append(identifications[0]["url"])
            # elif post_type == "follow":
            #     follows = resource["follow-of"]
            #     follows[0] = {"type": "cite", **follows[0]["properties"]}
            #     textslug = follows[0]["name"]
            #     mentions.append(follows[0]["url"])
            #     tx.sub.follow(follows[0]["url"])
            author_id = tx.db.select(
                "resources",
                where="""json_extract(resources.resource,
                                                  '$.uid[0]') == ?""",
                vals=[tx.origin],
            )[0]["version"]
            resource.update(author=[author_id])
        # elif resource_type == "event":
        #     slug = resource.get("nickname", resource.get("name"))[0]
        #     urls.insert(0, f"/pub/cards/{web.textslug(slug)}")
        #     # if resource["uid"] == str(web.uri(tx.host.name)):
        #     #     pass
        resource.update(url=urls, type=[resource_type])
        published = resource["published"][0]["datetime"]
        permalink_base = f"/{web.timeslug(published)}"

        def generate_trailer():
            letterspace = "abcdefghijkmnopqrstuvwxyz23456789"
            trailer = "".join([random.choice(letterspace) for i in range(2)])
            if trailer in ("bs",):
                return generate_trailer()
            else:
                return trailer

        while True:
            permalink = f"{permalink_base}/{generate_trailer()}"
            resource["url"].append(permalink)
            try:
                tx.db.insert(
                    "resources",
                    permalink=permalink,
                    version=web.nbrandom(10),
                    resource=resource,
                )
            except tx.db.IntegrityError:
                continue
            break

        web.publish("/recent", ".feed[-0:-0]", resource)
        for mention in mentions:
            web.enqueue(webmention.send, f"{tx.origin}{permalink}", mention)
        # TODO web.publish(mention, ".responses[-1:-1]", resource)
        # for subscriber in subscribers:
        #     web.enqueue(websub.publish)
        return permalink

    def read(self, url):
        """Return an entry with its metadata."""
        if not url.startswith(("http://", "https://")):
            url = f"/{url.strip('/')}"
        try:
            resource = tx.db.select(
                "resources",
                where="""json_extract(
                                                 resources.resource,
                                                 '$.url[0]') == ?""",
                vals=[url],
            )[0]
        except IndexError:
            try:
                resource = tx.db.select(
                    "resources",
                    where="""json_extract(
                                                     resources.resource,
                                                     '$.alias[0]') == ?""",
                    vals=[url],
                )[0]
            except IndexError:
                web.header("Content-Type", "text/html")  # TODO FIXME XXX
                raise web.NotFound(templates.post_not_found(url))
        r = resource["resource"]
        if "entry" in r["type"]:
            r["author"] = self.get_version(r["author"][0])["resource"]
        return resource

    def update(self, url, add=None, replace=None, remove=None):
        """Update a resource."""
        now = web.utcnow()
        path = f"/{url.strip('/')}"
        resource = tx.db.select("resources", where="path = ?", vals=[path])[0][
            "resource"
        ]
        for prop, vals in add.items():
            try:
                resource[prop].extend(vals)
            except KeyError:
                resource[prop] = vals
        resource["updated"] = now
        tx.db.update("resources", resource=resource, where="path = ?", vals=[path])
        # TODO web.publish(url, f".{prop}[-0:-0]", vals)

    def delete(self, url):
        """Delete a resource."""
        pass  # TODO

    def search(self, query):
        """Return a list of resources containing `query`."""
        where = """json_extract(resources.resource,
                       '$.bookmark-of[0].url') == ?
                   OR json_extract(resources.resource,
                       '$.like-of[0].url') == ?"""
        return tx.db.select("resources", vals=[query, query], where=where)

    def get_version(self, version):
        """Return a snapshot of resource at given version."""
        return tx.db.select("resources", where="version = ?", vals=[version])[0]

    def get_entry(self, path):
        """"""

    def get_card(self, nickname):
        """Return the card with given nickname."""
        resource = tx.db.select(
            "resources",
            vals=[nickname],
            where="""json_extract(resources.resource,
                                             '$.nickname[0]') == ?""",
        )[0]
        return resource["resource"]

    def get_event(self, path):
        """"""

    def get_entries(self, limit=20, modified="DESC"):
        """Return a list of entries."""
        return tx.db.select(
            "resources",
            order=f"""json_extract(resources.resource,
                                          '$.published[0]') {modified}""",
            where="""json_extract(resources.resource,
                                         '$.type[0]') == 'entry'""",
            limit=limit,
        )

    def get_cards(self, limit=20):
        """Return a list of alphabetical cards."""
        return tx.db.select(
            "resources",  # order="modified DESC",
            where="""json_extract(resources.resource,
                                         '$.type[0]') == 'card'""",
        )

    def get_rooms(self, limit=20):
        """Return a list of alphabetical rooms."""
        return tx.db.select(
            "resources",  # order="modified DESC",
            where="""json_extract(resources.resource,
                                         '$.type[0]') == 'room'""",
        )

    def get_channels(self):
        """Return a list of alphabetical channels."""
        return tx.db.select(
            "resources",  # order="modified DESC",
            where="""json_extract(resources.resource,
                                         '$.type[0]') == 'feed'""",
        )

    def get_posts_by_channel(self, uid):
        """Return the card with given nickname."""
        return tx.db.select(
            "resources",
            vals=[uid],
            where="""json_extract(resources.resource,
                                         '$.channel[0]') == ?""",
            order="""json_extract(resources.resource,
                                         '$.published[0]') DESC""",
        )

    # def get_channels(self):
    #     """Return a list of channels."""
    #     return [r["value"] for r in
    #             tx.db.select("""resources,
    #                            json_tree(resources.resource, '$.channel')""",
    #                          what="DISTINCT value", where="type = 'text'")]

    def get_year(self, year):
        return tx.db.select(
            "resources",
            order="""json_extract(resources.resource,
                                         '$.published[0].datetime') ASC""",
            where=f"""json_extract(resources.resource,
                                          '$.published[0].datetime')
                                          LIKE '{year}%'""",
        )

    def get_media(self):
        """Return a list of media filepaths."""
        try:
            filepaths = list(pathlib.Path(tx.host.name).iterdir())
        except FileNotFoundError:
            filepaths = []
        return filepaths

    def get_filepath(self, filename):
        """Return a media file's path."""
        return pathlib.Path(tx.host.name) / filename


@server.route(r"")
class MicropubEndpoint:
    """."""

    def get(self):
        local_client = LocalClient()
        try:
            form = web.form("q")
        except web.BadRequest:
            channels = local_client.get_channels()
            entries = local_client.get_entries()
            cards = local_client.get_cards()
            events = []  # local_client.get_events()
            reviews = []  # local_client.get_reviews()
            rooms = local_client.get_rooms()
            media = local_client.get_media()
            return templates.activity(
                channels, entries, cards, events, reviews, rooms, media
            )
        syndication_endpoints = []

        def generate_channels():
            return [
                {"name": r["name"][0], "uid": r["uid"][0]}
                for r in local_client.get_channels()
            ]

        if form.q == "config":
            response = {
                "q": ["category", "contact", "source", "syndicate-to"],
                "media-endpoint": f"https://{tx.host.name}/pub/media",
                "syndicate-to": syndication_endpoints,
                "visibility": ["public", "unlisted", "private"],
            }
            # TODO "channels": generate_channels()}
        elif form.q == "channel":
            response = {"channels": generate_channels()}
        elif form.q == "source":
            response = {}
            if "search" in form:
                response = {
                    "items": [
                        {"url": [r["resource"]["url"]]}
                        for r in local_client.search(form.search)
                    ]
                }
            elif "url" in form:
                response = dict(local_client.read(form.url))
            else:
                pass  # TODO list all posts
        else:
            raise web.BadRequest(
                """unsupported query.
                                    check `q=config` for support."""
            )
        web.header("Content-Type", "application/json")
        return response

    def post(self):
        try:
            form = web.form("h")
        except web.BadRequest:
            resource = tx.request.body._data
        else:
            h = form.pop("h")
            properties = {
                k.rstrip("[]"): (v if isinstance(v, list) else [v])
                for k, v in form.items()
            }
            resource = {"type": [f"h-{h}"], "properties": properties}
        client = LocalClient()
        action = resource.pop("action", None)
        if action == "update":
            url = resource.pop("url")
            client.update(url, **resource)
            return
        elif action == "delete":
            pass
        elif action == "undelete":
            pass
        permalink = client.create(
            resource["type"][0].partition("-")[2], **resource["properties"]
        )
        # web.header("Link", '</blat>; rel="shortlink"', add=True)
        # web.header("Link", '<https://twitter.com/angelogladding/status/'
        #                    '30493490238590234>; rel="syndication"', add=True)
        raise web.Created("post created", permalink)


@server.route(r"channels")
class Channels:
    """All channels."""

    def get(self):
        return templates.channels(LocalClient().get_channels())


@server.route(r"channels/{channel}")
class Channel:
    """A single channel."""

    def get(self):
        return templates.channel(self.channel)


@server.route(r"entries")
class Entries:
    """All entries on file."""

    def get(self):
        return templates.entries(LocalClient().get_entries(), templates.render_dict)


@server.route(r"entries/{entry}")
class Entry:
    """A single entry on file."""

    def get(self):
        try:
            resource = tx.db.select(
                "cache", where="url = ?", vals=[f"https://{self.resource}"]
            )[0]
        except IndexError:
            resource = tx.db.select(
                "cache", where="url = ?", vals=[f"http://{self.resource}"]
            )[0]
        return templates.cache_resource(resource)


@server.route(r"cards")
class Cards:
    """
    All cards on file.

    `OPTIONS`, `PROPFIND` and `REPORT` methods provide CardDAV support.

    """

    def get(self):
        return templates.cards(tx.pub.get_cards(), templates.render_dict)

    def options(self):
        """Signal capabilities to CardDAV client."""
        web.header("DAV", "1, 2, 3, access-control, addressbook")
        web.header(
            "Allow",
            "OPTIONS, GET, HEAD, POST, PUT, DELETE, TRACE, "
            "COPY, MOVE, MKCOL, PROPFIND, PROPPATCH, LOCK, "
            "UNLOCK, REPORT, ACL",
        )
        tx.response.naked = True
        return ""

    def propfind(self):
        """
        Return a status listing of addressbook/contacts.

        This resource is requsted twice with `Depth` headers of 0 and 1.
        0 is a request for the addressbook itself. 1 is a request for the
        addressbook itself and all contacts in the addressbook. Thus both
        the addressbook itself and each user have an etag.

        """
        # TODO refactor..
        web.header("DAV", "1, 2, 3, access-control, addressbook")

        depth = int(tx.request.headers["Depth"])
        etags = {"": tx.kv["carddav-lasttouch"]}
        if depth == 1:
            for identity in get_resources("identities"):
                etags[identity["-uuid"]] = identity.get(
                    "updated", identity["published"]
                ).timestamp()

        props = list(tx.request.body.iterchildren())[0]
        namespaces = set()
        responses = []

        for uuid, etag in etags.items():
            ok = []
            notfound = []
            for prop in props.iterchildren():
                # supported
                if prop.tag == "{DAV:}current-user-privilege-set":
                    ok.append(
                        """<current-user-privilege-set>
                                     <privilege>
                                         <all />
                                         <read />
                                         <write />
                                         <write-properties />
                                         <write-content />
                                     </privilege>
                                 </current-user-privilege-set>"""
                    )
                if prop.tag == "{DAV:}displayname":
                    ok.append("<displayname>carddav</displayname>")
                if prop.tag == "{DAV:}getetag":
                    ok.append(f'<getetag>"{etag}"</getetag>')
                if prop.tag == "{DAV:}owner":
                    ok.append("<owner>/</owner>")
                if prop.tag == "{DAV:}principal-URL":
                    ok.append(
                        """<principal-URL>
                                     <href>/identities</href>
                                 </principal-URL>"""
                    )
                if prop.tag == "{DAV:}principal-collection-set":
                    ok.append(
                        """<principal-collection-set>
                                     <href>/identities</href>
                                 </principal-collection-set>"""
                    )
                if prop.tag == "{DAV:}current-user-principal":
                    ok.append(
                        """<current-user-principal>
                                     <href>/identities</href>
                                 </current-user-principal>"""
                    )
                if prop.tag == "{DAV:}resourcetype":
                    namespaces.add("CR")
                    if uuid:
                        ok.append("<resourcetype />")
                    else:
                        ok.append(
                            """<resourcetype>
                                         <CR:addressbook />
                                         <collection />
                                     </resourcetype>"""
                        )
                if prop.tag == "{DAV:}supported-report-set":
                    ok.append(
                        """<supported-report-set>
                                     <supported-report>
                                         <report>principal-property-search</report>
                                     </supported-report>
                                     <supported-report>
                                         <report>sync-collection</report>
                                     </supported-report>
                                     <supported-report>
                                         <report>expand-property</report>
                                     </supported-report>
                                     <supported-report>
                                         <report>principal-search-property-set</report>
                                     </supported-report>
                                 </supported-report-set>"""
                    )
                if (
                    prop.tag == "{urn:ietf:params:xml:ns:carddav}"
                    "addressbook-home-set"
                ):
                    namespaces.add("CR")
                    ok.append(
                        """<CR:addressbook-home-set>
                                     <href>/identities</href>
                                 </CR:addressbook-home-set>"""
                    )
                if prop.tag == "{http://calendarserver.org/ns/}" "getctag":
                    namespaces.add("CS")
                    ok.append(f'<CS:getctag>"{etag}"</CS:getctag>')

                # conditionally supported
                if prop.tag == "{http://calendarserver.org/ns/}me-card":
                    namespaces.add("CS")
                    if uuid:
                        notfound.append("<CS:me-card />")
                    else:
                        ok.append(
                            f"""<CS:me-card>
                                      <href>/identities/{tx.owner["-uuid"]}.vcf</href>
                                      </CS:me-card>"""
                        )

                # not supported
                if prop.tag == "{DAV:}add-member":
                    notfound.append("<add-member />")
                if prop.tag == "{DAV:}quota-available-bytes":
                    notfound.append("<quota-available-bytes />")
                if prop.tag == "{DAV:}quota-used-bytes":
                    notfound.append("<quota-used-bytes />")
                if prop.tag == "{DAV:}resource-id":
                    notfound.append("<resource-id />")
                if prop.tag == "{DAV:}sync-token":
                    notfound.append("<sync-token />")
                if prop.tag == "{urn:ietf:params:xml:ns:carddav}" "directory-gateway":
                    namespaces.add("CR")
                    notfound.append("<CR:directory-gateway />")
                if prop.tag == "{urn:ietf:params:xml:ns:carddav}" "max-image-size":
                    namespaces.add("CR")
                    notfound.append("<CR:max-image-size />")
                if prop.tag == "{urn:ietf:params:xml:ns:carddav}" "max-resource-size":
                    namespaces.add("CR")
                    notfound.append("<CR:max-resource-size />")
                if prop.tag == "{http://calendarserver.org/ns/}" "email-address-set":
                    namespaces.add("CS")
                    notfound.append("<CS:email-address-set />")
                if prop.tag == "{http://calendarserver.org/ns/}" "push-transports":
                    namespaces.add("CS")
                    notfound.append("<CS:push-transports />")
                if prop.tag == "{http://calendarserver.org/ns/}" "pushkey":
                    namespaces.add("CS")
                    notfound.append("<CS:pushkey />")
                if prop.tag == "{http://me.com/_namespace/}" "bulk-requests":
                    namespaces.add("ME")
                    notfound.append("<ME:bulk-requests />")
            href = "/identities"
            if uuid:
                href += f"/{uuid}.vcf"
            responses.append((href, ok, notfound))
        tx.response.naked = True
        raise web.MultiStatus(view.carddav(namespaces, responses))

    def report(self):
        """Return a full listing for each requested identity."""
        etags = {}
        for identity in get_resources("identities"):
            etags[identity["-uuid"]] = identity.get(
                "updated", identity["published"]
            ).timestamp()
        children = list(tx.request.body.iterchildren())
        # XXX props = children[0]  # TODO soft-code prop responses
        responses = []
        for href in children[1:]:
            uuid = href.text.rpartition("/")[2].partition(".")[0]
            ok = [
                f'<getetag>"{etags[uuid]}"</getetag>',
                f"<CR:address-data>{generate_vcard(uuid)}</CR:address-data>",
            ]
            notfound = []
            responses.append((href.text, ok, notfound))
        tx.response.naked = True
        raise web.MultiStatus(view.carddav(set(["CR"]), responses))


@server.route(r"cards/{nickname}")
class Card:
    """A single card on file."""

    def get(self):
        # try:
        #     resource = tx.db.select("cache", where="url = ?",
        #                             vals=[f"https://{self.resource}"])[0]
        # except IndexError:
        #     resource = tx.db.select("cache", where="url = ?",
        #                             vals=[f"http://{self.resource}"])[0]
        return templates.card(tx.pub.get_card(self.nickname))


@server.route(r"cards/{nickname}.vcf")
class VCard:
    """
    A single card on file, represented as a vCard.

    `PUT` and `DELETE` methods provide CardDAV support.

    """

    def get(self):
        web.header("Content-Type", "text/vcard")
        return generate_vcard(self.nickname)

    def put(self):
        """
        add or update a identity

        """
        # TODO only add if "if-none-match" is found and identity isn't
        try:
            print("if-none-match", tx.request.headers.if_none_match)
        except AttributeError:
            pass
        else:
            try:
                identities.get_identity_by_uuid(self.card_id)
            except ResourceNotFound:
                pass
            else:
                raise web.Conflict("identity already exists")

        # TODO only update if "if-match" matches etag on hand
        try:
            request_etag = str(tx.request.headers.if_match).strip('"')
            print("if-match", request_etag)
        except AttributeError:
            pass
        else:
            identity = identities.get_identity_by_uuid(self.card_id)
            current_etag = identity.get("updated", identity["published"]).timestamp()
            print("current etag", current_etag)
            if request_etag != current_etag:
                raise web.Conflict("previous edit already exists")

        # TODO non-standard type-params (url) not handled by vobject

        card = vobject.readOne(tx.request.body.decode("utf-8"))

        name = card.fn.value.strip()

        extended = {}
        n = card.n.value

        def explode(key):
            item = getattr(n, key)
            if isinstance(item, list):
                extended[key] = ";".join(item)
            else:
                extended[key] = [item]

        explode("prefix")
        explode("given")
        explode("additional")
        explode("family")
        explode("suffix")

        # TODO identity_type = "identity"
        basic = {"name": name, "uuid": self.card_id}

        # TODO organizations = [o.value[0]
        # TODO                  for o in card.contents.get("org", [])]
        # TODO for organization in organizations:
        # TODO     if organization == name:
        # TODO         identity_type = "organization"

        # TODO telephones = []
        # TODO for tel in card.contents.get("tel", []):
        # TODO     telephones.append((tel.value, tel.params["TYPE"]))
        # TODO websites = []
        # TODO for url in card.contents.get("url", []):
        # TODO     type = url.params.get("TYPE", [])
        # TODO     for label in card.contents.get("x-ablabel"):
        # TODO         if label.group == url.group:
        # TODO             type.append(label.value)
        # TODO     print(url.value, type)
        # TODO     print()
        # TODO     websites.append((url.value, type))

        # photo = card.contents.get("photo")[0]
        # print()
        # print(photo)
        # print()
        # print(photo.group)
        # print(photo.params.get("ENCODING"))
        # print(photo.params.get("X-ABCROP-RECTANGLE"))
        # print(photo.params.get("TYPE", []))
        # print(len(photo.value))
        # print()
        # filepath = tempfile.mkstemp()[1]
        # with open(filepath, "wb") as fp:
        #     fp.write(photo.value)
        # photo_id = canopy.branches["images"].photos.upload(filepath)
        # extended["photos"] = [photo_id]

        try:
            details = identities.get_identity_by_uuid(self.card_id)
        except ResourceNotFound:
            print("NEW identity!")
            print(basic)
            print(extended)
            quick_draft("identity", basic, publish="Identity imported from iPhone.")
            # XXX details = create_identity(access="private", uid=self.card_id,
            # XXX                          **basic)
            # XXX details = update_identity(identifier=details["identifier"],
            # XXX                  telephones=telephones, websites=websites,
            # XXX                  **extended)
            print("CREATED")
        else:
            print("EXISTING identity!")
            print(details)
            print("UPDATED")
        # XXX     basic.update(extended)
        # XXX     details = update_identity(identifier=details["identifier"],
        # XXX                      telephones=telephones, websites=websites,
        # XXX                      **basic)
        identity = identities.get_identity_by_uuid(self.card_id)
        etag = identity.get("updated", identity["published"]).timestamp()
        web.header("ETag", f'"{etag}"')
        tx.response.naked = True
        raise web.Created("created identity", f"/identities/{self.card_id}.vcf")

    def delete(self):
        """
        delete a identity

        This method provides CardDAV support.

        """
        # delete_resource(...)
        tx.response.naked = True
        return f"""<?xml version="1.0"?>
                   <multistatus xmlns="DAV:">
                     <response>
                       <href>/identities/{self.card_id}.vcf</href>
                       <status>HTTP/1.1 200 OK</status>
                     </response>
                   </multistatus>"""


@server.route(r"rooms")
class Rooms:
    """All rooms on file."""

    def get(self):
        return templates.rooms(tx.pub.get_rooms(), templates.render_dict)


@server.route(r"syndication")
class Syndication:
    """."""

    def get(self):
        return templates.syndication()

    def post(self):
        destinations = web.form()
        if "twitter_username" in destinations:
            un = destinations.twitter_username
            # TODO pw = destinations.twitter_password
            # TODO sign in
            user_photo = ""  # TODO doc.qS(f"a[href=/{un}/photo] img").src
            destination = {
                "uid": f"//twitter.com/{un}",
                "name": f"{un} on Twitter",
                "service": {
                    "name": "Twitter",
                    "url": "//twitter.com",
                    "photo": "//abs.twimg.com/favicons/" "twitter.ico",
                },
                "user": {"name": un, "url": f"//twitter.com/{un}", "photo": user_photo},
            }
            tx.db.insert("syndication", destination=destination)
        if "github_username" in destinations:
            un = destinations.github_username
            # TODO token = destinations.github_token
            # TODO check the token
            user_photo = ""  # TODO doc.qS("img.avatar-user.width-full").src
            destination = {
                "uid": f"//github.com/{un}",
                "name": f"{un} on GitHub",
                "service": {
                    "name": "GitHub",
                    "url": "//github.com",
                    "photo": "//github.githubassets.com/" "favicons/favicon.png",
                },
                "user": {"name": un, "url": f"//github.com/{un}", "photo": user_photo},
            }
            tx.db.insert("syndication", destination=destination)


@server.route(r"media")
class MediaEndpoint:
    """."""

    def get(self):
        return templates.media(LocalClient().get_media())

    def post(self):
        media_dir = pathlib.Path(tx.host.name)
        media_dir.mkdir(exist_ok=True, parents=True)
        while True:
            mid = web.nbrandom(4)
            filename = media_dir / mid
            if not filename.exists():
                filename = web.form("file").file.save(filename)
                break
        if str(filename).endswith(".heic"):
            sh.convert(
                filename,
                "-set",
                "filename:base",
                "%[basename]",
                f"{media_dir}/%[filename:base].jpg",
            )
        sha256 = str(sh.sha256sum(filename)).split()[0]
        try:
            tx.db.insert("media", mid=mid, sha256=sha256, size=filename.stat().st_size)
        except tx.db.IntegrityError:
            mid = tx.db.select("media", where="sha256 = ?", vals=[sha256])[0]["mid"]
            filename.unlink()
        path = f"/pub/media/{mid}"
        raise web.Created(
            f"File can be found at <a href={path}>{path}</a>", location=path
        )


@server.route(r"media/{filename}")
class MediaFile:
    """."""

    def get(self):
        content_types = {
            (".jpg", ".jpeg"): "image/jpg",
            ".heic": "image/heic",
            ".png": "image/png",
            ".mp3": "audio/mpeg",
            ".mov": "video/quicktime",
            ".mp4": "video/mp4",
        }
        for suffix, content_type in content_types.items():
            if self.filename.endswith(suffix):
                web.header("Content-Type", content_type)
                break
        relative_path = f"{tx.host.name}/{self.filename}"
        if tx.host.server[0] == "gunicorn":
            with open(relative_path, "rb") as fp:
                return fp.read()
        else:  # assumes Nginx context
            web.header("X-Accel-Redirect", f"/X/{relative_path}")

    def delete(self):
        filepath = LocalClient().get_filepath(self.filename)
        tx.db.delete("media", where="mid = ?", vals=[filepath.stem])
        filepath.unlink()
        return "deleted"


@content.route(r"{year}/{month}/{day}/{seconds}(/{slug})?")
class Permalink:
    """An individual entry."""

    def get(self):
        resource = tx.pub.read(tx.request.uri.path)["resource"]
        if resource["visibility"] == "private" and not tx.user.session:
            raise web.Unauthorized(f"/auth?return_to={tx.request.uri.path}")
        # mentions = web.indie.webmention.get_mentions(str(tx.request.uri))
        return templates.entry(resource)  # , mentions)
