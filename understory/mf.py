"""A Microformats parser and utilities."""

import datetime
import json

import mf2py
import mf2util as util
import requests
from mf2util import interpret_comment, interpret_event, interpret_feed

from understory import uri

__all__ = [
    "parse",
    "util",
    "interpret_feed",
    "interpret_entry",
    "interpret_event",
    "interpret_comment",
]


stable = {
    "adr": [
        "p-street-address",
        "p-extended-address",
        "p-post-office-box",
        "p-locality",
        "p-region",
        "p-postal-code",
        "p-country-name",
        "p-label",
        "p/u-geo",
        "p-latitude",
        "p-longitude",
        "p-altitude",
    ],
    "card": [
        "p-name",
        "p-honorific-prefix",
        "p-given-name",
        "p-additional-name",
        "p-family-name",
        "p-sort-string",
        "p-honorific-suffix",
        "p-nickname",
        "u-email",
        "u-logo",
        "u-photo",
        "u-url",
        "u-uid",
        "p-category",
        "p/h-adr",
        "p-post-office-box",
        "p-extended-address",
        "p-street-address",
        "p-locality",
        "p-region",
        "p-postal-code",
        "p-country-name",
        "p-label",
        "p/u/h-geo",
        "p-latitude",
        "p-longitude",
        "p-altitude",
        "p-tel",
        "p-note",
        "dt-bday",
        "u-key",
        "p-org",
        "p-job-title",
        "p-role",
        "u-impp",
        "p-sex",
        "p-gender-identity",
        "dt-anniversary",
    ],
    "entry": [
        "p-name",
        "p-summary",
        "e-content",
        "dt-published",
        "dt-updated",
        "p-author",
        "p-category",
        "u-url",
        "u-uid",
        "p-location",
        "u-syndication",
        "u-in-reply-to",
        "p-rsvp",
        "u-like-of",
        "u-repost-of",
    ],
    "event": [
        "p-name",
        "p-summary",
        "dt-start",
        "dt-end",
        "dt-duration",
        "e-content",
        "u-url",
        "p-category",
        "p-location(card/adr/geo)",
        "[p-attendee]",
    ],
    "feed": ["p-name", "p-author(card)", "u-url", "u-photo"],
    "geo": ["p-latitude", "p-longitude", "p-altitude"],
    "item": ["p-name", "u-url", "u-photo"],
    "product": [
        "p-name",
        "u-photo",
        "p-brand(card)",
        "p-category",
        "e-content",
        "u-url",
        "u-identifier",
        "p-review(review)",
        "p-price",
    ],
    "recipe": [
        "p-name",
        "p-ingredient",
        "p-yield",
        "e-instructions",
        "dt-duration",
        "u-photo",
        "p-summary",
        "p-author(card)",
        "dt-published",
        "p-nutrition",
        "p-category",
    ],
    "resume": [
        "p-name",
        "p-summary",
        "p-contact",
        "p-education(event+card)",
        "p-experience(event+card)",
        "p-skill",
        "p-affiliation",
    ],
    "review": [
        "p-name ",
        "p-item(card/event/adr/geo/product/item)",
        "p-author(card)",
        "dt-published",
        "p-rating",
        "p-best",
        "p-worst",
        "e-content",
        "p-category",
        "u-url",
    ],
    "review-aggregate": [
        "p-item(card/event/adr/geo/product/item)",
        "p-average",
        "p-best",
        "p-worst",
        "p-count",
        "p-votes",
        "p-name",
    ],
}
draft = {"app": ["p-name", "u-url", "u-logo", "u-photo"]}


def parse(doc=None, url=None):
    """
    Return a dictionary containing the mf2json of the HTML document `doc`.

    You may provide a document, a URL or both. When both are provided
    the URL is used as the document's base href.

    """
    url = str(url)
    if doc is None:
        try:
            response = requests.get(url)
        except requests.exceptions.SSLError:
            response = requests.get(url, verify=False)
        doc = response.text
    data = mf2py.parse(doc, url)
    data.pop("debug")
    return data


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uri.URI):
            return str(obj)
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


