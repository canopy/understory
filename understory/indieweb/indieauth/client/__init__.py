"""An IndieAuth client."""

import base64
import hashlib

from understory import web
from understory.web import tx, uri

app = web.application(
    __name__,
    prefix="access",
    model={
        "users": {
            "url": "TEXT",
            "name": "TEXT",
            "email": "TEXT",
            "access_token": "TEXT",
            "account_created": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
        },
    },
)


def sign_in(site: uri, user: uri) -> uri:
    """
    Return the URI to initiate an IndieAuth sign-in at `site` for `user`.

    `site` should be the actual sign-in endpoint URI (different for each service)
    `me` should be the identity URI for the user attempting sign in

    """
    # TODO determine the sign-in endpoint from form on given site
    site["me"] = user
    return site


def get_users():
    return list(tx.db.select("users"))


def wrap(handler, mainapp):
    """Ensure client database contains users table."""
    # TODO store User Agent and IP address
    yield


@app.control(r"")
class Users:
    """."""

    def get(self):
        return app.view.users(get_users())


@app.control(r"sign-in")
class SignIn:
    """IndieAuth client sign in."""

    def get(self):
        try:
            form = web.form("me", return_to="/")
        except web.BadRequest:
            return app.view.signin(tx.host.name)
        # XXX try:
        # XXX     rels = tx.cache[form.me].mf2json["rels"]
        # XXX except web.ConnectionError:
        # XXX     return f"can't reach {form.me}"
        # XXX auth_endpoint = uri(rels["authorization_endpoint"][0])
        # XXX token_endpoint = uri(rels["token_endpoint"][0])
        # XXX micropub_endpoint = uri(rels["micropub"][0])
        auth_endpoint = web.discover_link(form.me, "authorization_endpoint")
        token_endpoint = web.discover_link(form.me, "token_endpoint")
        micropub_endpoint = web.discover_link(form.me, "micropub")
        tx.user.session["auth_endpoint"] = str(auth_endpoint)
        tx.user.session["token_endpoint"] = str(token_endpoint)
        tx.user.session["micropub_endpoint"] = str(micropub_endpoint)
        client_id = uri(f"http://{tx.host.name}:{tx.host.port}")
        auth_endpoint["me"] = form.me
        auth_endpoint["client_id"] = tx.user.session["client_id"] = client_id
        auth_endpoint["redirect_uri"] = tx.user.session["redirect_uri"] = (
            client_id / "access/authorize"
        )
        auth_endpoint["response_type"] = "code"
        auth_endpoint["state"] = tx.user.session["state"] = web.nbrandom(16)
        code_verifier = tx.user.session["code_verifier"] = web.nbrandom(64)
        auth_endpoint["code_challenge"] = (
            base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode("ascii")).digest()
            )
            .decode()
            .rstrip("=")
        )
        auth_endpoint["code_challenge_method"] = "S256"
        auth_endpoint["scope"] = "create draft update delete profile email"
        tx.user.session["return_to"] = form.return_to
        raise web.SeeOther(auth_endpoint)


@app.control(r"authorize")
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
            "users",
            url=response["me"],
            name=profile.get("name"),
            email=profile.get("email"),
            access_token=response["access_token"],
        )
        tx.user.session["uid"] = response["me"]
        raise web.SeeOther(tx.user.session["return_to"])


@app.control(r"sign-out")
class SignOut:
    """IndieAuth client sign out."""

    def get(self):
        return app.view.signout()

    def post(self):
        access_token = tx.db.select(
            "users", where="url = ?", vals=[tx.user.session["uid"]]
        )[0]["access_token"]
        web.post(
            tx.user.session["token_endpoint"],
            data={"action": "revoke", "token": access_token},
        )
        tx.user.session = None
        raise web.SeeOther("/")
