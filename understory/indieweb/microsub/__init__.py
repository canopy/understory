"""
Microsub server and client implementations.

> Microsub is a proposed standard for creating a new generation of social
> readers that decouples the management of subscriptions to feeds and the
> parsing/delivering content from the user interface and presentation of
> the content. [0]

[0]: https://indieweb.org/Microsub

"""

from . import client, server

__all__ = ["client", "server"]
