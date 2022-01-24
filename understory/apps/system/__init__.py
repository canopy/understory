""""""

import lxml
import pkg_resources
import requests
import semver
import sh
from understory import web
from understory.web import tx

app = web.application(__name__, prefix="system")


def get_versions(package):
    """Return the latest version if currently installed `package` is out of date."""
    current_version = pkg_resources.get_distribution(package).version
    current_version = current_version.partition("a")[0]  # TODO FIXME strips alpha/beta
    update_available = False
    versions_rss = lxml.etree.fromstring(
        requests.get(
            f"https://pypi.org/rss/project/{package}/releases.xml"
        ).text.encode("utf-8")
    )
    latest_version = [
        child.getchildren()[0].text
        for child in versions_rss.getchildren()[0].getchildren()
        if child.tag == "item"
    ][0]
    if semver.compare(current_version, latest_version) == -1:
        update_available = latest_version
    return current_version, update_available


@app.control("")
class System:
    """Render information about the application structure."""

    def get(self):
        return app.view.index(tx.app, get_versions("understory"), web.get_apps())


def update_system():
    """Update system software."""
    sh.sudo("supervisorctl", "stop", "canopy-app")
    # TODO finish current jobs & pause job queue
    sh.sudo(
        "/root/runinenv",
        "/root/canopy",
        "pip",
        "install",
        "-U",
        "understory",
    )
    sh.sudo("supervisorctl", "start", "canopy-app")
    # TODO XXX sh.sudo("supervisorctl", "restart", "canopy-app-jobs", _bg=True)


@app.control("update")
class Update:
    """"""

    def post(self):
        web.enqueue(update_system)
        raise web.Accepted(app.view.update())
