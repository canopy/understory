"""Spawn and manage servers."""

import configparser
import io
import json
import os
import pathlib
import random
import textwrap
import time
import webbrowser

from understory import web

try:
    import sh
except ImportError:
    pass

from . import digitalocean, providers


class TokenError(Exception):
    """Bad Dynadot auth token."""


__all__ = ["digitalocean", "dynadot", "Gaea", "main", "spawn_gaea", "spawn_understory"]

STARTED = False
DHPARAM_BITS = 512  # FIXME 4096 for production (perform in bg post install)
SSL_CIPHERS = ":".join(
    (
        "ECDHE-RSA-AES256-GCM-SHA512",
        "DHE-RSA-AES256-GCM-SHA512",
        "ECDHE-RSA-AES256-GCM-SHA384",
        "DHE-RSA-AES256-GCM-SHA384",
        "ECDHE-RSA-AES256-SHA384",
    )
)
system_dir = "/root"
etc_dir = "/root/etc"
src_dir = "/root/src"
var_dir = "/root/var"
nginx_dir = "/root/nginx"
APTITUDE_PACKAGES = (
    "ufw",
    "build-essential",  # build tools
    "libbz2-dev",  # bz2 support
    "libicu-dev",
    "python3-icu",  # SQLite unicode collation
    "libsqlite3-dev",  # SQLite Python extension loading
    "python3-dev",  # Python build dependencies
    "cargo",  # rust (pycryptography)
    "libffi-dev",  # rust (pycryptography)
    "zlib1g-dev",
    "python3-cryptography",  # pycrypto
    "python3-libtorrent",  # libtorrent
    "zip",  # .zip support
    "expect",  # ssh password automation
    "psmisc",  # killall
    "xz-utils",  # .xz support
    "git",
    "fcgiwrap",  # Git w/ HTTP serving
    "supervisor",  # service manager
    "redis-server",  # Redis key-value database
    "haveged",  # produces entropy for faster key generation
    "sqlite3",  # SQLite flat-file relational database
    "libssl-dev",  # uWSGI SSL support
    "ffmpeg",  # a/v en/de[code]
    "imagemagick",  # heic -> jpeg
    "libsm-dev",
    "python-opencv",  # opencv
    "libevent-dev",  # Tor
    "pandoc",  # markup translation
    "graphviz",  # graphing
    "libgtk-3-0",
    "libdbus-glib-1-2",  # Firefox
    "xvfb",
    "x11-utils",  # browser automation
    "libenchant-dev",  # pyenchant => sopel => bridging IRC
    "tmux",  # automatable terminal multiplexer
    "tree",
    "htop",
    "stow",  # for dotfiles
    "zsh",  # default shell
)
VERSIONS = {
    "python": "3.9.2",
    "nginx": "1.18.0",
    "tor": "0.4.4.5",
    "firefox": "82.0",
    "geckodriver": "0.27.0",
}
templates = web.templates(__name__)


# def spawn_gaea(ip_address):
#     """Spawn a gaea node for bootstrapping purposes."""
#     ssh = digitalocean.get_ssh("root", ip_address, process_out(ip_address))
#     upgrade_system(ip_address)
#     install_packages(ip_address, "nginx")
#     setup_firewall(ip_address)
#     ssh("rm /var/www/html/index.nginx-debian.html")
#     ssh(
#         f"echo '<p><code>This is a <a href=https://understory.cloud/gaea>gaea</a>"
#         f" bootstrap server.</code></p>' > /var/www/html/index.html"
#     )
#     # TODO send webmention
#     ssh("mkdir /root/src")


# XXX def _init_gaea():  # XXX
# XXX     ssh("apt install fuse -y")  # TODO try again on error (dpkg lock)
# XXX     # TODO XXX digitalocean.scp("gaea", f"gaea@{ip_address}:")
# XXX     gaea_ssh = digitalocean.get_ssh("gaea", ip_address, process_out(ip_address))
# XXX     gaea_ssh("wget http://137.184.4.213/dists/gaea")
# XXX     gaea_ssh("chown gaea:gaea gaea")
# XXX     gaea_ssh("chmod u+x gaea")
# XXX     gaea_ssh(f"./gaea setup {digitalocean_token}")


