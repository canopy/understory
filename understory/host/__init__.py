"""Manage a web host."""

import shutil

import feedparser
import gaea
import pendulum
import semver
import sh
from understory import indieweb, web
from understory.web import tx

app = web.application(
    "gaea",
    service=r"(digitalocean|dynadot|github)",
    site=r"[a-z0-9-.]{4,128}",
    pkg=r"[a-z-]+",
    app_path=r"[a-z0-9-:.]{4,128}",
)
app.db.define("sessions", **web.session_table_sql)
web.add_job_tables(app.db)
app.wrap(web.resume_session)
app.mount(indieweb.indieauth.client.app)
app.wrap(indieweb.indieauth.client.wrap)


def get_ip():
    return sh.hostname("-I").split()[0]


@app.wrap
def contextualize(handler, app):
    tx.gaea = gaea.Gaea()
    yield


@app.route(r"")
class Main:
    """Admin interface."""

    def get(self):
        self.handle_auth()
        system_hostname = sh.hostname("--fqdn")
        system_uptime = sh.uptime()
        config = tx.gaea.get_config()
        sites = []
        for site in tx.gaea.sites_dir.iterdir():
            url = web.uri(site.name)
            try:
                a_record = str(web.dns.resolve(site.name, "A")[0])
            except (web.dns.NoAnswer, web.dns.NXDOMAIN):
                a_record = None
            try:
                ns_records = [str(r) for r in web.dns.resolve(site.name, "NS")]
            except (web.dns.NoAnswer, web.dns.NXDOMAIN):
                ns_records = []
            certified = (site / "domain.crt").exists()
            preloaded = web.in_hsts_preload(site.name)
            sites.append(
                (
                    url.suffix,
                    url.domain,
                    url.subdomain,
                    site,
                    a_record,
                    ns_records,
                    certified,
                    preloaded,
                )
            )
        tokens = config["tokens"]
        dynadot_token = tokens.get("dynadot")
        if dynadot_token:
            dynadot_domains = dict(Dynadot(dynadot_token).list_domain())
        else:
            dynadot_domains = {}
        apps = {}
        for package, applications in web.get_apps().items():
            name = package.metadata["Name"]
            current_version = package.metadata["Version"]
            update_available = None
            versions_url = f"https://pypi.org/rss/project/{name}/releases.xml"
            versions = feedparser.parse(versions_url)["entries"]
            try:
                latest_version = versions[0]["title"]
            except IndexError:
                pass  # TODO fallback to query from GitHub API
            else:
                if semver.compare(current_version, latest_version):
                    update_available = latest_version
            apps[package] = (update_available, applications)
        return web.template(html)(
            system_hostname,
            get_ip(),
            system_uptime,
            sites,
            dynadot_domains,
            apps,
            gaea.get_statuses(),
            config,
            tx.user,
        )

    def handle_auth(self):
        secret = web.form(secret=None).secret
        if secret:
            if secret == tx.gaea.get_config()["secret"]:
                web.tx.user.session["signed_in"] = True
                raise web.SeeOther("/")
            raise web.Unauthorized("bad secret")
        elif not web.tx.user.session.get("signed_in", False):
            raise web.Unauthorized("please sign in with your secret")


@app.route(r"tokens/{service}")
class Token:
    """Update the locally cached Dynadot API token."""

    def post(self):
        token = web.form("token").token
        config = tx.gaea.get_config()
        if token:
            config["tokens"][self.service] = token
        else:
            del config["tokens"][self.service]
        tx.gaea.save_config(config)
        raise web.SeeOther("/")


@app.route(r"sites")
class Websites:
    """Installed sites."""

    def post(self):
        site = web.form("site").site
        if not web.uri(site).suffix:
            return "unknown suffix"
        (tx.gaea.sites_dir / site).mkdir()
        raise web.SeeOther("/")


@app.route(r"sites/{site}")
class Website:
    """Installed site."""

    def delete(self):
        shutil.rmtree(tx.gaea.sites_dir / self.site)
        raise web.SeeOther("/")


