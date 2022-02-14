""""""

from understory import host, sql, web
from understory.web import tx

model = sql.model(
    __name__,
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


@app.control("gaea")
class Gaea:
    """"""

    def get(self):
        # XXX config = get_config()
        # XXX if web.tx.request.headers["accept"] == "application/json":
        # XXX     return config

        # domains = []
        # if "registrar" in config:
        #     registrar = dict(config["registrar"])
        #     clients = {
        #         "dynadot.com": host.providers.Dynadot,
        #         "name.com": host.providers.NameCom,
        #     }
        #     domains = clients[registrar.pop("provider")](**registrar).list_domains()
        # dns = {}
        # if "domain" in config:
        #     dns["ns"] = [
        #         str(ns)
        #         for ns in web.dns.resolve(config["domain"], "NS").rrset.items.keys()
        #     ]
        #     dns["a"] = web.dns.resolve(config["domain"], "A")[0].address
        return app.view.gaea()  # config)  # , domains, dns)

    def post(self):
        # form = web.form("subdomain", "name")
        form = web.form("provider", "token")
        config = get_config()

        # domain = config["domain"]
        # fqdn = domain
        # if form.subdomain:
        #     fqdn = f"{form.subdomain}.{domain}"
        # update_config(fqdn=fqdn)

        if form.provider == "digitalocean.com":
            c = host.digitalocean.Client(form.token)
            try:
                c.get_keys()
            except host.digitalocean.TokenError:
                return {"status": "error", "message": "bad token"}
        elif form.provider == "linode.com":
            ...
        elif form.provider == "hetzner.com":
            ...
        else:
            return {
                "status": "error",
                "message": f"unsupported provider: {form.provider}",
            }
        config = update_config(
            host={
                "provider": form.provider,
                "token": form.token,
            }
        )

        # try:
        #     ip_address = config["ip_address"]
        # except KeyError:
        ip_address = host.spawn_machine("canopy", config["host"]["token"])
        config = update_config(ipAddress=ip_address, status={})

        # registrar = config["registrar"]
        # if registrar["provider"] == "dynadot.com":
        #     dynadot = host.providers.Dynadot(registrar["token"])
        #     dynadot.create_record(domain, ip_address, form.subdomain)
        # elif registrar["provider"] == "name.com":
        #     namecom = host.providers.NameCom(registrar["username"],
        #                                      registrar["token"])
        #     namecom.create_record(domain, ip_address, form.subdomain)

        host.setup_machine(ip_address)
        config = update_config(system_setup=True)
        host.setup_nginx(ip_address)
        config = update_config(nginx_installed=True)
        return
        host.generate_dhparam(ip_address)
        host.setup_tor(ip_address)
        host.setup_python(ip_address)
        host.setup_supervisor(ip_address)

        # while True:
        #     try:
        #         if web.dns.resolve(fqdn, "A")[0].address == ip_address:
        #             break
        #     except (
        #         web.dns.NoAnswer,
        #         web.dns.NXDOMAIN,
        #         web.dns.Timeout,
        #         web.dns.NoNameservers,
        #     ):
        #         pass
        #     else:
        #         print("waiting for DNS changes to propagate..")
        #         time.sleep(15)

        onion, passphrase = setup_canopy(ip_address)  # , form.name, fqdn)
        update_config(onion=onion, passphrase=passphrase)
        return {"onion": onion, "passphrase": passphrase}


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
