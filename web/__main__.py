"""Command line tools for the web."""

import json
import pathlib

import clicks

import web

__all__ = ["main"]


main = clicks.application("web", web.__doc__)


@main.register()
class MF:
    """Get a resource and parse it for Microformats."""

    def setup(self, add_arg):
        add_arg("uri", help="address of the resource")

    def run(self, stdin, log):
        pprint(agent.get(self.uri).mf2json)
        return 0


@main.register()
class Apps:
    """Serve a web app."""

    def setup(self, add_arg):
        pass

    def run(self, stdin, log):
        for pkg, apps in web.get_apps().items():
            for name, _, ns, obj in apps:
                print(f"{name} {ns}:{obj[0]}")
        return 0


@main.register()
class Serve:
    """Serve a web app."""

    def setup(self, add_arg):
        add_arg("app", help="name of web application")
        add_arg("--port", help="port to serve on")
        add_arg("--socket", help="file socket to serve on")
        add_arg("--watch", default=".", help="directory to watch for changes")

    def run(self, stdin, log):
        import asyncio

        if self.port:
            asyncio.run(web.serve(self.app, port=self.port, watch_dir=self.watch))
        elif self.socket:
            asyncio.run(web.serve(self.app, socket=self.socket, watch_dir=self.watch))
        else:
            print("must provide a port or a socket")
            return 1
        return 0

        # from pprint import pprint
        # pprint(web.get_apps())
        # for pkg, apps in web.get_apps().items():
        #     for name, _, ns, obj in apps:
        #         if self.app == name:
        #             web.serve(ns, obj)
        #             return 0
        # return 1


@main.register()
class Config:
    """Config your environments."""

    def setup(self, add_arg):
        add_arg("provider", choices=("digitalocean",), help="hosting provider")
        add_arg("token", help="API access token")

    def run(self, stdin, log):
        with pathlib.Path("~/.understory").expanduser().open("w") as fp:
            json.dump({"provider": self.provider, "token": self.token}, fp)
        return 0


@main.register()
class Host:
    """Host a web app."""

    def setup(self, add_arg):
        ...
        # add_arg("app", help="name of web application")
        # add_arg("--port", help="port to serve on")
        # add_arg("--socket", help="file socket to serve on")
        # add_arg("--watch", default=".", help="directory to watch for changes")

    def run(self, stdin, log):
        return 0