def spawn_machine(name, digitalocean_token):
    """
    Spawn a new machine for understory purposes.

    Currently supports Digital Ocean.

    """
    cli = digitalocean.Client(digitalocean_token)
    key = digitalocean.get_key(cli)
    droplet = cli.create_droplet(name, size="1gb", ssh_keys=[key["id"]])
    digitalocean.wait(cli, droplet["id"])
    droplet = cli.get_droplet(droplet["id"])
    ip_address = None
    for ip_details in droplet["networks"]["v4"]:
        if ip_details["type"] == "public":
            ip_address = ip_details["ip_address"]
            break
    return ip_address


def setup_machine(ip_address):
    ssh = digitalocean.get_ssh("root", ip_address, process_out(ip_address))
    upgrade_system(ip_address)
    install_packages(ip_address, *APTITUDE_PACKAGES)
    setup_firewall(ip_address)
    ssh("adduser gaea --disabled-login --gecos gaea")  # TODO --shell /usr/bin/zsh")
    ssh('echo "gaea  ALL=NOPASSWD: ALL" | tee -a /etc/sudoers.d/01_gaea')
    gaea_ssh_dir = "/home/gaea/.ssh"
    ssh(f"mkdir {gaea_ssh_dir}")
    ssh(f"cp /root/.ssh/authorized_keys {gaea_ssh_dir}")
    ssh(f"chown gaea:gaea {gaea_ssh_dir} -R")
    ssh("mkdir /root/src /root/etc")


def upgrade_system(ip_address):
    """Upgrade aptitude and install new system-level dependencies."""
    ssh = digitalocean.get_ssh("root", ip_address, process_out(ip_address))
    ssh(
        "apt-get -o DPkg::Lock::Timeout=60 update",
        env={"DEBIAN_FRONTEND": "noninteractive"},
    )
    ssh(
        "apt-get -o DPkg::Lock::Timeout=60 dist-upgrade -yq",
        env={"DEBIAN_FRONTEND": "noninteractive"},
    )


def install_packages(ip_address, *packages):
    """"""
    ssh = digitalocean.get_ssh("root", ip_address, process_out(ip_address))
    ssh(
        "apt-get -o DPkg::Lock::Timeout=60 install -yq " + " ".join(packages),
        env={"DEBIAN_FRONTEND": "noninteractive"},
    )


def setup_firewall(ip_address):
    """Wall off everything but SSH and web."""
    ssh = digitalocean.get_ssh("root", ip_address, process_out(ip_address))
    ssh("ufw allow proto tcp from any to any port 22")
    ssh("ufw allow proto tcp from any to any port 80,443")
    ssh("ufw --force enable")


def _build(ip_address, archive_url, *config_args):
    archive_filename = archive_url.rpartition("/")[2]
    archive_stem = archive_filename
    for ext in (".gz", ".xz", ".bz2", ".tar"):
        if archive_stem.endswith(ext):
            archive_stem = archive_stem[: -len(ext)]
    # archive_file = f"{src_dir}/{archive_filename}"
    archive_dir = f"{src_dir}/{archive_stem}"
    # if not (archive_file.exists() and archive_dir.exists()):
    #     log(f"installing {archive_stem.capitalize().replace('-', ' ')}")
    # if not archive_file.exists():
    ssh = digitalocean.get_ssh("root", ip_address, process_out(ip_address))
    log(" ", "downloading")
    tries = 0
    while True:
        try:
            ssh(f"cd {src_dir} && wget https://{archive_url}")
        except sh.ErrorReturnCode_1:
            tries += 1
            if tries == 3:
                raise  # fail with traceback for bug reporting
            time.sleep(3)
            continue
        break
    # if not archive_dir.exists():
    log(" ", "extracting")
    ssh(f"cd {src_dir} && tar xf {archive_filename}")
    log(" ", "configuring")
    ssh(f"cd {archive_dir} && bash ./configure {' '.join(config_args)}")
    log(" ", "making")
    ssh(f"cd {archive_dir} && make")
    log(" ", "installing")
    ssh(f"cd {archive_dir} && make install")


