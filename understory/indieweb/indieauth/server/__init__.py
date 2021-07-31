"""IndieAuth server app."""

from __future__ import annotations

import base64
import hashlib

from understory import web
from understory.web import tx

app = web.application(
    "IndieAuthServer", mount_prefix="auth", db=False, client_id=r"[\w/.]+"
)
profile = web.application("IndieAuthProfile", mount_prefix="profile", db=False)
templates = web.templates(__name__)


def init_owner(name):
    """Initialize owner of the request domain."""
    salt, scrypt_hash, passphrase = web.generate_passphrase()
    tx.db.insert("credentials", salt=salt, scrypt_hash=scrypt_hash)
    version = web.nbrandom(3)
    uid = str(web.uri(tx.origin))
    tx.db.insert(
        "identities",
        card={"version": version, "name": [name], "uid": [uid], "url": [uid]},
    )
    tx.user.session = {"uid": uid, "name": name}
    tx.user.is_owner = True
    tx.host.owner = get_owner()
    return uid, passphrase


def get_owner() -> dict | None:
    """Return a dict of owner details or None if no know owner."""
    try:
        owner = tx.db.select("identities")[0]["card"]
    except IndexError:
        owner = None
    return owner


def get_client(client_id):
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


def wrap(handler, app):
    """Ensure server links are in head of root document."""
    tx.db.define(
        "auths",
        auth_id="TEXT",
        initiated="DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
        revoked="DATETIME",
        code="TEXT",
        client_id="TEXT",
        client_name="TEXT",
        code_challenge="TEXT",
        code_challenge_method="TEXT",
        redirect_uri="TEXT",
        response="JSON",
        token="TEXT",
    )
    tx.db.define(
        "credentials",
        created="DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
        salt="BLOB",
        scrypt_hash="BLOB",
    )
    tx.db.define("identities", card="JSON")
    tx.host.owner = get_owner()
    if not tx.host.owner:
        web.header("Content-Type", "text/html")
        if tx.request.method == "GET":
            raise web.OK(templates.claim())
        elif tx.request.method == "POST":
            uid, passphrase = init_owner(web.form("name").name)
            raise web.Created(templates.claimed(uid, " ".join(passphrase)), uid)
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
    #     raise web.Unauthorized(templates.unauthorized())
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


@app.route(r"")
class AuthorizationEndpoint:
    """IndieAuth server `authorization endpoint`."""

    def get(self):
        """Initiate a third-party sign-in falling back"""
        if not tx.user.is_owner:
            raise web.Unauthorized("This area is for the site owner's use only.")
        try:
            form = web.form(
                "response_type",
                "client_id",
                "redirect_uri",
                "state",
                "code_challenge",
                "code_challenge_method",
                scope="",
            )
        except web.BadRequest:
            return templates.authorizations(get_clients(), get_active(), get_revoked())
        client, developer = get_client(form.client_id)
        tx.user.session.update(
            client_id=form.client_id,
            client_name=client["name"],
            redirect_uri=form.redirect_uri,
            state=form.state,
            code_challenge=form.code_challenge,
            code_challenge_method=form.code_challenge_method,
        )
        supported_scopes = [
            "create",
            "draft",
            "update",
            "delete",
            "media",
            "profile",
            "email",
        ]
        scopes = [s for s in form.scope.split() if s in supported_scopes]
        return templates.signin(client, developer, scopes)

    def post(self):
        form = web.form("action", scopes=[])
        redirect_uri = web.uri(tx.user.session["redirect_uri"])
        if form.action == "cancel":
            raise web.Found(redirect_uri)
        code = web.nbrandom(32)
        s = tx.user.session
        decoded_code_challenge = base64.b64decode(s["code_challenge"]).decode()
        while True:
            try:
                tx.db.insert(
                    "auths",
                    auth_id=web.nbrandom(3),
                    code=code,
                    code_challenge=decoded_code_challenge,
                    code_challenge_method=s["code_challenge_method"],
                    client_id=s["client_id"],
                    client_name=s["client_name"],
                    redirect_uri=s["redirect_uri"],
                    response={"scope": " ".join(form.scopes)},
                )
            except tx.db.IntegrityError:
                continue
            break
        redirect_uri["code"] = code
        redirect_uri["state"] = tx.user.session["state"]
        raise web.Found(redirect_uri)


