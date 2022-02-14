"""A web app for the site owner."""

from Crypto.Random import random
from understory import host, web

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


@app.wrap
def connect_model(handler, main_app):
    """Connect the model to this transaction's database."""
    web.tx.identities = app.model(web.tx.db)
    yield


@app.wrap
def wrap(handler, main_app):
    """Ensure an owner exists and then add their details to the transaction."""
    web.tx.response.claimed = True
    try:
        web.tx.host.owner = web.tx.identities.get_identity(web.tx.origin)["card"]
    except IndexError:
        web.header("Content-Type", "text/html")
        # if web.tx.request.method == "GET":
        #     web.tx.response.claimed = False
        #     raise web.NotFound(app.view.claim())
        # elif web.tx.request.method == "POST":
        # name = web.form("name").name
        web.tx.identities.add_identity(web.tx.origin, "Anonymous")
        passphrase = " ".join(web.tx.identities.add_passphrase())
        web.tx.host.owner = web.tx.user.session = web.tx.identities.get_identity(
            web.tx.origin
        )["card"]
        web.tx.user.is_owner = True
        if kiosk := web.form(kiosk=None).kiosk:
            with open(f"{kiosk}/passphrase", "w") as fp:
                fp.write(passphrase)
            raise web.SeeOther("/")
        raise web.Created(app.view.claimed(web.tx.origin, passphrase), web.tx.origin)
    try:
        web.tx.user.is_owner = web.tx.user.session["uid"][0] == web.tx.origin
    except (AttributeError, KeyError, IndexError):
        web.tx.user.is_owner = False
    yield


@app.control("")
class Owner:
    """Owner information."""

    def get(self):
        return app.view.index(web.tx.providers.get_digitalocean_token())


@app.control("sign-in")
class SignIn:
    """Sign in as the owner of the site."""

    def get(self):
        try:
            self.verify_passphrase()
        except web.BadRequest:
            return app.view.signin()

    def post(self):
        self.verify_passphrase()

    def verify_passphrase(self):
        """Verify passphrase, sign the owner in and return to given return page."""
        form = web.form("passphrase", return_to="/")
        passphrase = web.tx.identities.get_passphrase()
        if web.verify_passphrase(
            passphrase["passphrase_salt"],
            passphrase["passphrase_hash"],
            form.passphrase.replace(" ", ""),
        ):
            web.tx.user.session = web.tx.identities.get_identity(web.tx.origin)["card"]
            raise web.SeeOther(form.return_to)
        raise web.Unauthorized("bad passphrase")


@app.control("sign-out")
class SignOut:
    """Sign out as the owner of the site."""

    def get(self):
        """Return the sign out form."""
        # XXX if not web.tx.user.is_owner:
        # XXX     raise web.Unauthorized("must be owner")
        return app.view.signout()

    def post(self):
        """Sign the owner out and return to given return page."""
        # XXX if not web.tx.user.is_owner:
        # XXX     raise web.Unauthorized("must be owner")
        web.tx.user.session = None
        return_to = web.form(return_to="").return_to
        raise web.SeeOther(f"/{return_to}")


def spawn_canopy(token):
    host.setup_canopy("138.68.11.120")
    return
    ip_address = host.spawn_machine("canopy", token)
    host.setup_machine(ip_address)
    host.setup_nginx(ip_address)
    host.generate_dhparam(ip_address)
    host.setup_python(ip_address)
    host.setup_supervisor(ip_address)
    # XXX host.setup_tor(ip_address)


@app.control("move")
class Move:
    """Move site to the cloud."""

    def post(self):
        web.enqueue(spawn_canopy, web.tx.providers.get_digitalocean_token())
        raise web.Accepted("canopy tree is being spawned in the cloud..")


@app.model.control
def get_identity(db, uid):
    """Return identity with given `uid`."""
    return db.select(
        "identities",
        where="json_extract(identities.card, '$.uid[0]') = ?",
        vals=[uid],
    )[0]


@app.model.control
def add_identity(db, uid, name):
    db.insert("identities", card={"uid": [uid], "name": [name]})


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
