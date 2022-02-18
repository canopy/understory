"""
Tools for metamodern software packaging.

"""

from pkg_resources import DistributionNotFound
from pkg_resources import iter_entry_points as get_entry_points

from .discover import auto_discover, discover, get_repo_files
from .install import add, remove
from .listing import get_distribution
from .system import get_apt_history

__all__ = [
    "DistributionNotFound",
    "get_entry_points",
    "add",
    "remove",
    "auto_discover",
    "discover",
    "get_repo_files",
    "get_apt_history",
    "get_distribution",
]


def detail_package(self):
    """
    a knowledge tree extension for detailing the contents of Python packages

    """
    packages = []

    def handle(file):
        z = discover(file)
        print(z)
        yield
        print("XXX")
        yield

    def summarize():
        print("{} packages found: {}".format(len(packages), ", ".join(packages)))

    return handle, summarize
