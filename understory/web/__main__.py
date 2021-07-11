"""Command line tools for the web."""

import json
import textwrap
from pprint import pprint

from understory import term, web

__all__ = ["main"]


main = term.application("web", web.__doc__)


@main.register()
class Serve:
    """Serve a web app."""

    def setup(self, add_arg):
        add_arg("app", help="name of web application")
        add_arg("port", help="port to serve")

    def run(self, stdin, log):
        web.serve(self.app, self.port)

        # from pprint import pprint
        # pprint(web.get_apps())
        # for pkg, apps in web.get_apps().items():
        #     for name, _, ns, obj in apps:
        #         if self.app == name:
        #             web.serve(ns, obj)
        #             return 0
        # return 1


@main.register()
class MF:
    """Get microformats."""

    def setup(self, add_arg):
        add_arg("uri", help="address of the resource to GET and parse for MF")

    def run(self, stdin, log):
        pprint(web.get(self.uri).mf2json)
        return 0


@main.register()
class Micropub:
    """A Micropub editor."""

    # TODO media upload

    def setup(self, add_arg):
        add_arg("endpoint", help="address of the Micropub endpoint")
        add_arg("--type", default="entry", help="post type")
        add_arg("--token", default=None, help="IndieAuth bearer token")
        add_arg("--channel", nargs="*", help="add to given channel(s)")

    def run(self, stdin, log):
        properties = json.loads(stdin.read())
        try:
            properties["channel"].extend(self.channel)
        except KeyError:
            if self.channel:
                properties["channel"] = self.channel
        location, links = web.micropub.send(
            properties, endpoint=self.endpoint, h=self.type, token=self.token
        )
        print("Location:", location)
        print("Links:", links)
        return 0


@main.register()
class Microsub:
    """A Microsub reader."""

    def setup(self, add_arg):
        add_arg("endpoint", help="address of the Microsub endpoint")

    def run(self, stdin, log):
        return 0


@main.register()
class Braidpub:
    """A Braid publisher."""

    def setup(self, add_arg):
        add_arg("uri", help="address of the resource to publish")
        add_arg("range", help="content-range of the update in JSON Range")

    def run(self, stdin, log):
        patch_body = stdin.read()
        web.put(
            self.uri,
            headers={"Patches": "1"},
            data=textwrap.dedent(
                f"""
            content-length: {len(patch_body)}
            content-range: {self.range}

            {patch_body}"""
            ),
        )
        return 0


@main.register()
class Braidsub:
    """A Braid subscriber."""

    def setup(self, add_arg):
        add_arg("uri", help="address of the resource to subscribe")

    def run(self, stdin, log):
        for version, parents, patches in web.subscribe(self.uri):
            if version:
                print("version:", version)
            if parents:
                print("parents:", parents)
            for patch_range, patch_body in patches:
                if patch_range:
                    print("range:", patch_range)
                print(patch_body)
                print()
            print()
        return 0
