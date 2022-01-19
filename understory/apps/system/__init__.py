""""""

import pkg_resources
import semver
import sh
from understory import web
from understory.web import tx

app = web.application(__name__, prefix="system")


def get_versions(package):
    """Return the latest version if currently installed `package` is out of date."""
    import feedparser  # FIXME here for nuitka

    current_version = pkg_resources.get_distribution(package).version
    current_version = current_version.partition("a")[0]  # TODO FIXME strips alpha/beta
    update_available = False
    versions_url = f"https://pypi.org/rss/project/{package}/releases.xml"
    versions = feedparser.parse(versions_url)["entries"]
    try:
        latest_version = versions[0]["title"]
    except IndexError:
        pass  # TODO fallback to query from GitHub API
    else:
        if semver.compare(current_version, latest_version) == -1:
            update_available = latest_version
    return current_version, update_available


@app.control("")
class System:
    """Render information about the application structure."""

    def get(self):
        applications = web.get_apps()
        understory_version = pkg_resources.get_distribution("understory").version
        return app.view.index(
            tx.app,
            get_versions("canopy-platform"),
            get_versions("understory"),
            applications,
        )


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
        "canopy-platform",
    )
    sh.sudo("supervisorctl", "start", "canopy-app")
    # TODO XXX sh.sudo("supervisorctl", "restart", "canopy-app-jobs", _bg=True)


@app.control("update")
class Update:
    """"""

    def post(self):
        web.enqueue(update_system)
        raise web.Accepted(app.view.update())
