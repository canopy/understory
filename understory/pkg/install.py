"""
install & uninstall distributions

"""

# TODO CHEESESHOP = "https://lahacker.net/software"

import os
import pkg_resources
import shlex

import pip.__main__

from . import listing

__all__ = ["add", "remove", "get_orphans"]


class VirtualEnvironmentError(Exception):

    """
    raised when an action is attemped outside a virtual environment

    """


def add(*distributions, editable=False):
    """
    instruct `pip` to install given distributions `dists`

    `pip` will automatically fetch and install required dependencies.

    """
    # TODO verify w/ GPG
    args = ["install"]
    if editable:
        args.append("-e")
    for dist in distributions:
        pipmain(*args, str(dist))
        # TODO "--no-index -f", CHEESESHOP,
        # TODO "-i https://pypi.python.org/simple/",
    write_log("installed", distributions)


def remove(*distributions, clean_reqs=False):
    """
    instruct `pip` to uninstall given `distributions`

    Set `clean_reqs` True to remove distributions' orphaned requirements.

    """
    for distribution in distributions:
        for dist in get_orphans(distribution):
            pipmain("uninstall", "-y", dist.project_name)
    write_log("remove", distributions)


def pipmain(*args):
    """"""
    status = pip.__main__._main(shlex.split(" ".join(args)))
    # XXX pip.logger.consumers = []  # reset accumulated loggers after each run
    return status


def write_log(action, distributions):
    """"""
    # TODO timestamp & sign w/ GPG
    try:
        venv_dir = os.environ["VIRTUAL_ENV"]
    except KeyError:
        raise VirtualEnvironmentError()
    with open(os.path.join(venv_dir, "package.log"), "a") as fp:
        print(f"{action}:", " ".join(str(d) for d in distributions), file=fp)


def get_orphans(distribution):
    """"""
    dist = pkg_resources.get_distribution(distribution)
    return _find_all_dead(listing.get_graph(), set([dist]))


def _find_all_dead(graph, start):
    """"""
    return _fixed_point(lambda d: _find_dead(graph, d), start)


def _fixed_point(f, x):
    """"""
    while True:
        y = f(x)
        if y == x:
            return x
        x = y


def _find_dead(graph, dead):
    """"""

    def is_killed_by_us(node):
        succ = graph[node]
        return succ and not (succ - dead)

    return dead | set(filter(is_killed_by_us, graph))
