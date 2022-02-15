"""
interrogate debian system packages

"""

# TODO use `src.git` to interrogate `etckeeper` git log

__all__ = ["get_apt_history"]


def get_apt_history():
    """"""
    log = []
    with open("/var/log/apt/history.log") as fp:
        contents = fp.read().strip()
        if contents:
            for raw_entry in fp.read().strip().split("\n\n"):
                log.append(
                    dict(line.partition(": ")[::2] for line in raw_entry.split("\n"))
                )
    return log
