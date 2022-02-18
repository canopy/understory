""""""

import json

from understory import micropub, term

__all__ = ["main"]

main = term.application("micropub", micropub.__doc__)


@main.register()
class Micropub:
    """A Micropub client."""

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
        location, links = micropub.client.create_post(
            properties, endpoint=self.endpoint, h=self.type, token=self.token
        )
        print("Location:", location)
        if links:
            print("Links:", links)
        return 0


if __name__ == "__main__":
    main()
