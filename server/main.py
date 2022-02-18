"""Canopy desktop app."""

from gevent import monkey

monkey.patch_all()

import json
import logging
import os
import pathlib
import platform
import subprocess
import sys
import time
import webbrowser

import gunicorn.app.base
# VOSK from PySide6.QtCore import QObject, QThread
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

import canopy
from understory import loveliness, web  # VOSK voice

SYSTEM = platform.system()
LINUX, MACOS, WINDOWS = "Linux", "Darwin", "Windows"

gaea_app = None
gaea_app_dir = pathlib.Path(__file__).parent

data_dir = pathlib.Path("canopy-data").absolute()
data_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG, filename=data_dir / "run.log", filemode="w", force=True
)
logging.debug(f"system is {SYSTEM}")

canopy_port = 13579
canopy_server = None
job_queue = None

tor_server = None
tor_version = "11.0.6"
tor_browser_base_url = f"https://www.torproject.org/dist/torbrowser/{tor_version}/"
try:
    tor_browser_archive_name = {
        LINUX: f"tor-browser-linux64-{tor_version}_en-US.tar.xz",
        MACOS: f"TorBrowser-{tor_version}-osx64_en-US.dmg",
        WINDOWS: f"torbrowser-install-win64-{tor_version}_en-US.exe",
    }[SYSTEM]
except KeyError:
    print(f"ERROR: operating system `{SYSTEM}` not supported")
    sys.exit(1)
onion_dir = data_dir / "onion"
torrc = data_dir / "torrc"
tor_config = f"""SOCKSPort 9333
HiddenServiceDir {onion_dir}
HiddenServiceVersion 3
HiddenServicePort 80 127.0.0.1:{canopy_port}"""

if SYSTEM == LINUX:
    tor_dir = data_dir / "tor-browser_en-US/Browser/TorBrowser/Tor"
    mozilla_path = data_dir / "tor-browser_en-US/Browser/firefox"
elif SYSTEM == MACOS:
    ...
elif SYSTEM == WINDOWS:
    ...

mozilla_path = f"{data_dir}/tor-browser_en-US/Browser/firefox"
webbrowser.register("firefox", None, webbrowser.BackgroundBrowser(mozilla_path))

logging.debug(f"data in {data_dir}")
logging.debug(f"application in {gaea_app_dir}")


def main():
    """
    Run the main application and kick off the servers and speech listener.

    Install if necessary.

    """
    global gaea_app
    gaea_app = QApplication([])
    gaea_app.setQuitOnLastWindowClosed(False)
    icon = QIcon(f"{gaea_app_dir}/gaea.png")
    tray = QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setVisible(True)
    menu = QMenu()
    show = QAction("Show Site")
    show.triggered.connect(show_site)
    menu.addAction(show)
    quit = QAction("Quit")
    quit.triggered.connect(shut_down)
    menu.addAction(quit)
    tray.setContextMenu(menu)

    try:
        onion_dir.mkdir(0o700)
    except FileExistsError:
        pass
    else:
        install()
    spawn_servers()
    show_site()

    # VOSK speech_worker = SpeechWorker()
    # VOSK speech_listener = QThread()
    # VOSK speech_worker.moveToThread(speech_listener)
    # VOSK speech_listener.started.connect(speech_worker.listen)
    # VOSK speech_listener.start()
    return gaea_app.exec()


def install():
    """Install Tor Browser and configure a torrc."""
    logging.debug("installing...")
    web.download(
        f"{tor_browser_base_url}/{tor_browser_archive_name}",
        data_dir / tor_browser_archive_name,
    )
    if SYSTEM == LINUX:
        subprocess.run(["tar", "xf", tor_browser_archive_name], cwd=data_dir)
    elif SYSTEM == MACOS:
        subprocess.run(["hdiutil", "attach", tor_browser_archive_name], cwd=data_dir)
        # XXX browser_dir = pathlib.Path(
        # XXX     "/Volumes/Tor Browser/Tor Browser.app/Contents/Resources/TorBrowser"
        # XXX )
        # TODO move .app out of mount back to data_dir
    elif SYSTEM == WINDOWS:
        subprocess.run(
            [tor_browser_archive_name, "/S", f"/D={data_dir}\\Tor Browser"],
            cwd=data_dir,
        )
    with torrc.open("w") as fp:
        fp.write(tor_config)