def setup_python(ip_address):
    """
    Install Python (w/ SQLite extensions).

    Additionally create a virtual environment and the web package.

    """
    version = VERSIONS["python"]
    _build(
        ip_address,
        f"python.org/ftp/python/{version}/Python-{version}.tar.xz",
        "--enable-loadable-sqlite-extensions",
        "--prefix=/root/python",
    )
    return version


def setup_canopy(ip_address):
    ssh = digitalocean.get_ssh("root", ip_address, process_out(ip_address))
    log("creating primary virtual environment")
    ssh("/root/python/bin/python3 -m venv /root/canopy")
    return

    # if self.env_dir.exists():
    #     return
    # log("creating primary virtual environment")
    get_python_sh()("-m", "venv", self.env_dir)
    sh.echo(
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            VENV=$1
            . ${VENV}/bin/activate
            shift 1
            exec "$@"
            deactivate"""
        ),
        _out=f"{self.home_dir}/runinenv",
    )
    sh.chmod("+x", self.home_dir / "runinenv")

    # log("installing SQLite")
    # log(" ", "downloading")
    # sh.wget("https://www.sqlite.org/src/tarball/sqlite.tar.gz", _cwd=self.src_dir)
    # log(" ", "extracting")
    # sh.tar("xf", "sqlite.tar.gz", _cwd=self.src_dir)
    # sqlite_dir = self.src_dir / "sqlite"
    # log(" ", "configuring")
    # sh.bash("./configure", _cwd=sqlite_dir)
    # sh.make("sqlite3.c", _cwd=sqlite_dir)
    # sh.git("clone", "https://github.com/coleifer/pysqlite3", _cwd=self.src_dir)
    # pysqlite_dir = self.src_dir / "pysqlite3"
    # sh.cp(sqlite_dir / "sqlite3.c", ".", _cwd=pysqlite_dir)
    # sh.cp(sqlite_dir / "sqlite3.h", ".", _cwd=pysqlite_dir)
    # sh.sh(
    #     self.home_dir / "runinenv",
    #     self.env_dir,
    #     "python",
    #     "setup.py",
    #     "build_static",
    #     _cwd=pysqlite_dir,
    # )
    # sh.sh(
    #     self.home_dir / "runinenv",
    #     self.env_dir,
    #     "python",
    #     "setup.py",
    #     "install",
    #     _cwd=pysqlite_dir,
    # )

    log("installing Gaea")
    sh.sh(
        self.home_dir / "runinenv",
        self.env_dir,
        "pip",
        "install",
        "libgaea",
    )

    log("installing Poetry")
    get_python_sh()(
        sh.wget(
            "https://raw.githubusercontent.com/python-poetry/poetry"
            "/master/install-poetry.py",
            "-q",
            "-O",
            "-",
        ),
        "-",
    )


def setup_nginx(ip_address):
    """Install Nginx (w/ TLS, HTTPv2, RTMP) for web serving."""
    version = VERSIONS["nginx"]
    nginx_src = f"nginx-{version}"
    # if (self.src_dir / nginx_src).exists():
    #     return
    ssh = digitalocean.get_ssh("root", ip_address, process_out(ip_address))
    mod_url = "https://github.com/sergey-dryabzhinsky/nginx-rtmp-module/archive/dev.zip"
    ssh(f"cd {src_dir} && wget {mod_url} -O nginx-rtmp-module.zip")
    ssh(f"cd {src_dir} && unzip -qq nginx-rtmp-module.zip")
    _build(
        ip_address,
        f"nginx.org/download/{nginx_src}.tar.gz",
        "--with-http_ssl_module",
        "--with-http_v2_module",
        f"--add-module={src_dir}/nginx-rtmp-module-dev",
        f"--prefix={nginx_dir}",
    )
    ssh(f"mkdir -p {nginx_dir}/conf/conf.d")
    # XXX web.enqueue(generate_dhparam, ip_address)
    ssh("cat > /root/nginx/conf/nginx.conf", stdin=str(templates.nginx()))
    return version


def generate_dhparam(ip_address):
    """
    Generate a unique Diffie-Hellman prime for Nginx.

    This functionality has been abstracted here in order to allow an
    administrator to regenerate a cloned system's dhparam.

    """
    # if not (self.nginx_dir / "conf/dhparam.pem").exists():
    log("generating a large prime for TLS..")
    ssh = digitalocean.get_ssh("root", ip_address, process_out(ip_address))
    ssh(f"openssl dhparam -out {nginx_dir}/conf/dhparam.pem {DHPARAM_BITS}")


def setup_supervisor(ip_address):
    """Initialize a supervisor configuration."""
    supervisor = configparser.ConfigParser()
    supervisor["program:nginx"] = {
        "autostart": "true",
        "command": f"{nginx_dir}/sbin/nginx",
        "stopsignal": "INT",
        "user": "root",
    }

    # XXX command = (f"{self.home_dir}/runinenv {self.env_dir} "
    # XXX            f"loveliness serve")
    # XXX supervisor["program:gaea-jobs"] = {"autostart": "true",
    # XXX                                     "command": command,
    # XXX                                     "directory": (self.apps_dir /
    # XXX                                                   "gaea-app"),
    # XXX                                     "stopsignal": "INT",
    # XXX                                     "user": "gaea"}

    # TODO supervisor[f"program:tor"] = {"autostart": "true",
    # TODO                               "command": bin_dir / "tor",
    # TODO                               "stopsignal": "INT",
    # TODO                               "user": "gaea"}
    _write_supervisor_conf(ip_address, "servers", supervisor)
    return True


def _write_supervisor_conf(ip_address, name, config):
    ssh = digitalocean.get_ssh("root", ip_address)
    conf_path = f"{etc_dir}/{name}.conf"
    output = io.StringIO()
    config.write(output)
    ssh(f"cat > {conf_path}", stdin=output.getvalue())
    ssh(f"ln -sf {conf_path} /etc/supervisor/conf.d/{name}.conf")
    ssh("supervisorctl", "reread")
    ssh("supervisorctl", "update")


def setup_tor(ip_address):
    """Install Tor for anonymous hosting."""
    ssh = digitalocean.get_ssh("root", ip_address)
    version = VERSIONS["tor"]
    tor_dir = f"tor-{version}"
    if ssh(f"test -f {src_dir}/{tor_dir}").returncode == 0:
        return
    _build(
        ip_address,
        f"dist.torproject.org/{tor_dir}.tar.gz",
        f"--prefix={system_dir}",
    )
    ssh(f"mkdir -p {var_dir}/tor")
    return version


# def spawn_local():
#     # sh.sudo("bash", "spawn.sh")  # TODO FIXME
#
#     # sh.scp("-i", "gaea_key", "gaea", "gaea@localhost:")
#
#     # TODO sh bake
#     def ssh(command):
#         sh.ssh(
#             "gaea@localhost", "-i", "gaea_key", command,
#             _out=process_out("localhost")
#         )
#
#     # ssh("chown gaea:gaea gaea")
#     # ssh("chmod u+x gaea")
#     ssh("./gaea setup")


def process_out(host):
    def process(line):
        if "?secret=" in line:
            secret = line.partition("=")[2]
            # TODO osx appends a trailing newline (?)
            webbrowser.open(f"https://{host}?secret={secret}")
        print(line, end="", flush=True)

    return process


def log(*args, **kwargs):
    """Print with a prefixed elapsed time indicator."""
    if STARTED:
        total_seconds = int(time.time() - STARTED)
        minutes = int(total_seconds / 60)
        seconds = total_seconds % 60
        print(f"{minutes: 3d}:{seconds:02d}", *args, **kwargs)
    else:
        print(*args, **kwargs)