@app.route(r"sites/{site}/dns")
class WebsiteDNS:
    """Site A record."""

    def post(self):
        do = DigitalOcean(tx.gaea.get_config()["tokens"]["digitalocean"])
        site = web.uri(self.site)
        domain_name = f"{site.domain}.{site.suffix}"
        ip = get_ip()
        if site.subdomain:
            digitalocean_domains = [d["name"] for d in do.get_domains()["domains"]]
            if self.site in digitalocean_domains:
                do.create_domain_record(domain_name, site.subdomain, ip)
        else:
            try:
                do.create_domain(domain_name, get_ip())
            except DomainExistsError:
                for record in do.get_domain_records(domain_name):
                    if record["name"] == "@" and record["type"] == "A":
                        break
                do.update_domain_record(domain_name, record["id"], data=ip)
        raise web.SeeOther("/")


@app.route(r"sites/{site}/certificate")
class WebsiteCertificate:
    """Site certificate."""

    def get(self):
        expires = pendulum.from_format(
            str(
                sh.openssl(
                    "x509",
                    "-enddate",
                    "-noout",
                    "-in",
                    tx.gaea.sites_dir / self.site / "domain.crt",
                )
            )
            .partition("=")[2]
            .rstrip(" GMT\n"),
            "MMM  D HH:mm:ss YYYY",
            tz="GMT",
        )
        web.header("Content-Type", "text/html")
        return f"""Expires: {expires}<br>
                   <form action=/sites/{self.site}/certificate method=post>
                     <button>Renew</button>
                   </form>"""

    def post(self):
        site_dir = tx.gaea.sites_dir / self.site
        conf = tx.gaea.nginx_dir / "conf/conf.d" / f"{self.site}.conf"
        if not conf.exists():
            with conf.open("w") as fp:
                fp.write(nginx_site_tls_conf.format(site=self.site))
            sh.sudo("supervisorctl", "restart", "nginx")
        web.generate_cert(self.site, site_dir, site_dir)
        raise web.SeeOther("/")


@app.route(r"sites/{site}/mount")
class WebsiteMount:
    """Site mount."""

    def post(self):
        app = web.form("app").app
        tx.gaea.mount_site(self.site, app)
        raise web.SeeOther("/")


@app.route(r"apps")
class Applications:
    """Installed applications."""

    def post(self):
        app = web.form("app").app
        web.enqueue(
            install_app,
            app,
            str(tx.gaea.home_dir),
            tx.gaea.get_config()["tokens"]["github"],
        )
        return "installing and restarting.."

        # github.com/<username>/<repo_name>

        # XXX owner, _, name = app.partition("/")
        # XXX app = app.removeprefix("https://")
        # XXX if "." in app.partition("/")[0]:
        # XXX     app_url = f"https://{app}"
        # XXX else:
        # XXX     if "/" in app:
        # XXX         owner, _, name = app.partition("/")
        # XXX     else:
        # XXX         owner = name = app
        # XXX     token = tx.gaea.get_config()["tokens"]["github"]
        # XXX     if token:
        # XXX         token += "@"
        # XXX     app_url = (f"git+https://{token}github.com/{owner}/{name}"
        # XXX                f".git#egg={name}")
        # XXX sh.sh("runinenv", "system/env", "pip", "install", "-e",
        # XXX       app_url, _cwd=tx.gaea.home_dir)


def install_app(app, home_dir, github_token):
    if app.startswith("https://"):  # Git repo
        pass  # TODO
    elif "/" in app:  # GitHub project
        gh_prefix = f"https://api.github.com/repos/{app}/releases"
        gh_token_header = f"token {github_token}"
        gh_headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": gh_token_header,
        }
        asset = web.get(f"{gh_prefix}/latest", headers=gh_headers).json["assets"][0]
        sh.wget(
            f"{gh_prefix}/assets/{asset['id']}",
            "-O",
            asset["name"],
            "--header",
            "Accept: application/octet-stream",
            "--header",
            f"Authorization: {gh_token_header}",
            _cwd=home_dir,
        )
        sh.sh("runinenv", "system/env", "pip", "install", asset["name"], _cwd=home_dir)
    else:  # PyPI package
        sh.sh("runinenv", "system/env", "pip", "install", app, _cwd=home_dir)
    sh.sudo("supervisorctl", "restart", "gaea-app", "gaea-app-jobs")


