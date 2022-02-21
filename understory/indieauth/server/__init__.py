"""IndieAuth server."""

from understory import web
from understory.web import tx

from ..util import generate_challenge

__all__ = ["app"]

app = web.application(
    __name__,
    prefix="auth",
    args={"client_id": r"[\w/.]+"},
    model={
        "auths": {
            "auth_id": "TEXT",
            "initiated": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "revoked": "DATETIME",
            "code": "TEXT",
            "client_id": "TEXT",
            "client_name": "TEXT",
            "code_challenge": "TEXT",
            "code_challenge_method": "TEXT",
            "redirect_uri": "TEXT",
            "response": "JSON",
            "token": "TEXT",
        },
    },
)

supported_scopes = (
    "create",
    "draft",
    "update",
    "delete",
    "media",
    "profile",
    "email",
)


def initiate_auth():
    """
    Begin the authorization and return a three-tuple of client, developer and scope(s).

    Should be called from the GET handler for the Authorization Endpoint.

    """
    form = web.form("response_type", "client_id", "redirect_uri", "state", scope="")
    if form.response_type not in ("code", "id"):  # NOTE `id` for backcompat
        raise web.BadRequest('`response_type` must be "code".')
    client, developer = _discover_client(form.client_id)
    tx.user.session.update(
        client_id=form.client_id,
        client_name=client["name"],
        redirect_uri=form.redirect_uri,
        state=form.state,
    )
    if "code_challenge" in form and "code_challenge_method" in form:
        tx.user.session.update(
            code_challenge=form.code_challenge,
            code_challenge_method=form.code_challenge_method,
        )
    return client, developer, form.scope.split()


def _discover_client(client_id: web.uri):
    """Discover `client_id` and return details of the client and its developer."""
    client = {"name": None, "url": web.uri(client_id).normalized}
    developer = None
    if client["url"].startswith("https://addons.mozilla.org"):
        _, resource = web.tx.cache[client_id]
        try:
            heading = resource.dom.select("h1.AddonTitle")[0]
        except IndexError:
            pass
        else:
            client["name"] = heading.text.partition(" by ")[0]
            developer_link = heading.select("a")[0]
            developer_id = developer_link.href.rstrip("/").rpartition("/")[2]
            developer = {
                "name": developer_link.text,
                "url": f"https://addons.mozilla.org/user/{developer_id}",
            }
    else:
        mfs = web.mf.parse(url=client["url"])
        for item in mfs["items"]:
            if "h-app" in item["type"]:
                properties = item["properties"]
                client["name"] = properties["name"][0]
                break
            developer = {"name": "NAME", "url": "URL"}  # TODO
    return client, developer


def consent(scopes):
    """Complete the authorization and redirect to client's `redirect_uri`."""
    redirect_uri = web.uri(tx.user.session["redirect_uri"])
    redirect_uri["code"] = tx.auth_server.create_auth(
        tx.user.session["code_challenge"],
        tx.user.session["code_challenge_method"],
        tx.user.session["client_id"],
        tx.user.session["client_name"],
        tx.user.session["redirect_uri"],
        scopes,
    )
    redirect_uri["state"] = tx.user.session["state"]
    raise web.Found(redirect_uri)


def redeem_authorization_code(
    flow: str, me: web.uri, name: str = None, email: str = None, photo: web.uri = None
) -> dict:
    """
    Redeem an authorization code with given `flow` and return a profile and/or a token.

    `flow` can be one of ['profile'][0] or ['token'][1].

    [0]: https://indieauth.spec.indieweb.org/#profile-url-response
    [1]: https://indieauth.spec.indieweb.org/#access-token-response

    """
    form = web.form(
        "code", "client_id", "redirect_uri", grant_type="authorization_code"
    )
    # TODO verify authenticity
    # TODO grant_type=refresh_token
    if form.grant_type not in ("authorization_code", "refresh_token"):
        raise web.Forbidden(f"`grant_type` {form.grant_type} not supported")
    auth = tx.auth_server.get_auth_from_code(form.code)
    if form.client_id != auth["client_id"]:
        raise web.BadRequest("`client_id` does not match original request")
    if form.redirect_uri != auth["redirect_uri"]:
        raise web.BadRequest("`redirect_uri` does not match original request")
    if "code_verifier" in form:
        if not auth["code_challenge"]:
            raise web.BadRequest("`code_verifier` without a `code_challenge`")
        if auth["code_challenge"] != generate_challenge(form.code_verifier):
            raise web.Forbidden("code mismatch")
    elif auth["code_challenge"]:
        raise web.BadRequest("`code_challenge` without `code_verifier`")
    response = auth["response"]
    if flow == "token":
        if not response["scope"]:
            raise web.BadRequest("Access Token request requires a scope")
        response.update(
            token_type="Bearer",
            access_token=f"secret-token:{web.nbrandom(24)}",
        )
    response["me"] = me
    if "profile" in response["scope"]:
        response["profile"] = {"url": me, "name": name, "photo": photo}
        if "email" in response["scope"] and email:
            response["profile"]["email"] = email
    tx.auth_server.update_auth(response, auth["code"])
    web.header("Content-Type", "application/json")
    return response


def revoke_auth(token):
    tx.auth_server.revoke_token(token)
    raise web.OK("revoked")


