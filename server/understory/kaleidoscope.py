"""Canopy device management."""

# TODO async_add_torrent/add_torrent_alert

import argparse
import json
import pathlib
import signal
import sqlite3
import sys
import time

try:
    import libtorrent
except ImportError:
    import warnings

    warnings.warn("libtorrent could not be loaded")

# TODO handle.file_priorities()

__all__ = ["start_client"]


save_path = pathlib.Path("./")
dht_bootstraps = ["router.bittorrent.com:6881"]
max_download, max_upload = -1, -1  # -1 = no limit; 4000 = 4kb/s
statistics = ("state", "download_rate", "upload_rate", "total_download", "total_upload")


def start_client(port):
    """Run the BitTorrent client."""
    dbconn = sqlite3.connect("torrents.db")
    db = dbconn.cursor()

    session = libtorrent.session()
    try:
        with (save_path / ".bt-session").open("rb") as fp:
            session.load_state(libtorrent.bdecode(fp.read()))
    except FileNotFoundError:
        pass
    settings = libtorrent.session_settings()
    settings.user_agent = f"bt/{libtorrent.version}"
    session.set_settings(settings)
    session.listen_on(port, port)  # XXX + 10)
    for dht_server in dht_bootstraps:
        dht_host, dht_port = dht_server.split(":")
        session.add_dht_router(dht_host, int(dht_port))
    session.start_dht()
    session.set_download_rate_limit(max_download)
    session.set_upload_rate_limit(max_upload)
    session.set_severity_level(libtorrent.alert.severity_levels.info)
    session.add_extension(libtorrent.create_ut_pex_plugin)
    session.add_extension(libtorrent.create_ut_metadata_plugin)
    session.add_extension(libtorrent.create_metadata_plugin)
    # XXX session.add_extension(lambda x: PythonExtension(alerts))

    def add_torrent(**details):
        storage_mode = libtorrent.storage_mode_t.storage_mode_sparse
        details.update(
            storage_mode=storage_mode,
            auto_managed=True,
            duplicate_is_error=True,
            save_path=str(save_path),
        )
        if details.get("resume_data") is None:
            details.pop("resume_data", None)
        handle = session.add_torrent(details)
        handle.set_max_connections(60)
        handle.set_max_uploads(-1)
        handle.set_ratio(0)
        return handle

    try:
        torrents = db.execute("SELECT * FROM torrents")
    except sqlite3.OperationalError:
        db.execute("""CREATE TABLE incoming (url TEXT)""")
        db.execute(
            """CREATE TABLE torrents (info_hash TEXT, magnet TEXT,
                                             fast_resume TEXT)"""
        )
        db.execute("""CREATE TABLE stats (info_hash TEXT, stats TEXT)""")
    else:
        for torrent in torrents:
            add_torrent(url=torrent[1], resume_data=torrent[2])

    def handle_exit(*args):
        for handle in session.get_torrents():
            # if not handle.is_valid() or not handle.has_metadata():
            #     continue
            handle.pause()
            db.execute(
                """UPDATE torrents SET fast_resume = ? WHERE info_hash = ?""",
                (
                    libtorrent.bencode(handle.write_resume_data()),
                    str(handle.info_hash()),
                ),
            )
            dbconn.commit()
        with (save_path / ".bt-session").open("wb") as fp:
            fp.write(libtorrent.bencode(session.save_state()))
        dbconn.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    try:
        while True:
            while True:
                alert = session.pop_alert()
                if not alert:
                    break
                try:
                    alert_message = alert.message()
                except AttributeError:
                    alert_message = alert
                if alert_message.startswith(":"):
                    continue
                # print(">", alert_message)  # TODO silence some output
            for (url,) in db.execute("SELECT url FROM incoming"):
                if url.startswith(
                    ("https://www.youtube.com/watch?v=", "https://youtu.be/qwi6XzjB00I")
                ):
                    url, _, format_code = url.rpartition("|")
                    sh.youtube_dl(url, "-f", format_code, _bg=True)
                    continue
                try:
                    handle = add_torrent(url=url)
                except RuntimeError:  # torrent already exists in session
                    continue
                # TODO pause until torrent info has been fetched from DHT?
                # while not handle.has_metadata():
                #     time.sleep(.1)
                print("added torrent:", handle.name())
                db.execute(
                    """INSERT INTO torrents (info_hash, magnet)
                              VALUES (?, ?)""",
                    (str(handle.info_hash()), url),
                )
                db.execute("DELETE FROM incoming WHERE url = ?", (url,))
                dbconn.commit()
            for lockfile in pathlib.Path("stats").glob("*.lock"):
                # if filepath.suffix == ".data":
                #     continue
                info_hash = lockfile.stem
                stats = {"torrents": {}}
                for handle in session.get_torrents():
                    if info_hash != "all" and str(handle.info_hash()) != info_hash:
                        continue
                    status = {k: str(getattr(handle.status(), k)) for k in statistics}

                    # TODO async or break after 3 seconds
                    # while True:
                    #     torrent_info = handle.get_torrent_info()
                    #     if torrent_info is not None:
                    #         break
                    #     time.sleep(.1)

                    torrent_info = handle.get_torrent_info()

                    if torrent_info:
                        file_info = torrent_info.files()
                        files = list(
                            zip(
                                (
                                    (file_info.file_path(n), file_info.file_size(n))
                                    for n in range(file_info.num_files())
                                ),
                                handle.file_progress(),
                            )
                        )
                    else:
                        files = []
                    stats["torrents"][str(handle.info_hash())] = [
                        handle.name(),
                        status["state"],
                        status["download_rate"],
                        status["upload_rate"],
                        status["total_download"],
                        status["total_upload"],
                        files,
                    ]
                with open(f"stats/{info_hash}.data", "w") as fp:
                    json.dump(stats, fp)
                lockfile.unlink()
            time.sleep(0.5)
    except KeyboardInterrupt:
        handle_exit()


def get_stats(info_hash="all"):
    """Return stats for torrent with info_hash otherwise all torrents."""
    lock_path = pathlib.Path(f"stats/{info_hash}.lock")
    lock_path.touch()
    while lock_path.exists():
        pass
    data_path = pathlib.Path(f"stats/{info_hash}.data")
    with data_path.open() as fp:
        data = fp.read()
    data_path.unlink()
    return data


def main():
    parser = argparse.ArgumentParser()
    contexts = parser.add_subparsers()

    start_client_p = contexts.add_parser("start-client", help="start client")
    start_client_p.set_defaults(context="start-client")

    get_stats_p = contexts.add_parser("get-stats", help="get statistics")
    get_stats_p.set_defaults(context="get-stats")
    get_stats_p.add_argument("info_hash", nargs="?", help="specify a specific torrent")

    args = parser.parse_args()
    try:
        context = args.context
    except AttributeError:
        parser.exit(1)

    if context == "start-client":
        # with open("/tmp/vpnportfw") as fp:
        #     port = int(fp.read())  # 6881
        port = 6881
        start_client(port)
    elif context == "get-stats":
        try:
            stats = get_stats(args.info_hash)
        except AttributeError:
            stats = get_stats()
        print(stats)

    parser.exit(0)


if __name__ == "__main__":
    main()