def representative_card(parsed, source_url):
    """
    Find the representative card for a URL.

    http://microformats.org/wiki/representative-h-card-parsing

    :param dict parsed: an mf2 parsed dict
    :param str source_url: the source of the parsed document.
    :return: the representative h-card if one is found

    """
    # FIXME NOTE mf2py needs plain mf2json
    parsed = json.loads(JSONEncoder().encode(parsed))  # FIXME

    source_url = uri.parse(source_url).minimized

    def get_normal(card, prop):
        """Return a list of normalized URLs for an card's prop (uid/url)."""
        urls = []
        for url in card["properties"].get(prop, []):
            try:
                urls.append(uri.parse(url).minimized)
            except ValueError:
                pass
        return urls

    cards = [
        h
        for h in util.find_all_entries(parsed, ["h-card"], include_properties=True)
        if (
            h["properties"].get("name", [""])[0]
            or h["properties"].get("nickname", [""])[0]
        )
    ]

    # uid and url both match source_url
    for card in cards:
        if source_url in get_normal(card, "uid") and source_url in get_normal(
            card, "url"
        ):
            return card["properties"]

    # url that is also a rel=me
    for card in cards:
        rel_mes = set()
        for rel_me in parsed.get("rels", {}).get("me", []):
            try:
                rel_me = uri.parse(rel_me)
            except ValueError:
                continue
            if isinstance(rel_me, (uri.HTTPURI, uri.HTTPSURI)):
                rel_mes.add(rel_me.minimized)
        if any(url in rel_mes for url in get_normal(card, "url")):
            return card["properties"]

    # single card with matching url
    found = []
    count = 0
    for card in cards:
        # if source_url in card['properties'].get('url', []):
        for card_url in get_normal(card, "url"):
            if card_url.rstrip("/") == source_url:
                found.append(card)
                count += 1
    if count:
        return found[0]["properties"]


util.representative_hcard = representative_card


def interpret_entry(
    parsed,
    source_url,
    base_href=None,
    hentry=None,
    use_rel_syndication=True,
    want_json=False,
    fetch_mf2_func=None,
):
    """
    Given a document containing an h-entry, return a dictionary.

        {'type': 'entry',
         'url': permalink of the document (may be different than source_url),
         'published': datetime or date,
         'updated': datetime or date,
         'name': title of the entry,
         'content': body of entry (contains HTML),
         'author': {
          'name': author name,
          'url': author url,
          'photo': author photo
         },
         'syndication': [
           'syndication url',
           ...
         ],
         'in-reply-to': [...],
         'like-of': [...],
         'repost-of': [...]}

    :param dict parsed: the result of parsing a document containing mf2 markup
    :param str source_url: the URL of the parsed document, used by the
      authorship algorithm
    :param str base_href: (optional) the href value of the base tag
    :param dict hentry: (optional) the item in the above document
      representing the h-entry. if provided, we can avoid a redundant
      call to find_first_entry
    :param boolean use_rel_syndication: (optional, default True) Whether
      to include rel=syndication in the list of syndication sources. Sometimes
      useful to set this to False when parsing h-feeds that erroneously include
      rel=syndication on each entry.
    :param boolean want_json: (optional, default False) if true, the result
      will be pure json with datetimes as strings instead of python objects
    :param callable fetch_mf2_func: (optional) function to fetch mf2 parsed
      output for a given URL.
    :return: a dict with some or all of the described properties

    """
    # find the h-entry if it wasn't provided
    if not hentry:
        hentry = util.find_first_entry(parsed, ["h-entry"])
        if not hentry:
            return {}

    result = _interpret_common_properties(
        parsed,
        source_url,
        base_href,
        hentry,
        use_rel_syndication,
        want_json,
        fetch_mf2_func,
    )
    if "h-cite" in hentry.get("type", []):
        result["type"] = "cite"
    else:
        result["type"] = "entry"

    # NOTE patch start
    if "category" in hentry["properties"]:
        result["category"] = hentry["properties"]["category"]
    if "pubkey" in hentry["properties"]:
        result["pubkey"] = hentry["properties"]["pubkey"]
    if "vote" in hentry["properties"]:
        result["vote"] = hentry["properties"]["vote"]
    # NOTE patch end

    title = util.get_plain_text(hentry["properties"].get("name"))
    if title and util.is_name_a_title(title, result.get("content-plain")):
        result["name"] = title

    for prop in (
        "in-reply-to",
        "like-of",
        "repost-of",
        "bookmark-of",
        "vote-on",
        "comment",
        "like",
        "repost",
    ):  # NOTE added vote-on
        for url_val in hentry["properties"].get(prop, []):
            if isinstance(url_val, dict):
                result.setdefault(prop, []).append(
                    util.interpret(
                        parsed,
                        source_url,
                        base_href,
                        url_val,
                        use_rel_syndication=False,
                        want_json=want_json,
                        fetch_mf2_func=fetch_mf2_func,
                    )
                )
            else:
                result.setdefault(prop, []).append(
                    {
                        "url": url_val,
                    }
                )

    return result


