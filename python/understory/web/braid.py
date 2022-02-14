"""Braid support."""

import time

import jsonpatch
import requests
from gevent import spawn
from gevent.queue import Queue

from .framework.util import Headers, JSONEncoder, header, json, tx
from .response import OK, NoContent, Subscription

__all__ = ["publish", "subscribe", "braidify"]


def publish(url, patch_range, patch_body):
    """Publish a patch to a local or web resource using Braid."""
    if url.startswith("/"):
        tx.kv.db.publish(
            url, JSONEncoder().encode({"range": patch_range, "body": patch_body})
        )
    else:
        requests.put(url, json={"Patches": 1})  # TODO


def subscribe(url):
    """Subscribe to a web resource using Braid."""
    while True:
        try:
            buf = []
            sections = []
            version = None
            parents = None
            patchcount = 0
            patches = []
            in_snapshot = False
            in_patchset = False
            in_patch = False
            patch_range = None
            for chunk in requests.get(
                url, headers={"Subscribe": "keep-alive"}, stream=True, verify=False
            ):
                buf.extend(chunk.splitlines())
                while b"" in buf:
                    delimiter = buf.index(b"")
                    sections.append(b"\n".join(buf[:delimiter]))
                    buf = buf[delimiter + 1 :]
                while True:
                    try:
                        section = sections.pop(0)
                    except IndexError:
                        break
                    if in_snapshot:
                        section = section.replace(b"\n", b"")
                        yield version, parents, [(None, json.loads(section))]
                        version = None
                        in_snapshot = False
                    elif in_patchset:
                        if in_patch:
                            patchcount -= 1
                            section = section.replace(b"\n", b"")
                            patches.append((patch_range, json.loads(section)))
                            patch_range = None
                            if patchcount == 0:
                                yield version, parents, patches
                                version = None
                                patches = []
                                in_patchset = False
                                in_patch = False
                        else:
                            headers = Headers.from_lines(section.decode())
                            patch_range = headers["content-range"]
                            in_patch = True
                    else:
                        headers = Headers.from_lines(section.decode())
                        version = headers.get("version")
                        parents = headers.get("parents")
                        patchcount = int(headers.get("patches", 0))
                        if patchcount:
                            in_patchset = True
                        else:
                            in_snapshot = True
        except requests.exceptions.ChunkedEncodingError as err:
            print("---")
            print(err)
            print("connection lost. reconnecting..")
            print("---")


def multi_subscribe(path, *urls):
    """Yield patches from multiple subscriptions."""
    queue = Queue()

    def producer(url):
        def _producer():
            for patch in subscribe(url):
                queue.put_nowait(patch)
            queue.put_nowait("COMPLETED")

        return _producer

    for url in urls:
        spawn(producer(url))
    completed = 0
    while True:
        patch = queue.get(timeout=5)
        if patch == "COMPLETED":
            completed += 1
            if completed == len(urls):
                break
            continue
        tx.kv.db.publish(path, patch)
        # XXX yield patch + b"\n"


def braidify(handler, app):
    """Handle Braid Pub/Sub."""
    path = f"/{tx.request.uri.path}"
    method = tx.request.method
    headers = tx.request.headers
    controller = tx.request.controller
    if method == "OPTIONS":  # allow CORS FIXME secure with IndieAuth?
        header("Access-Control-Allow-Origin", "*")
        header("Access-Control-Allow-Methods", "GET,PUT")
        header("Access-Control-Allow-Headers", "credentials,subscribe,patches,client")
        header("Vary", "Origin")
        raise NoContent()
    if method == "GET":
        if "application/json" in str(tx.request.headers.get("accept")):
            try:
                resource = tx.db.select("resources", where="path = ?", vals=[path])[0]
            except IndexError:
                pass  # not a braided resource
            else:
                raise OK(JSONEncoder().encode(dict(resource["resource"])))
        elif headers.get("Subscribe") == "keep-alive":
            header("Access-Control-Allow-Origin", "*")
            header("Subscribe", "keep-alive")
            header("Content-Type", "application/json")
            header("X-Accel-Buffering", "no")
            try:
                subscription = controller._subscribe()
            except AttributeError:
                subscription = Braid(path)
            tx.response.naked = True
            raise Subscription(subscription)
    if method == "PUT" and headers.get("Patches"):
        # TODO handle multiple patches
        print(tx.request.body)
        patch_range, patch_body = parse_patch(tx.request.body)
        resource = tx.db.select("resources", where="url = ?", vals=[path])[0][
            "resource"
        ]
        if patch_range.endswith("-"):  # TODO FIXME
            op = "add"
        else:
            op = "replace"
        patch = {"op": op, "path": patch_range, "value": patch_body}
        jsonpatch.apply_patch(resource, [patch], in_place=True)
        tx.db.update("resources", resource=resource, where="url = ?", vals=[path])
        publish(path, patch_range, json.loads(patch_body))
        header("Access-Control-Allow-Origin", "*")
        header("Patches", "OK")
        raise OK(b"")
    yield


def parse_patch(patch, delimiter):
    """Parse a single patch from a GET or a PUT."""
    raw_headers, _, patch_body = patch.partition(delimiter)
    patch_headers = Headers.from_lines(raw_headers.decode())
    # TODO version = patch_headers.get("version")
    # TODO parents = patch_headers.get("parents")
    # TODO merge_type = patch_headers.get("merge-type")
    try:
        patch_range = str(patch_headers["content-range"]).partition("=")[2]
    except KeyError:
        patch_range = None  # snapshot
    print(patch_body)
    return patch_range, json.loads(patch_body)


class Braid:
    """A Braid subscription."""

    def __init__(self, path):
        """Create Redis subscription to resource at given path."""
        self.p = tx.kv.pubsub(ignore_subscribe_messages=True)
        self.p.subscribe(path)

    def __next__(self):
        """Serve patches to client when received from Redis subscription."""
        while True:
            message = self.p.get_message()
            if message is None:
                time.sleep(0.001)
                continue
            patch = json.loads(message["data"])
            body = JSONEncoder().encode(patch["body"])
            return bytes(
                f"Content-Length: {len(body)}\n"
                f"Content-Range: json={patch['range']}\n"
                f"\n"
                f"{body}\n"
                f"\n",
                "utf-8",
            )

    def __iter__(self):  # TODO XXX use iter() on Braid object above?
        """Identify and function as an iterator."""
        return self
