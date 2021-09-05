"""
WebSub publisher and subscriber implementations.

> WebSub provides a common mechanism for communication between publishers
> of any kind of Web content and their subscribers, based on HTTP web hooks.
> Subscription requests are relayed through hubs, which validate and verify
> the request. Hubs then distribute new and updated content to subscribers
> when it becomes available. WebSub was previously known as PubSubHubbub. [0]

[0]: https://w3.org/TR/websub

"""

from . import publisher, subscriber

__all__ = ["publisher", "subscriber"]
