""""""

from understory import host, sql, web
from understory.web import tx

model = sql.model(
    __name__,
    providers={"service": "TEXT UNIQUE", "token": "TEXT UNIQUE"},
    machines={
        "name": "TEXT UNIQUE",
        "ip_address": "TEXT UNIQUE",
        "details": "JSON",
    },
    domains={
        "name": "TEXT UNIQUE",
        "nameserver": "TEXT UNIQUE",
        "details": "JSON",
    },
)
app = web.application(
    __name__,
    prefix="sites",
    args={"machine": r"\w+", "domain_name": r"\w+"},
    model=model.schemas,
)


def spawn_machine(name, token):
    """Spin up a VPS and setup a machine."""
    ip_address = host.spawn_machine(name, token)
    tx.db.insert("machines", name=name, ip_address=ip_address, details={})


def build(ip_address, program):
    details = tx.db.select("machines", where="ip_address = ?", vals=[ip_address])[0][
        "details"
    ]
    details[program] = getattr(host, f"setup_{program}")(ip_address)
    tx.db.update("machines", where="ip_address = ?", vals=[ip_address], details=details)


@app.control("")
class Sites:
    """Manage your websites."""

    def get(self):
        machines = tx.db.select("machines")
        return app.view.index(machines)


@app.control("providers")
class Providers:
    """Manage your third-party service providers."""

    def get(self):
        try:
            host = tx.db.select(
                "providers", where="service = ?", vals=["digitalocean.com"]
            )[0]
        except IndexError:
            host = None
        try:
            registrar = tx.db.select(
                "providers", where="service = ?", vals=["dynadot.com"]
            )[0]
        except IndexError:
            registrar = None
        return app.view.providers(host, registrar)


@app.control("providers/host")
class MachineHost:
    """Manage your machine host."""

    def post(self):
        form = web.form("service", "token")
        tx.db.insert("providers", service=form.service, token=form.token)
        return "token has been set"

    def delete(self):
        tx.db.delete("providers", where="service = ?", vals=["digitalocean.com"])
        return "deleted"


@app.control("providers/registrar")
class DomainRegistrar:
    """Manage your domain registrar."""

    def post(self):
        form = web.form("service", "token")
        tx.db.insert("providers", service=form.service, token=form.token)
        return "token has been set"

    def delete(self):
        tx.db.delete("providers", where="service = ?", vals=["dynadot.com"])
        return "deleted"


@app.control("machines")
class Machines:
    """Manage your machines."""

    def get(self):
        return app.view.machines()

    def post(self):
        name = web.form("name").name
        token = tx.db.select(
            "providers", where="service = ?", vals=["digitalocean.com"]
        )[0]["token"]
        web.enqueue(spawn_machine, name, token)
        raise web.Accepted("machine is being created..")


@app.control("machines/{machine}")
class Machine:
    """Manage one of your machines."""

    def get(self):
        machine = tx.db.select("machines", where="name = ?", vals=[self.machine])[0]
        try:
            token = get_dynadot_token(tx.db)
        except IndexError:
            domains = None
        else:
            domains = host.dynadot.Client(token).list_domain()
        # ssh = host.digitalocean.get_ssh("root", machine["ip_address"])
        # ls = ssh("ls -la /etc")
        return app.view.machine(machine, domains)  # , ls)


@app.control("machines/{machine}/update")
class MachineBuild:
    """Manage your machine's system updates."""

    def get(self):
        ...

    def post(self):
        machine = tx.db.select("machines", where="name = ?", vals=[self.machine])[0]
        web.enqueue(host.upgrade_system, machine["ip_address"])
        raise web.Accepted("system is updating on the machine..")


@app.control("machines/{machine}/builds")
class MachineBuild:
    """Manage your machine's builds."""

    def get(self):
        ...

    def post(self):
        program = web.form("program").program
        machine = tx.db.select("machines", where="name = ?", vals=[self.machine])[0]
        web.enqueue(build, machine["ip_address"], program)
        raise web.Accepted(f"{program} is building on the machine..")


@app.control("domains")
class Domains:
    """Manage your domains."""

    def get(self):
        return app.view.domains()

    def post(self):
        name = web.form("name").name
        token = tx.db.select("providers", where="service = ?", vals=["dynadot.com"])[0][
            "token"
        ]
        # XXX web.enqueue(spawn_machine, name, token)
        raise web.Created("domain has been added..", f"/sites/domains/{name}")


@app.control("domains/{domain_name}")
class Domain:
    """Manage one of your domains."""

    def get(self):
        domain = tx.db.select("domains", where="name = ?", vals=[self.domain_name])[0]
        return app.view.domain(domain)


@model.control
def get_dynadot_token(db):
    return db.select("providers", where="service = ?", vals=["dynadot.com"])[0]["token"]
