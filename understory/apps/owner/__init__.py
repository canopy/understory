"""A web app for the site owner."""

from understory import web
from understory.web import tx

app = web.application(
    __name__,
    prefix="owner",
    model={
        "identities": {
            "created": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "card": "JSON",
        },
        "passphrases": {
            "created": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "passphrase_salt": "BLOB",
            "passphrase_hash": "BLOB",
        },
    },
)


def wrap(handler, main_app):
    """Initialize owner."""
    tx.identities = app.model(tx.db)
    try:
        tx.host.owner = tx.identities.get_identity(tx.origin)["card"]
    except IndexError:
        web.header("Content-Type", "text/html")
        if tx.request.method == "GET":
            raise web.OK(app.view.claim())
        elif tx.request.method == "POST":
            name = web.form("name").name
            tx.identities.add_identity(tx.origin, name)
            passphrase = tx.identities.add_passphrase()
            tx.user.session = tx.identities.get_identity(tx.origin)["card"]
            raise web.Created(app.view.claimed(tx.origin, passphrase), tx.origin)
    try:
        tx.user.is_owner = tx.user.session["uid"] == tx.origin
    except (AttributeError, KeyError, IndexError):
        tx.user.is_owner = False
    yield


@app.control(r"sign-in")
class SignIn:
    """Sign in as the owner of the site."""

    def get(self):
        """Return the sign in form."""
        return app.view.signin()

    def post(self):
        """Verify passphrase, sign the owner in and return to given return page."""
        form = web.form("passphrase", return_to="/")
        passphrase = tx.identities.get_passphrase()
        if web.verify_passphrase(
            passphrase["passphrase_salt"],
            passphrase["passphrase_hash"],
            form.passphrase.replace(" ", ""),
        ):
            tx.user.session = tx.identities.get_identity(tx.origin)["card"]
            raise web.SeeOther(form.return_to)
        raise web.Unauthorized("bad passphrase")


@app.control(r"sign-out")
class SignOut:
    """Sign out as the owner of the site."""

    def get(self):
        """Return the sign out form."""
        # XXX if not tx.user.is_owner:
        # XXX     raise web.Unauthorized("must be owner")
        return app.view.signout()

    def post(self):
        """Sign the owner out and return to given return page."""
        # XXX if not tx.user.is_owner:
        # XXX     raise web.Unauthorized("must be owner")
        tx.user.session = None
        return_to = web.form(return_to="").return_to
        raise web.SeeOther(f"/{return_to}")


@app.model.control
def get_identity(db, uid):
    """Return identity with given `uid`."""
    return db.select(
        "identities",
        where="json_extract(identities.card, '$.uid') = ?",
        vals=[uid],
    )[0]


@app.model.control
def add_identity(db, uid, name):
    db.insert(
        "identities",
        card={"uid": uid, "name": name},
    )


@app.model.control
def get_passphrase(db):
    """Return most recent passphrase."""
    return db.select("passphrases", order="created DESC")[0]


@app.model.control
def add_passphrase(db):
    passphrase_salt, passphrase_hash, passphrase = web.generate_passphrase()
    db.insert(
        "passphrases",
        passphrase_salt=passphrase_salt,
        passphrase_hash=passphrase_hash,
    )
    return passphrase
