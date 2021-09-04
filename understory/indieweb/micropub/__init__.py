"""
Micropub server and client implementations.

> The Micropub protocol is used to create, update and delete posts on
> one's own domain using third-party clients. Web apps and native apps
> (e.g. iPhone, Android) can use Micropub to post and edit articles,
> short notes, comments, likes, photos, events or other kinds of posts
> on your own website. [0]

[0]: https://micropub.spec.indieweb.org

"""

from . import client, server

__all__ = ["client", "server"]
