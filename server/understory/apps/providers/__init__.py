""""""

from understory import sql, web

app = web.application(
    __name__,
    prefix="providers",
    model={"providers": {"service": "TEXT UNIQUE", "token": "TEXT UNIQUE"}},
)


@app.wrap
def connect_model(handler, main_app):
    """Connect the model to this transaction's database."""
    web.tx.providers = app.model(web.tx.db)
    yield


@app.control("")
class Providers:
    """Manage your third-party service providers."""

    def get(self):
        try:
            host = web.tx.db.select(
                "providers", where="service = ?", vals=["digitalocean.com"]
            )[0]
        except IndexError:
            host = None
        try:
            registrar = web.tx.db.select(
                "providers", where="service = ?", vals=["dynadot.com"]
            )[0]
        except IndexError:
            registrar = None
        return app.view.providers(host, registrar)


@app.control("host")
class MachineHost:
    """Manage your machine host."""

    def post(self):
        form = web.form("service", "token")
        web.tx.db.insert("providers", service=form.service, token=form.token)
        return "token has been set"

    def delete(self):
        web.tx.db.delete("providers", where="service = ?", vals=["digitalocean.com"])
        return "deleted"


@app.control("registrar")
class DomainRegistrar:
    """Manage your domain registrar."""

    def post(self):
        form = web.form("service", "token")
        web.tx.db.insert("providers", service=form.service, token=form.token)
        return "token has been set"

    def delete(self):
        web.tx.db.delete("providers", where="service = ?", vals=["dynadot.com"])
        return "deleted"


@app.model.control
def get_digitalocean_token(db):
    try:
        return db.select("providers", where="service = ?", vals=["digitalocean.com"])[
            0
        ]["token"]
    except IndexError:
        return None


@app.model.control
def get_dynadot_token(db):
    return db.select("providers", where="service = ?", vals=["dynadot.com"])[0]["token"]