@app.route(r"tokens")
class TokenEndpoint:
    """A token endpoint."""

    def get(self):
        return "token endpoint: show tokens to owner; otherwise form to submit a code"

    def post(self):
        """Create or revoke an access token."""
        try:
            form = web.form("action", "token")
            if form.action == "revoke":
                tx.db.update(
                    "auths",
                    revoked=web.utcnow(),
                    where="""json_extract(response, '$.access_token') = ?""",
                    vals=[form.token],
                )
                raise web.OK("")
        except web.BadRequest:
            pass
        form = web.form(
            "grant_type", "code", "client_id", "redirect_uri", "code_verifier"
        )
        if form.grant_type != "authorization_code":
            raise web.Forbidden("only grant_type=authorization_code supported")
        auth = tx.db.select("auths", where="code = ?", vals=[form.code])[0]
        computed_code_challenge = hashlib.sha256(
            form.code_verifier.encode("ascii")
        ).hexdigest()
        if auth["code_challenge"] != computed_code_challenge:
            raise web.Forbidden("code mismatch")
        response = auth["response"]
        scope = response["scope"].split()
        if "profile" in scope:
            profile = {"name": tx.host.owner["name"][0]}
            if "email" in scope:
                try:
                    profile["email"] = tx.host.owner["email"][0]
                except KeyError:
                    pass
            response["profile"] = profile
        if scope and self.is_token_request(scope):
            response.update(
                access_token=f"secret-token:{web.nbrandom(12)}", token_type="Bearer"
            )
            response["me"] = f"{tx.request.uri.scheme}://{tx.request.uri.netloc}"
        tx.db.update("auths", response=response, where="code = ?", vals=[auth["code"]])
        web.header("Content-Type", "application/json")
        return response

    def is_token_request(self, scope):
        """Determine whether the list of scopes dictates a token request."""
        return bool(len([s for s in scope if s not in ("profile", "email")]))


@app.route(r"tickets")
class TicketEndpoint:
    """A ticket endpoint."""

    def get(self):
        return (
            "ticket endpoint: show tickets to owner; otherwise form to submit a ticket"
        )


@app.route(r"clients")
class Clients:
    """Authorized clients."""

    def get(self):
        clients = tx.db.select(
            "auths", what="DISTINCT client_id, client_name", order="client_name ASC"
        )
        return templates.clients(clients)


@app.route(r"clients/{client_id}")
class Client:
    """An authorized client."""

    client_id: str

    def get(self):
        auths = tx.db.select(
            "auths",
            where="client_id = ?",
            vals=[f"https://{self.client_id}"],
            order="redirect_uri, initiated DESC",
        )
        return templates.client(auths)


# XXX @root.route(r"")
# XXX class Authentication:
# XXX     """Authentication root dynamically manages either or both of server and client."""
# XXX
# XXX     def get(self):
# XXX         return templates.root(
# XXX             server.get_owner(), server.get_clients(), client.get_users()
# XXX         )


@app.route(r"sign-in")
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


@app.route(r"sign-out")
class SignOut:
    """Sign out as the owner of the site."""

    def get(self):
        if not tx.user.is_owner:
            raise web.Unauthorized("must be owner")
        return templates.signout()

    def post(self):
        if not tx.user.is_owner:
            raise web.Unauthorized("must be owner")
        tx.user.session = None
        return_to = web.form(return_to="").return_to
        raise web.SeeOther(f"/{return_to}")


@profile.route(r"")
class Profile:
    """"""

    def get(self):
        return templates.identity(get_owner())

    def post(self):
        if not tx.user.is_owner:
            raise web.Unauthorized("must be owner")
        return self.set_name()

    def set_name(self):
        name = web.form("name").name
        card = tx.db.select("identities")[0]["card"]
        card.update(name=[name])
        tx.db.update("identities", card=card)
        return name