def spawn_servers():
    """Run tor, canopy and its job queue."""
    global tor_server
    global canopy_server
    global job_queue
    tor_server = subprocess.Popen(
        ["./tor", "-f", torrc], cwd=tor_dir, stdout=subprocess.PIPE
    )
    if sys.argv[0].endswith("main.py"):
        command = [
            "poetry",
            "run",
            "python",
            f"{gaea_app_dir}/main.py",
        ]  # TODO "-m", "canopy"]
    else:
        command = [f"{gaea_app_dir}/understory"]
    canopy_server = subprocess.Popen(
        command + ["app"], cwd=data_dir, stdout=subprocess.PIPE
    )
    job_queue = subprocess.Popen(
        command + ["queue"], cwd=data_dir, stdout=subprocess.PIPE
    )


def show_site():
    """Open Tor Browser to user's canopy site."""
    while True:
        try:
            with (onion_dir / "hostname").open() as fp:
                onion = fp.read()
        except FileNotFoundError:
            time.sleep(0.1)
        else:
            break
    try:
        passphrase = get_config()["passphrase"]
    except KeyError:
        webbrowser.get("firefox").open(f"http://{onion}?kiosk={data_dir}")
        while True:
            try:
                with (data_dir / "passphrase").open() as fp:
                    passphrase = fp.read()
            except FileNotFoundError:
                time.sleep(0.1)
            else:
                break
        update_config(passphrase=passphrase)
    else:
        webbrowser.get("firefox").open(
            f"http://{onion}/owner/sign-in?passphrase={passphrase}"
        )


def shut_down():
    """Shut everything down and quit."""
    tor_server.kill()
    canopy_server.kill()
    job_queue.kill()
    gaea_app.quit()


def get_config():
    """Get configuration."""
    try:
        with (data_dir / "settings.json").open() as fp:
            config = json.load(fp)
    except FileNotFoundError:
        config = {}
    return config


def update_config(**items):
    """Update configuration."""
    config = get_config()
    config.update(**items)
    with (data_dir / "settings.json").open("w") as fp:
        json.dump(config, fp, indent=2, sort_keys=True)
        fp.write("\n")
    return get_config()


# VOSK class SpeechWorker(QObject):
# VOSK     """A background thread object for speech-to-text processing."""
# VOSK
# VOSK     def listen(self):
# VOSK         """Have Vosk listen on the microphone."""
# VOSK         voice.get_commands()


class StandaloneServer(gunicorn.app.base.BaseApplication):
    """A standalone gunicorn webapp context for the canopy."""

    def __init__(self):
        """Initialize standalone server."""
        self.options = {"bind": f"localhost:{canopy_port}", "workers": 2}
        self.application = canopy.app
        super().__init__()

    def load_config(self):
        """Load configuration values."""
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        """Load the application."""
        return self.application


if __name__ == "__main__":
    if len(sys.argv) == 1:
        try:
            sys.exit(main())
        except KeyboardInterrupt:
            sys.exit()
    if sys.argv[1] == "app":
        StandaloneServer().run()
    elif sys.argv[1] == "queue":
        loveliness.serve()


def build():
    """Build gaea using nuitka."""
    env = os.environ.copy()
    if platform.system() == LINUX:
        env["ARCH"] = "x86_64"
    sys.exit(
        subprocess.run(
            ["python", "-m", "nuitka", "main.py", "-o", "dist/understory"], env=env
        ).returncode
    )


# nuitka-project: --onefile

# nuitka-project-if: {OS} == "Linux":
#    nuitka-project: --linux-onefile-icon=gaea.png
# nuitka-project-if: {OS} == "Windows":
#    nuitka-project: --windows-icon-from-ico=gaea.png
# nuitka-project-if: {OS} == "Darwin":
#    nuitka-project: --macos-onefile-icon=gaea.png

# nuitka-project: --enable-plugin=pyside6

# nuitka-project: --include-package=understory
# nuitka-project: --include-package=understory.apps.micropub_server.posts
# nuitka-project: --include-package=understory.apps.micropub_server.posts.templates
# nuitka-project: --include-package=understory.web.framework.templates
# nuitka-project: --include-package=understory.host.templates
# nuitka-project: --include-package=canopy
# nuitka-project: --include-package=canopy.templates
# nuitka-project: --include-package=gevent.signal
# nuitka-project: --include-package=gunicorn.glogging
# nuitka-project: --include-package=gunicorn.workers.sync
# nuitka-project: --include-package-data=understory
# nuitka-project: --include-package-data=understory.apps.micropub_server.posts
# nuitka-project: --include-package-data=canopy
# nuitka-project: --include-package-data=mf2py
# nuitka-project: --include-package-data=selenium
