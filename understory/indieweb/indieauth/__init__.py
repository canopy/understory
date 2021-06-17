"""IndieAuth client and server apps and sign-in helper."""

from __future__ import annotations

import base64
import hashlib

from understory import web
from understory.web import tx

root = web.application("IndieAuth", mount_prefix="auth", db=False, client_id=r"[\w/.]+")
server = web.application(
    "IndieAuthServer", mount_prefix="auth/sign-ins", db=False, client_id=r"[\w/.]+"
)
client = web.application("IndieAuthClient", mount_prefix="auth/visitors", db=False)
templates = web.templates(__name__)


def init_owner(name):
    """Initialize owner of the request domain."""
    salt, scrypt_hash, passphrase = web.generate_passphrase()
    tx.db.insert("credentials", salt=salt, scrypt_hash=scrypt_hash)
    uid = str(web.uri(tx.origin))
    tx.db.insert("identities", card={"name": [name], "uid": [uid], "url": [uid]})
    tx.user.session = {"uid": uid, "name": name}
    tx.host.owner = get_owner()
    return uid, passphrase


def get_owner() -> dict | None:
    """Return a dict of owner details or None if no know owner."""
    try:
        owner = tx.db.select("identities")[0]["card"]
    except IndexError:
        owner = None
    return owner


def wrap_server(handler, app):
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
    if not tx.host.owner and tx.request.method == "GET":
        raise web.OK(templates.claim())
    try:
        tx.user.is_owner = tx.user.session["uid"] == tx.host.owner["uid"][0]
    except (AttributeError, KeyError, IndexError):
        tx.user.is_owner = False
    passthrough = (
        "auth",
        "auth/sign-in",
        "auth/claim",
        "auth/sign-ins/token",
        "auth/visitors/sign-in",
        "auth/visitors/authorize",
    )
    if (
        tx.request.uri.path.startswith(("auth", "pub", "sub"))
        and tx.request.uri.path not in passthrough
        and not tx.user.is_owner
        and not tx.request.headers.get("Authorization")
    ):  # TODO validate token
        raise web.Unauthorized(templates.unauthorized())
    yield
    if tx.request.uri.path == "" and tx.response.body:
        doc = web.parse(tx.response.body)
        base = "/auth/sign-ins"
        try:
            head = doc.select("head")[0]
        except IndexError:
            pass
        else:
            head.append(
                f"<link rel=authorization_endpoint href={base}>",
                f"<link rel=token_endpoint href={base}/token>",
            )
            tx.response.body = doc.html
        web.header("Link", f'<{base}>; rel="authorization_endpoint"', add=True)
        web.header("Link", f'<{base}/token>; rel="token_endpoint"', add=True)


def wrap_client(handler, app):
    """Ensure client database contains visitors table."""
    # TODO store User Agent and IP address
    tx.db.define(
        "visitors",
        url="TEXT",
        name="TEXT",
        email="TEXT",
        access_token="TEXT",
        account_created="DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
    )
    yield


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


@root.route(r"")
class AuthorizationRoot:
    """IndieAuth root manages either or both of server and client."""

    def get(self):
        return templates.root()


@root.route(r"sign-in")
class OwnerSignIn:
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


@root.route(r"sign-out")
class OwnerSignOut:
    """Owner sign out."""

    def post(self):
        form = web.form(return_to="")
        print(form.return_to)
        tx.user.session = None
        raise web.SeeOther(f"/{form.return_to}")


@root.route(r"claim")
class ClaimOwner:
    """Claim site as owner."""

    def post(self):
        name = web.form("name").name
        # tx.user.session = None
        uid, passphrase = init_owner(name)
        return templates.claimed(" ".join(passphrase))


@root.route(r"identity")
class Identity:
    """"""

    def get(self):
        return templates.identity(get_owner())

    def post(self):
        return self.set_name()

    def set_name(self):
        name = web.form("name").name
        card = tx.db.select("identities")[0]["card"]
        card.update(name=[name])
        tx.db.update("identities", card=card)
        return name


@server.route(r"")
class AuthorizationEndpoint:
    """IndieAuth server `authorization endpoint`."""

    def get(self):
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
            clients = tx.db.select(
                "auths", order="client_name ASC", what="DISTINCT client_id, client_name"
            )
            active = tx.db.select("auths", where="revoked is null")
            revoked = tx.db.select("auths", where="revoked not null")
            return templates.authorizations(clients, active, revoked)
        client, developer = get_client(form.client_id)
        tx.user.session["client_id"] = form.client_id
        tx.user.session["client_name"] = client["name"]
        tx.user.session["redirect_uri"] = form.redirect_uri
        tx.user.session["state"] = form.state
        tx.user.session["code_challenge"] = form.code_challenge
        tx.user.session["code_challenge_method"] = form.code_challenge_method
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
        tx.user.is_authenticating = True
        return templates.signin(client, developer, scopes)

    def post(self):
        form = web.form("action", scopes=[])
        redirect_uri = web.uri(tx.user.session["redirect_uri"])
        if form.action == "cancel":
            raise web.Found(redirect_uri)
        code = f"secret-token:{web.nbrandom(32)}"
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


