"""An IndieAuth server."""

from __future__ import annotations

import base64
import hashlib

from understory import web
from understory.web import tx

app = web.application(
    __name__,
    prefix="auth",
    args={
        "client_id": r"[\w/.]+",
    },
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
        "credentials": {
            "created": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "salt": "BLOB",
            "scrypt_hash": "BLOB",
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


def get_card() -> dict | None:
    """Return a dict of owner details or None if no known owner."""
    try:
        card = tx.db.select("resources", where="permalink = ?", vals=["/"])[0][
            "resource"
        ]
    except IndexError:
        card = None
    return card


def get_resume() -> dict | None:
    """Return a dict of owner's resume details or None if nothing exists yet."""
    try:
        resume = tx.db.select("identities")[0]["resume"]
    except IndexError:
        resume = None
    return resume


def init_owner(name):
    """Initialize owner of the requested domain."""
    salt, scrypt_hash, passphrase = web.generate_passphrase()
    tx.db.insert("credentials", salt=salt, scrypt_hash=scrypt_hash)
    version = web.nbrandom(3)
    uid = str(web.uri(tx.origin))
    tx.db.insert(
        "resources",
        permalink="/",
        version=version,
        resource={
            "name": [name],
            "type": ["card"],
            "url": [uid],
            "uid": [uid],
            "visibility": ["public"],
        },
    )
    tx.user.session = {"uid": uid, "name": name}
    tx.user.is_owner = True
    tx.host.owner = get_card()
    return uid, passphrase


def discover_client(client_id):
    """Return the client name and author if provided."""
    # TODO FIXME unapply_dns was here..
    client = {"name": None, "url": web.uri(client_id).normalized}
    author = None
    if client["url"].startswith("https://addons.mozilla.org"):
        try:
            heading = tx.cache[client_id].dom.select("h1.AddonTitle")[0]
        except IndexError:
            pass
        else:
            client["name"] = heading.text.partition(" by ")[0]
            author_link = heading.select("a")[0]
            author_id = author_link.href.rstrip("/").rpartition("/")[2]
            author = {
                "name": author_link.text,
                "url": f"https://addons.mozilla.org/user/{author_id}",
            }
    else:
        mfs = web.mf.parse(url=client["url"])
        for item in mfs["items"]:
            if "h-app" in item["type"]:
                properties = item["properties"]
                client = {"name": properties["name"][0], "url": properties["url"][0]}
                break
            author = {"name": "NAME", "url": "URL"}  # TODO
    return client, author


def get_clients():
    return list(
        tx.db.select(
            "auths", order="client_name ASC", what="DISTINCT client_id, client_name"
        )
    )


def get_active():
    return list(tx.db.select("auths", where="revoked is null"))


def get_revoked():
    return list(tx.db.select("auths", where="revoked not null"))


def wrap(handler, mainapp):
    """Ensure server links are in head of root document."""
    tx.host.owner = get_card()
    if not tx.host.owner:
        web.header("Content-Type", "text/html")
        if tx.request.method == "GET":
            raise web.OK(app.view.claim())
        elif tx.request.method == "POST":
            uid, passphrase = init_owner(web.form("name").name)
            raise web.Created(app.view.claimed(uid, " ".join(passphrase)), uid)
    try:
        tx.user.is_owner = tx.user.session["uid"] == tx.host.owner["uid"][0]
    except (AttributeError, KeyError, IndexError):
        tx.user.is_owner = False
    # passthrough = (
    #     "auth",
    #     "auth/sign-in",
    #     "auth/claim",
    #     "auth/sign-ins/token",
    #     "auth/visitors/sign-in",
    #     "auth/visitors/authorize",
    # )
    # if (
    #     tx.request.uri.path.startswith(("auth", "pub", "sub"))
    #     and tx.request.uri.path not in passthrough
    #     and not tx.user.is_owner
    #     and not tx.request.headers.get("Authorization")
    # ):  # TODO validate token
    #     raise web.Unauthorized(app.view.unauthorized())
    yield
    if tx.request.uri.path == "" and tx.response.body:
        doc = web.parse(tx.response.body)
        base = f"{tx.origin}/auth"
        try:
            head = doc.select("head")[0]
        except IndexError:
            pass
        else:
            head.append(
                f"<link rel=authorization_endpoint href={base}>",
                f"<link rel=token_endpoint href={base}/tokens>",
                f"<link rel=ticket_endpoint href={base}/tickets>",
            )
            tx.response.body = doc.html
        web.header("Link", f'<{base}>; rel="authorization_endpoint"', add=True)
        web.header("Link", f'<{base}/tokens>; rel="token_endpoint"', add=True)
        web.header("Link", f'<{base}/tickets>; rel="ticket_endpoint"', add=True)


@app.control(r"")
class AuthorizationEndpoint:
    """IndieAuth server `authorization endpoint`."""

    def get(self):
        """Return a consent screen for a third-party site sign-in."""
        if not tx.user.is_owner:
            raise web.OK(app.view.root(get_card(), get_clients()))
        try:
            form = web.form(
                "response_type",
                "client_id",
                "redirect_uri",
                "state",
                scope=[],
            )
        except web.BadRequest:
            return app.view.authorizations(get_clients(), get_active(), get_revoked())
        if form.response_type not in (
            "code",
            "id",  # XXX treat the same as "code" for backwards-compatibility
        ):
            raise web.BadRequest('`response_type` must be "code".')
        client, developer = discover_client(form.client_id)
        tx.user.session.update(
            client_id=form.client_id,
            client_name=client["name"],
            redirect_uri=form.redirect_uri,
            state=form.state,
        )
        try:
            code_details = web.form("code_challenge", "code_challenge_method")
        except web.BadRequest:
            pass
        else:
            tx.user.session.update(
                code_challenge=code_details.code_challenge,
                code_challenge_method=code_details.code_challenge_method,
            )
        return app.view.signin(client, developer, form.scope, supported_scopes)

    def post(self):
        """Handle "Profile URL" flow response."""
        auth_response, complete_redemption = redeem_authorization_code()
        complete_redemption(auth_response)


@app.control(r"consent")
class AuthorizationConsent:
    """The authorization consent screen."""

    def post(self):
        """Handle consent screen action."""
        form = web.form("action", scopes=[])
        redirect_uri = web.uri(tx.user.session["redirect_uri"])
        if form.action == "cancel":
            raise web.Found(redirect_uri)
        code = web.nbrandom(32)
        while True:
            try:
                tx.db.insert(
                    "auths",
                    auth_id=web.nbrandom(4),
                    code=code,
                    code_challenge=tx.user.session["code_challenge"],
                    code_challenge_method=tx.user.session["code_challenge_method"],
                    client_id=tx.user.session["client_id"],
                    client_name=tx.user.session["client_name"],
                    redirect_uri=tx.user.session["redirect_uri"],
                    response={"scope": form.scopes},
                )
            except tx.db.IntegrityError:
                continue
            break
        redirect_uri["code"] = code
        redirect_uri["state"] = tx.user.session["state"]
        raise web.Found(redirect_uri)


@app.control(r"tokens")
class TokenEndpoint:
    """A token endpoint."""

    def get(self):
        return "token endpoint: show tokens to owner; otherwise form to submit a code"

    def post(self):
        """Create or revoke an access token."""
        # TODO token introspection
        # TODO token verification
        try:
            auth_response, complete_redemption = redeem_authorization_code()
        except web.BadRequest:
            pass
        else:
            # handle "Access Token" response
            if not auth_response["scope"]:
                raise web.BadRequest("Access Token request requires a scope")
            auth_response.update(
                access_token=f"secret-token:{web.nbrandom(12)}",
                token_type="Bearer",
            )
            complete_redemption(auth_response)
        # perform revocation
        form = web.form("action", "token")
        if form.action == "revoke":
            tx.db.update(
                "auths",
                revoked=web.utcnow(),
                where="""json_extract(response, '$.access_token') = ?""",
                vals=[form.token],
            )
            raise web.OK("")


def redeem_authorization_code():
    """Verify authenticity and return list of requested scopes."""
    # TODO verify authenticity
    # TODO grant_type=refresh_token
    form = web.form(
        "code", "client_id", "redirect_uri", grant_type="authorization_code"
    )
    if form.grant_type not in ("authorization_code", "refresh_token"):
        raise web.Forbidden(f"`grant_type` {form.grant_type} not supported")
    auth = tx.db.select("auths", where="code = ?", vals=[form.code])[0]
    if "code_verifier" in form:
        if not auth["code_challenge"]:
            raise web.BadRequest("`code_verifier` without a `code_challenge`")
        if auth["code_challenge"] != base64.urlsafe_b64encode(
            hashlib.sha256(form.code_verifier.encode("ascii")).digest()
        ).decode().rstrip("="):
            raise web.Forbidden("code mismatch")
    elif auth["code_challenge"]:
        raise web.BadRequest("`code_challenge` without `code_verifier`")

    def complete_redemption(response):
        response["me"] = f"{tx.request.uri.scheme}://{tx.request.uri.netloc}"
        if "profile" in response["scope"]:
            response["profile"] = {
                "name": tx.host.owner["name"][0],
                "url": "TODO",
                "photo": "TODO",
            }
            if "email" in response["scope"]:
                try:
                    auth_response["profile"]["email"] = tx.host.owner["email"][0]
                except KeyError:
                    pass
        tx.db.update("auths", response=response, where="code = ?", vals=[auth["code"]])
        web.header("Content-Type", "application/json")
        raise web.OK(response)

    return auth["response"], complete_redemption


@app.control(r"tickets")
class TicketEndpoint:
    """A ticket endpoint."""

    def get(self):
        return (
            "ticket endpoint: show tickets to owner; otherwise form to submit a ticket"
        )


@app.control(r"clients")
class Clients:
    """Authorized clients."""

    def get(self):
        clients = tx.db.select(
            "auths", what="DISTINCT client_id, client_name", order="client_name ASC"
        )
        return app.view.clients(clients)


@app.control(r"clients/{client_id}")
class Client(web.Resource):
    """An authorized client."""

    def get(self):
        auths = tx.db.select(
            "auths",
            where="client_id = ?",
            vals=[f"https://{self.client_id}"],
            order="redirect_uri, initiated DESC",
        )
        return app.view.client(auths)


@app.control(r"sign-in")
class SignIn:
    """Sign in as the owner of the site."""

    def post(self):
        form = web.form("passphrase", return_to="/")
        credential = tx.db.select("credentials", order="created DESC")[0]
        if web.verify_passphrase(
            credential["salt"],
            credential["scrypt_hash"],
            form.passphrase.translate({32: None}),
        ):
            tx.user.session["uid"] = tx.host.owner["uid"][0]
            raise web.SeeOther(form.return_to)
        raise web.Unauthorized("bad passphrase")


@app.control(r"sign-out")
class SignOut:
    """Sign out as the owner of the site."""

    def get(self):
        if not tx.user.is_owner:
            raise web.Unauthorized("must be owner")
        return app.view.signout()

    def post(self):
        if not tx.user.is_owner:
            raise web.Unauthorized("must be owner")
        tx.user.session = None
        return_to = web.form(return_to="").return_to
        raise web.SeeOther(f"/{return_to}")


# @app.migrate(1)
# def change_name(db):
#     db.rename_column("auths", "revoked", "revoced")
