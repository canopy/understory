"""Packaging tools for the terminal."""

import json
import os
import pathlib

import sh

from understory import pkg
from understory import term


main = term.application("pkg", pkg.__doc__)


def complete_distname(prefix, **kwargs):
    return (
        dist.project_name
        for dist in pkg.listing.get_environment()
        if dist.startswith(prefix)
    )


@main.register()
class Test:
    """Test a package."""

    def run(self, stdin, log):
        print(
            sh.poetry(
                "run",
                "pytest-gevent",
                "--doctest-modules",
                doctest_glob="README*",
                cov=".",
            )
        )


@main.register()
class Commit:
    """Commit a change to the package."""

    def run(self, stdin, log):
        pass  # TODO pare down publish to only push


@main.register()
class Publish:
    """Publish a package to PyPI and GitHub."""

    def setup(self, add_arg):
        add_arg(
            "rule",
            choices=["patch", "minor", "major"],
            help="increment to bump the version",
        )

    def run(self, stdin, log):
        stashed = False
        try:
            sh.git("diff", "--quiet")
        except sh.ErrorReturnCode_1:
            if input("Repo is dirty! Stash? [y/N] ").lower() == "y":
                sh.git("stash", "push", "--keep-index")
                stashed = True
            else:
                return 1
        try:
            print(
                sh.poetry(
                    "run",
                    "pytest",
                    "--doctest-modules",
                    doctest_glob="README*",
                    cov=".",
                )
            )
        except sh.ErrorReturnCode_5:
            pass
        env = os.environ.copy()
        env.update(NO_COLOR="1", GH_PAGER="cat")
        private = json.loads(
            str(sh.gh("repo", "view", "--json", "isPrivate", _env=env))
        )["isPrivate"]
        print(sh.poetry("version", self.rule))
        print(sh.poetry("build"))
        if not private:
            print(sh.poetry("publish"))
        version = str(sh.poetry("version", "-s")).strip()
        print(sh.git("commit", "-a", "-m", f"Release {version}"))
        print(sh.git("push"))
        dist_dir = (
            pathlib.Path(str(sh.git("rev-parse", "--show-toplevel")).strip()) / "dist"
        )
        asset = str(sh.tail(sh.grep(sh.ls("-1tr", dist_dir), ".whl"), "-n1")).strip()
        try:
            previous_version_string = (
                str(sh.git("describe", "--tags", abbrev=0)).strip() + ".."
            )
        except sh.ErrorReturnCode_128:
            previous_version_string = ""
        changelog = sh.git(
            "--no-pager",
            "log",
            "--no-color",
            f"{previous_version_string}HEAD^",
            "--oneline",
            "--no-decorate",
        )
        print(sh.gh("release", "create", version, f"dist/{asset}", notes=changelog))
        print(sh.git("pull"))
        print(f"Published release {version}!")
        if stashed:
            try:
                sh.git("stash", "pop", "--index")
            except sh.ErrorReturnCode_1:
                pass
            sh.git("mergetool", "pyproject.toml")
        return 0


