"""
list distributions

"""

import collections
import json
import os
import pathlib
import re

import pkg_resources

from .discover import PackageRepoError, gitsh

__all__ = ["get_graph", "get_distributions", "get_distribution"]


def get_graph():
    """
    return a dict mapping env's installed distributions to their requirements

    """
    graph = {dist: set() for dist in pkg_resources.working_set}
    for dist in pkg_resources.working_set:
        for req in _requires(dist):
            graph[req].add(dist)
    return graph


def _requires(dist):
    """"""
    return [pkg_resources.get_distribution(d) for d in dist.requires()]


def get_distributions(dependencies=False):
    """
    return a list of installed distributions

    """
    if dependencies:
        return list(pkg_resources.Environment())
    return [
        dist.project_name
        for dist, required_by in get_graph().items()
        if not required_by
    ]
    # and not dist.location.startswith("/usr/lib/")]


def get_distribution(name):
    """
    return a dictionary containing details of given installed distribution

        >>> dist = get_distribution("understory")
        >>> dist["name"]
        'understory'

    # >>> dist["home-page"]
    # 'https://angelo.lahacker.net/software/source/projects/belle'
    # >>> dist["summary"]
    # 'a library for software packaging'
    # >>> dist["license"]
    # 'GNU Affero General Public License v3'

    """
    return Distribution(name)


class Distribution:

    """ """

    def __init__(self, name):
        dist = pkg_resources.get_distribution(name)
        self.location = pathlib.Path(dist.location)
        # TODO check if system installation
        try:
            env = pathlib.Path(os.environ["VIRTUAL_ENV"]).resolve()
        except KeyError:
            env = None
        self.in_env = self.location in env.parents if env else False

        try:
            key = None
            metadata = {}
            for match in re.split(
                r"^([A-Z][A-Za-z-]+): ",
                dist.get_metadata("PKG-INFO"),
                flags=re.MULTILINE,
            )[3:]:
                if key:
                    metadata[key.lower()] = match.rstrip()
                    key = None
                else:
                    key = match
        except FileNotFoundError:
            try:
                metadata = json.loads(dist.get_metadata("metadata.json"))
            except FileNotFoundError:
                try:
                    metadata = json.loads(dist.get_metadata("pydist.json"))
                except FileNotFoundError:
                    metadata = {
                        "name": dist.project_name,
                        "version": dist.version,
                        "summary": "",
                    }
        details = {
            "name": metadata["name"],
            "version": metadata["version"],
            "summary": metadata["summary"],
            "license": metadata.get("license", "UNKNOWN"),
            "url": metadata.get("home-page", ""),
            "download_url": metadata.get("download-url", ""),
            "people": collections.defaultdict(dict),
        }

        if "contacts" in metadata:  # for flake8 & requests package formats
            for contact in metadata["contacts"]:
                person = details["people"][contact["name"]]
                person[contact["role"]] = contact["email"]
        else:
            try:
                author = metadata["author"]
                author_email = metadata["author-email"]
                details["people"][author]["author"] = author_email
            except KeyError:
                pass
            try:
                maintainer = metadata["maintainer"]
                maintainer_email = metadata["maintainer-email"]
                details["people"][maintainer]["maintainer"] = maintainer_email
            except KeyError:
                pass
        details["people"] = dict(details["people"])

        try:
            dep_links = dist.get_metadata("dependency_links.txt")
            details["deps"] = dep_links.strip().splitlines()
        except (KeyError, FileNotFoundError):
            pass
        mods = []
        try:
            mods = dist.get_metadata("top_level.txt").strip().splitlines()
        except (KeyError, FileNotFoundError):
            pass
        finally:
            details["mods"] = [mod for mod in mods if mod != "tests"]
            details["reqs"] = {
                r.project_name: [[list(s) for s in r.specs], list(r.extras)]
                for r in dist.requires()
            }
            details["entry-points"] = entry_points = dict(dist.get_entry_map())
            for group, group_eps in dist.get_entry_map().items():
                entry_points[group] = {
                    n: (ep.module_name, ep.attrs) for n, ep in group_eps.items()
                }
        self.details = details

    def __getitem__(self, name):
        return self.details[name]

    def is_dirty(self):
        """ """
        try:
            dirty = bool(gitsh("status --porcelain", self.location))
        except PackageRepoError:
            dirty = False
        return dirty