@app.wrap
def connect_model(handler, main_app):
    """Connect the model to this transaction's database."""
    tx.auth_server = app.model(tx.db)
    yield


@app.wrap
def linkify_head(handler, main_app):
    """Ensure server links are in head of root document."""
    yield
    if tx.request.uri.path == "":
        web.add_rel_links(
            authorization_endpoint="/auth",
            token_endpoint="/auth/tokens",
            ticket_endpoint="/auth/tickets",
        )


def _redeem_authorization_code(flow):
    return redeem_authorization_code(
        flow,
        tx.origin,
        tx.host.owner["name"][0],
        tx.host.owner.get("email", [None])[0],
        tx.host.owner.get("photo", [None])[0],
    )


@app.control(r"")
class AuthorizationEndpoint:
    """Identity and resource authorization."""

    def get(self):
        """Return a consent screen for a third-party site sign-in."""
        if not tx.user.is_owner:  # TODO FIXME
            raise web.OK(app.view.root(tx.host.owner, tx.auth_server.get_clients()))
        try:
            client, developer, scopes = initiate_auth()
        except web.BadRequest:
            return app.view.authorizations(
                tx.auth_server.get_clients(),
                tx.auth_server.get_active(),
                tx.auth_server.get_revoked(),
            )
        return app.view.consent(client, developer, scopes, supported_scopes)

    def post(self):
        """Handle "Profile URL" flow response."""
        return _redeem_authorization_code("profile")


@app.control(r"consent")
class AuthorizationConsent:
    """The authorization consent screen."""

    def post(self):
        """Handle consent screen action."""
        form = web.form("action", scopes=[])
        if form.action == "cancel":
            raise web.SeeOther(tx.user.session["redirect_uri"])
        consent(form.scopes)


@app.control(r"tokens")
class TokenEndpoint:
    """Your token endpoint."""

    def get(self):
        """Return a list of tokens to owner otherwise a form to submit a code."""
        # TODO move to library?
        try:
            auth = tx.auth_server.get_auth_from_token(
                str(tx.request.headers["authorization"])
            )
        except IndexError:
            raise web.Forbidden("token could not be found")
        web.header("Content-Type", "application/json")
        return {
            "me": auth["response"]["me"],
            "client_id": auth["client_id"],
            "scope": " ".join(auth["response"]["scope"]),
        }

    def post(self):
        """Handle "Access Token" flow response or revoke an existing access token."""
        # TODO token introspection
        # TODO token verification
        try:
            form = web.form("action", "token")
        except web.BadRequest:
            return _redeem_authorization_code("token")
        if form.action == "revoke":
            revoke_auth(form.token)


@app.control(r"tickets")
class TicketEndpoint:
    """Your ticket endpoint."""

    def get(self):
        """Return a list of tickets to owner otherwise a form to submit a ticket."""


@app.control(r"clients")
class Clients:
    """Third-party clients you've used."""

    def get(self):
        """Return a list of clients."""
        return app.view.clients(tx.auth_server.get_clients())


@app.control(r"clients/{client_id}")
class Client:
    """A third-party client."""

    def get(self, client_id):
        """Return given client's authorizations."""
        return app.view.client(tx.auth_server.get_client_auths(client_id))


@app.model.control
def get_clients(db):
    """Return a unique list of clients."""
    return db.select(
        "auths", order="client_name ASC", what="DISTINCT client_id, client_name"
    )


@app.model.control
def create_auth(
    db,
    code_challenge: str,
    code_challenge_method: str,
    client_id: str,
    client_name: str,
    redirect_uri: str,
    scopes: list,
):
    """Create an authorization."""
    code = web.nbrandom(32)
    while True:
        try:
            db.insert(
                "auths",
                auth_id=web.nbrandom(4),
                code=code,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method,
                client_id=client_id,
                client_name=client_name,
                redirect_uri=redirect_uri,
                response={"scope": scopes},
            )
        except db.IntegrityError:
            continue
        break
    return code


@app.model.control
def get_auth_from_code(db, code: str):
    """Return authorization with given `code`."""
    return db.select("auths", where="code = ?", vals=[code])[0]


@app.model.control
def get_auth_from_token(db, token: str):
    """Return authorization with given `token`."""
    return db.select(
        "auths",
        where="json_extract(auths.response, '$.access_token') = ?",
        vals=[token],
    )[0]


@app.model.control
def update_auth(db, response: dict, code: str):
    """Update `response` of authorization with given `code`."""
    db.update("auths", response=response, where="code = ?", vals=[code])


@app.model.control
def get_client_auths(db, client_id: web.uri):
    """Return all authorizations for given `client_id`."""
    return db.select(
        "auths",
        where="client_id = ?",
        vals=[f"https://{client_id}"],
        order="redirect_uri, initiated DESC",
    )


@app.model.control
def get_active(db):
    """Return all active authorizations."""
    return db.select("auths", where="revoked is null")


@app.model.control
def get_revoked(db):
    """Return all revoked authorizations."""
    return db.select("auths", where="revoked not null")


@app.model.control
def revoke_token(db, token: str):
    """Revoke authorization with given `token`."""
    db.update(
        "auths",
        revoked=web.utcnow(),
        where="json_extract(response, '$.access_token') = ?",
        vals=[token],
    )