@main.register()
class List:

    """list installed distributions"""

    def setup(self, add_arg):
        add_arg(
            "dists",
            nargs="*",
            completer=complete_distname,
            help="name of distribution(s) to list",
        )
        add_arg("-d", "--deps", action="store_true", help="include dependencies")
        add_arg(
            "-v", "--verbosity", action="count", default=0, help="show more details"
        )

    def run(self, stdin, log):
        get_dist = pkg.listing.get_distributions
        for dist in sorted(
            self.dists if self.dists else get_dist(dependencies=self.deps)
        ):
            self.print_dist(dist)
        return 0

    def print_dist(self, dist):
        d = pkg.listing.get_distribution(dist)
        details = d.details
        name = details.pop("name")
        version = details.pop("version")
        if not self.machine:
            print("/c/{}".format(name), end=" ")

        def machined_print(
            *prefixes, value, color="d,w", prefix=True, indent="", end="\n"
        ):
            """
            machinable human output

            """
            prefixes = list(prefixes)
            if self.machine:
                prefixes.insert(0, name)
                end = "\n"
            else:
                if len(prefixes) > 1:
                    prefixes = prefixes[1:]
                if not prefix:
                    prefixes = []

            padding = " " if prefixes and not self.machine else ""

            if isinstance(value, list):
                _vals = ["/{}/{}/X/".format(color, v) for v in value]
                value = [padding + (" " if self.machine else ", ").join(_vals)]
            else:
                value = ["{}/{}/{}/X/".format(padding, color, value)]
            if not self.machine and indent:
                try:
                    indent = " " * indent
                except TypeError:
                    pass
                print(indent, end="")

            print(
                *(["/lg/{}/X/".format(p) for p in prefixes] + value),
                sep="/X//lg/:/X/",
                end=end,
            )

        machined_print(
            "version",
            value=version,
            color="lr,Cle",
            prefix=None,
            end=": " if self.verbosity else "",
        )

        if self.verbosity:
            summary = details.pop("summary")
            if summary.lower().startswith(name + " "):
                summary = summary[len(name) :].lstrip(":")
            summary = summary.strip(". ")
            machined_print("summary", value=summary, prefix=None)

            reqs = sorted(details["reqs"])
            if reqs:
                machined_print("requires", value=reqs, color="lm", indent=2)

            mods = sorted(details["mods"])
            if mods:
                machined_print("provides", value=mods, color="m", indent=2)
            entrances = details["entry-points"]
            if "term.apps" in entrances:
                entrances.pop("console_scripts", None)
            else:
                try:
                    entrances["term.apps"] = entrances["console_scripts"]
                    entrances.pop("console_scripts")
                except KeyError:
                    pass
            if entrances:
                for e_cls, e_points in sorted(entrances.items()):
                    if self.machine:
                        for e_pnt, e_obj in sorted(e_points.items()):
                            o = "{}={}:{}".format(e_pnt, e_obj[0], e_obj[1][0])
                            machined_print(
                                "entrances", e_cls, indent=4, color="g", value=o
                            )
                    else:
                        indent = 6 + len(e_cls)
                        joiner = "\n" + (" " * (indent))
                        o = joiner.join(
                            "/g/{}/X/ /d,lg/{}:{}" "/X/".format(ep, eo[0], eo[1][0])
                            for ep, eo in sorted(e_points.items())
                        )
                        machined_print("entrances", e_cls, value=o, indent=4, color="g")

            location = str(d.location)
            home_dir = str(d.location.home())
            if location.startswith(home_dir):
                location = "~" + location[len(home_dir) :]
            if d.is_dirty():
                location += " /r/*/X/"
            machined_print("installed", indent=2, color="d,b", value=location)

        if self.verbosity > 1:
            if details["url"]:
                machined_print(
                    "website", value=details["url"].rstrip("/"), color="b", indent=2
                )
            if details["download_url"]:
                machined_print(
                    "download",
                    color="b",
                    indent=2,
                    value=details["download_url"].rstrip("/"),
                )

            raw_license = details.pop("license")
            if raw_license != "UNKNOWN":
                try:
                    if " and " in raw_license:
                        license = "/".join(
                            pkg.licensing.get_license(l).abbr
                            for l in raw_license.split(" and ")
                        )
                    elif " or " in raw_license:
                        license = "/".join(
                            pkg.licensing.get_license(l).abbr
                            for l in raw_license.split(" or ")
                        )
                    else:
                        license = pkg.licensing.get_license(raw_license).abbr
                except KeyError:
                    license = raw_license
                machined_print("license", value=license, color="y", indent=2)

            for prs, prs_det in sorted(details["people"].items()):
                email = list(prs_det.items())[0][1]
                o = "/lr/{}/X/ /lg/</X//b/{}/X//lg/>/X/".format(prs, email)
                machined_print("authors", value=o, color="lg", indent=2)
        print()


@main.register()
class Add:

    """add distributions"""

    def setup(self, add_arg):
        add_arg("dist", nargs="+", help="name of distribution(s) to install")

    def run(self, stdin, log):
        for dist in self.dist:
            print("Adding:")
            pkg.add(dist)


@main.register()
class Remove:

    """remove distributions"""

    def setup(self, add_arg):
        add_arg(
            "dist",
            nargs="+",
            completer=complete_distname,
            help="name of distribution(s) to uninstall",
        )

    def run(self, stdin, log):
        for dist in self.dist:
            print("Removing:")
            d = pkg.install.pkg_resources.get_distribution(dist)
            self.print_tree(d, pkg.install.get_orphans(dist))
            pkg.remove(dist, clean_reqs=True)

    def print_tree(self, dist, orphans, indent=0):
        """"""
        print(
            " " * indent * 4,
            "{0.project_name} {0.version} ({0.location})".format(dist),
            sep="",
        )
        for req in pkg.listing._requires(dist):
            if req in orphans:
                self.print_tree(req, orphans, indent + 1)
