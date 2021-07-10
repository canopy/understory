"""
IndieAuth server and client apps.

> IndieAuth is an identity layer on top of OAuth 2.0 [RFC6749], primarily
> used to obtain an OAuth 2.0 Bearer Token [RFC6750] for use by [Micropub]
> clients. End-Users and Clients are all represented by URLs. IndieAuth
> enables Clients to verify the identity of an End-User, as well as to
> obtain an access token that can be used to access resources under the
> control of the End-User. [0]

[0]: https://indieauth.spec.indieweb.org/

"""

from . import client, server