util.interpret_entry = interpret_entry


def _interpret_common_properties(
    parsed,
    source_url,
    base_href,
    hentry,
    use_rel_syndication,
    want_json,
    fetch_mf2_func,
):
    result = {}
    props = hentry["properties"]

    for prop in ("url", "uid", "photo", "featured" "logo"):
        value = util.get_plain_text(props.get(prop))
        if value:
            result[prop] = value

    for prop in ("start", "end", "published", "updated", "deleted"):
        date_str = util.get_plain_text(props.get(prop))
        if date_str:
            if want_json:
                result[prop] = date_str
            else:
                result[prop + "-str"] = date_str
                try:
                    date = util.parse_datetime(date_str)
                    if date:
                        result[prop] = date
                except ValueError:
                    util.logging.warn("Failed to parse datetime %s", date_str)

    author = util.find_author(parsed, source_url, hentry, fetch_mf2_func)
    if author:
        result["author"] = author

    content_prop = props.get("content")
    content_value = None
    if content_prop:
        if isinstance(content_prop[0], dict):
            content_html = content_prop[0].get("html", "").strip()
            content_value = content_prop[0].get("value", "").strip()
        else:
            content_value = content_html = content_prop[0]
        result["content"] = util.convert_relative_paths_to_absolute(
            source_url, base_href, content_html
        )
        result["content-plain"] = content_value

    summary_prop = props.get("summary")
    if summary_prop:
        if isinstance(summary_prop[0], dict):
            result["summary"] = summary_prop[0]["value"]
        else:
            result["summary"] = summary_prop[0]

    # Collect location objects, then follow this algorithm to consolidate
    # their properties:
    # //indieweb.org/location#How_to_determine_the_location_of_a_microformat
    location_stack = [props]

    for prop in "location", "adr":
        vals = props.get(prop)
        if vals:
            if isinstance(vals[0], util.string_type):
                location_stack.append({"name": vals})
            else:
                location_stack.append(vals[0].get("properties", {}))

    geo = props.get("geo")
    if geo:
        if isinstance(geo[0], dict):
            location_stack.append(geo[0].get("properties", {}))
        else:
            if geo[0].startswith("geo:"):
                # a geo: URL. try to parse it.
                # //tools.ietf.org/html/rfc5870
                parts = geo[0][len("geo:") :].split(";")[0].split(",")
                if len(parts) >= 2:
                    location_stack.append(
                        {
                            "latitude": [parts[0]],
                            "longitude": [parts[1]],
                            "altitude": [parts[2]] if len(parts) >= 3 else [],
                        }
                    )

    for prop in util.LOCATION_PROPERTIES:
        for obj in location_stack:
            if obj and obj.get(prop) and not (obj == props and prop == "name"):
                result.setdefault("location", {})[prop] = obj[prop][0]

    if use_rel_syndication:
        result["syndication"] = list(
            set(
                parsed.get("rels", {}).get("syndication", [])
                + hentry["properties"].get("syndication", [])
            )
        )
    else:
        result["syndication"] = hentry["properties"].get("syndication", [])

    # TODO patch start
    checkin_prop = props.get("checkin")
    if checkin_prop:
        if isinstance(checkin_prop[0], dict):
            props = checkin_prop[0]["properties"]
            result["checkin"] = {"name": props["name"][0]}
            try:
                result.update(
                    {
                        "latitude": props["latitude"][0],
                        "longitude": props["longitude"][0],
                    }
                )
            except KeyError:
                pass
        else:
            result["checkin"] = checkin_prop[0]

    categories = props.get("category")
    if categories:
        result["category"] = categories
    # TODO patch end

    return result


util._interpret_common_properties = _interpret_common_properties