@app.route(r"apps/{pkg}")
class Package:
    """Installed application package."""

    def post(self):
        web.enqueue(upgrade_app, self.pkg, str(tx.gaea.home_dir))
        return "upgrading and restarting.."


def upgrade_app(app, home_dir):
    sh.sh("runinenv", "system/env", "pip", "install", "-U", app, _cwd=home_dir)
    sh.sudo("supervisorctl", "restart", "gaea-app")


@app.route(r"apps/{app_path}")
class Application:
    """Installed application."""

    def post(self):
        tx.gaea.run_app(self.app)
        raise web.SeeOther("/")


html = """$def with (hostname, ip_address, system_uptime, sites,\
                     dynadot_domains, apps, statuses, config, user)
<!doctype html>
<style>
body {
    background-color: #002b36;
    color: #839496;
    font-family: Inconsolata, "Ubuntu Mono", monospace;
    margin: 2em; }
header {
    display: grid;
    grid-column-gap: 1em;
    grid-template-columns: auto auto; }
header h1 {
    margin: 0; }
header p {
    margin: 0; }
#tokens {
    text-align: right; }
#tokens > div {
    margin: .25em 0; }
#tokens input[type=text] {
    padding: .075em; }
a:link {
    color: #268bd2; }
a:visited {
    color: #6c71c4; }
a:active {
    color: #dc322f; }
div.button {
    text-align: right; }
button, input, select {
    font-family: Inconsolata, "Ubuntu Mono", monospace; }
button {
    padding: .075em .5em; }
button, select {
    background-color: #2aa198;
    border: 0;
    color: #002b36;
    text-transform: uppercase; }
input[type=text], select {
    background-color: #073642;
    border: 0;
    color: #839496; }
ul {
    list-style: none;
    padding-left: 0; }
#setup {
    display: grid;
    grid-column-gap: 1em;
    grid-template-columns: 1fr 1fr; }
#setup input[type=text] {
    width: 100%; }
#websites li > div {
    display: grid;
    grid-column-gap: 0;
    grid-template-columns: auto auto; }
// div.domain:nth-child(odd) { background-color: #073642; }
// div.domain:nth-child(even) { background: #; }

.input_submit {
    display: grid;
    grid-column-gap: .5em;
    grid-template-columns: auto min-content; }
</style>
<title>$hostname</title>

<header>
<div>
<h1><code>$hostname</code></h1>
<p><code>$ip_address<br><small>$system_uptime</small></code></p>
</div>
<div id=tokens>
<div id=digitalocean>
    <form action=/tokens/digitalocean method=post>
    <label><strong>DigitalOcean</strong>
    <input type=text name=token
        value="$config['tokens']['digitalocean']"></label>
    <button>Set</button>
    </form>
</div>
<div id=dynadot>
    <form action=/tokens/dynadot method=post>
    <label><strong>Dynadot</strong>
    <input type=text name=token value="$config['tokens']['dynadot']"></label>
    <button>Set</button>
    </form>
</div>
<div id=github>
    <form action=/tokens/github method=post>
    <label><strong>GitHub</strong>
    <input type=text name=token value="$config['tokens']['github']"></label>
    <button>Set</button>
    </form>
</div>
</div>
</header>

<section id=setup>

<div id=applications>
<h2>Applications</h2>
<form action=/apps method=post>
    <label for=app><strong>Package</strong><br>
    <small>PyPI (eg. <kbd>canopy</kbd>) or
    Repository URL (eg. <kbd>example.org/foo.git</kbd>) or
    GitHub Path (eg. <kbd>example/foo</kbd>)</small></label>
    <div class=input_submit>
        <input id=app type=text name=app></label>
        <button>Install</button>
    </div>
</form>
$for package, (update_available, applications) in sorted(apps.items()):
    $ meta = package.metadata
    <h3>$meta["Name"] <small>$meta["Version"]</small></h3>
    <p>$meta["Summary"]
    $if "Project-URL" in meta:
        <a href=$meta["Project-URL"].split(", ")[1]>more</a>
    </p>
    $ license = meta.get("License")
    <p><small><a href=$meta["Author-email"]>$meta["Author"]</a>
    $if license:
        <small><a href=https://spdx.org/licenses/$(license).html>\
        $license</a></small>
    </small></p>
    $if update_available:
        <form action=/apps/$meta["Name"] method=post>
        <button>Upgrade to $update_available</button>
        </form>
    <ul>
    $for appns, _, mod_name, attrs in applications:
        $ app = f"{mod_name}:{attrs[0]}"
        <li><form action=/apps/$app method=post>
        $appns<br><small>$app</small>
        $if app in statuses:
            <small style=color:#859900>\
            $" ".join(statuses[app]).lower()</small>
        </form></li>
    </ul>
</div>

<div id=websites>
<h2>Websites</h2>
<form action=/sites method=post>
    <label for=site><strong>Hostname</strong><br>
    <small>Domain (eg. <kbd>example.org</kbd>) or
    Subdomain (eg. <kbd>foo.example.org</kbd>)</small></label>
    <div class=input_submit>
        <input id=site type=text name=site>
        <button>Add</button>
    </div>
</form>
<ul>
$for suffix, domain, subdomain, site, a_record, ns_records, \
certified, preloaded in sorted(sites):
    $ show_point_ns = False
    $ show_point_a = False
    $ show_certify = False
    $ show_nothing = False
    <li>
    <h3>$site.name</h3>
    <div>
    <div>
    $ site_app = config["websites"].get(site.name)
    $if site_app:
        <small style=color:#859900>
        $site_app is mounted
        $if preloaded:
            <br><abbr title="HTTP Strict Transport Security">HSTS</abbr>
            is preloaded
        </small>
    $else:
        $ points = a_record == ip_address
        $if points:
            <small style=color:#$("859900" if points else "dc322f");>\\
            <code>$a_record</code></small><br>
            $if certified:
                <small style=color:#859900;><abbr
                title="Transport Layer Security">TLS</abbr>
                enabled</small><br>
                <small style=color:#$("859900" if preloaded else "dc322f")>
                <abbr title="HTTP Strict Transport Security">HSTS</abbr>
                $("" if preloaded else "not") preloaded</small><br>
            $else:
                <small style=color:#dc322f;><abbr
                title="Transport Layer Security">TLS</abbr>
                not enabled</small><br>
                $ show_certify = True
        $else:
            <small style=color:#dc322f>
            $if a_record is None:
                no A record<br>
            $else:
                $a_record<br>
            $if "ns1.digitalocean.com." not in ns_records:
                current nameservers: <code>$", ".join(ns_records)</code><br>
                $if domain + "." + suffix in dynadot_domains:
                    $ show_point_ns = True
                $else:
                    cannot continue (\\
                    $ show_nothing = True
                    $if config["tokens"]["dynadot"]:
                        domain not found in Dynadot account)<br>
                    $else:
                        no Dynadot access)<br>
            $else:
                $ show_point_a = True
            </small>
    </div>
    <div>
        $if show_point_ns:
            <form action=/sites/$site.name/dns method=post>
            <div class=button><button>Point to DigitalOcean</button></div>
            </form>
        $elif show_point_a:
            <form action=/sites/$site.name/dns method=post>
            <div class=button><button>Point here</button></div>
            </form>
        $elif show_certify:
            <form action=/sites/$site.name/certificate method=post>
            <div class=button><button>Certify</button></div>
            </form>
        $elif show_nothing:
            $pass
        $elif not site_app:
            <form action=/sites/$site.name/mount method=post>
            <select name=app required>
            <option value="" disabled selected>Choose application..</option>
            $for package, (_, applications) in sorted(apps.items()):
                $for appns, __, mod_name, attrs in applications:
                    <option value="$(mod_name):$attrs[0]">$appns
                    $if f"{mod_name}:{attrs[0]}" in statuses:
                        (running)
                    </option>
            </select>
            <div class=button><button>Mount</button></div>
            </form>
            $# TODO HSTS preload
        $if site.name != ip_address:
            <form action=/sites/$site.name method=delete>
            <input type=hidden name=_http_method value=delete>
            <div class=button><button>Delete</button></div>
            </form>
    </div>
    </div>
    </li>
</ul>
</div>
</section>
"""