@server.route(r"token")
class TokenEndpoint:
    """IndieAuth server `token endpoint`."""

    def post(self):
        try:
            form = web.form("action", "token")
            if form.action == "revoke":
                tx.db.update(
                    "auths",
                    revoked=web.utcnow(),
                    vals=[form.token],
                    where="""json_extract(response,
                                                   '$.access_token') = ?""",
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
            response.update(access_token=web.nbrandom(12), token_type="Bearer")
            response["me"] = f"{tx.request.uri.scheme}://" f"{tx.request.uri.netloc}"
        tx.db.update("auths", response=response, where="code = ?", vals=[auth["code"]])
        web.header("Content-Type", "application/json")
        return response

    def is_token_request(self, scope):
        """Determine whether the list of scopes dictates a token request."""
        return bool(len([s for s in scope if s not in ("profile", "email")]))


@server.route(r"clients")
class Clients:
    """IndieAuth server authorized clients."""

    def get(self):
        clients = tx.db.select(
            "auths", what="DISTINCT client_id, client_name", order="client_name ASC"
        )
        return templates.clients(clients)


@server.route(r"clients/{client_id}")
class Client:
    """IndieAuth server authorized client."""

    def get(self):
        auths = tx.db.select(
            "auths",
            where="client_id = ?",
            vals=[f"https://{self.client_id}"],
            order="redirect_uri, initiated DESC",
        )
        return templates.client(auths)


@client.route(r"")
class Visitors:
    """."""

    def get(self):
        return templates.visitors(dict(r) for r in tx.db.select("visitors"))


@client.route(r"sign-in")
class SignIn:
    """IndieAuth client sign in."""

    def get(self):
        try:
            form = web.form("me", return_to="/")
        except web.BadRequest:
            return templates.identify(tx.host.name)
        # XXX try:
        # XXX     rels = tx.cache[form.me].mf2json["rels"]
        # XXX except web.ConnectionError:
        # XXX     return f"can't reach {form.me}"
        # XXX auth_endpoint = web.uri(rels["authorization_endpoint"][0])
        # XXX token_endpoint = web.uri(rels["token_endpoint"][0])
        # XXX micropub_endpoint = web.uri(rels["micropub"][0])
        auth_endpoint = web.discover_link(form.me, "authorization_endpoint")
        token_endpoint = web.discover_link(form.me, "token_endpoint")
        micropub_endpoint = web.discover_link(form.me, "micropub")
        tx.user.session["auth_endpoint"] = str(auth_endpoint)
        tx.user.session["token_endpoint"] = str(token_endpoint)
        tx.user.session["micropub_endpoint"] = str(micropub_endpoint)
        client_id = web.uri(f"http://{tx.host.name}:{tx.host.port}")
        auth_endpoint["me"] = form.me
        auth_endpoint["client_id"] = tx.user.session["client_id"] = client_id
        auth_endpoint["redirect_uri"] = tx.user.session["redirect_uri"] = (
            client_id / "auth/visitors/authorize"
        )
        auth_endpoint["response_type"] = "code"
        auth_endpoint["state"] = tx.user.session["state"] = web.nbrandom(16)
        code_verifier = tx.user.session["code_verifier"] = web.nbrandom(64)
        code_challenge = hashlib.sha256(code_verifier.encode("ascii")).hexdigest()
        auth_endpoint["code_challenge"] = base64.b64encode(
            code_challenge.encode("ascii")
        )
        auth_endpoint["code_challenge_method"] = "S256"
        auth_endpoint["scope"] = "create draft update delete profile email"
        tx.user.session["return_to"] = form.return_to
        raise web.SeeOther(auth_endpoint)


@client.route(r"authorize")
class Authorize:
    """IndieAuth client authorization."""

    def get(self):
        form = web.form("state", "code")
        if form.state != tx.user.session["state"]:
            raise web.BadRequest("bad state")
        payload = {
            "grant_type": "authorization_code",
            "code": form.code,
            "client_id": tx.user.session["client_id"],
            "redirect_uri": tx.user.session["redirect_uri"],
            "code_verifier": tx.user.session["code_verifier"],
        }
        response = web.post(
            tx.user.session["token_endpoint"],
            headers={"Accept": "application/json"},
            data=payload,
        ).json
        profile = response.get("profile", {})
        tx.db.insert(
            "visitors",
            url=response["me"],
            name=profile.get("name"),
            email=profile.get("email"),
            access_token=response["access_token"],
        )
        tx.user.session["uid"] = response["me"]
        raise web.SeeOther(tx.user.session["return_to"])


@client.route(r"sign-out")
class SignOut:
    """IndieAuth client sign out."""

    def post(self):
        token = tx.db.select(
            "visitors", where="url = ?", vals=[tx.user.session["uid"]]
        )[0]["access_token"]
        web.post(
            tx.user.session["token_endpoint"], data={"action": "revoke", "token": token}
        )
        tx.user.session = None
        raise web.SeeOther("/")


def sign_in(user_url):
    """Initiate an IndieAuth sign-in (eg. micropub client)."""
