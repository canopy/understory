"""IndieAuth root app and sign-in helper."""

from understory import web
from understory.web import tx, uri

from . import client, server

profile = web.application("IndieAuthProfile", mount_prefix="profile", db=False)
root = web.application(
    "IndieAuthRoot", mount_prefix="auth", db=False, client_id=r"[\w/.]+"
)
templates = web.templates(__name__)


def sign_in(site: uri, user: uri) -> uri:
    """
    Return the URI to initiate an IndieAuth sign-in at `site` for `user`.

    `site` should be the actual sign-in endpoint URI (different for each service)
    `me` should be the identity URI for the user attempting sign in

    """
    # TODO determine the sign-in endpoint from form on given site
    site["me"] = user
    return site


@profile.route(r"")
class Profile:
    """"""

    def get(self):
        return templates.identity(server.get_owner())

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


@root.route(r"")
class Authentication:
    """Authentication root dynamically manages either or both of server and client."""

    def get(self):
        return templates.root(
            server.get_owner(), server.get_clients(), client.get_users()
        )


@root.route(r"sign-in")
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


@root.route(r"sign-out")
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
