"""
package detail discovery and automated setup

"""

from importlib.machinery import SourceFileLoader
import inspect
import pathlib
import re
import subprocess

__all__ = ["discover", "auto_discover", "get_repo_files"]


currently_discovering = False


class PackageRepoError(Exception):

    """
    raised when there exists a halting flaw in the package design

    """


def discover(pkgdir: str) -> dict:
    """
    return a dictionary containing package details discovered at `pkgdir`

    """
    # TODO gpg verify
    # TODO author from first commit and maintainer from last tag's commit
    # TODO url=`hg paths default`; verify against ^https://{gpg.comment}/
    # TODO dirty versions
    # TODO long_description = inspect.getdoc(setup_mod)
    # TODO kwargs["package_data"] = {"": ["*.dat", "*.json", "*.yaml"]}
    pkgdir = pathlib.Path(pkgdir)
    if pkgdir.name == "setup.py":
        pkgdir = pkgdir.parent

    import setuptools

    global discover
    currently_supplied_args = None

    def get_supplied(**args):
        nonlocal currently_supplied_args
        currently_supplied_args = args

    _setup, setuptools.setup = setuptools.setup, get_supplied
    _discover, discover = discover, lambda x, **y: {}
    _setup_loader = SourceFileLoader("setup", str(pkgdir / "setup.py"))
    setup_mod = _setup_loader.load_module()
    setuptools.setup, discover = _setup, _discover

    comments = inspect.getcomments(setup_mod)
    name = re.match(r"^# \[`(.*?)`\]\[1\]", comments).groups()[0]
    description = "TODO use setup.py docstring"
    # XXX re.match(r"^# \[`.*`\]\[1\]: (.*)", comments).groups()[0]
    license_match = re.search(r"%\[([A-Za-z ]+)\]", comments)
    try:
        license = license_match.groups()[0]
    except AttributeError:
        license = "Unknown"
    url = re.search(r"^# \[1\]: (.*)$", comments, re.M).groups()[0]
    if url.startswith("//"):
        url = "https:" + url
    download_url = "{}.git".format(url)

    install_requires = currently_supplied_args.get("requires", [])
    entry_points = currently_supplied_args.get("provides", {})
    try:
        entry_points["console_scripts"] = entry_points["term.apps"]
    except KeyError:
        pass

    versions = gitsh("tag -l --sort -version:refname", pkgdir)
    version = versions.splitlines()[0].lstrip("v") if versions else "0.0"

    committers = gitsh(
        "--no-pager log --no-color | grep " '"^Author: " --color=never', pkgdir
    ).splitlines()

    def get_committer(index):
        return re.match(r"Author: (.*) <(.*)>", committers[index]).groups()

    author, author_email = get_committer(-1)
    maintainer, maintainer_email = get_committer(0)

    packages = setuptools.find_packages(str(pkgdir))
    py_modules = [
        p.stem for p in pkgdir.iterdir() if p.suffix == ".py" and p.stem != "setup"
    ]

    kwargs = {}
    if packages:
        kwargs["packages"] = packages
    if py_modules:
        kwargs["py_modules"] = py_modules

    return dict(
        name=name,
        version=version,
        description=description,
        url=url,
        download_url=download_url,
        install_requires=install_requires,
        entry_points=entry_points,
        license=license,
        author=author,
        author_email=author_email,
        maintainer=maintainer,
        maintainer_email=maintainer_email,
        **kwargs
    )


def auto_discover(dist, _, setup_file):
    """
    a `distutils` setup keyword for automatic discovery using `discover`

        >>> import setuptools  # doctest: +SKIP
        >>> setuptools.setup(discover=__file__)  # doctest: +SKIP

    """
    global currently_discovering
    currently_discovering = True
    details = discover(setup_file)
    dist.packages = details.pop("packages", [])
    dist.py_modules = details.pop("py_modules", [])
    # dist.install_requires = details.pop("requires", [])
    # dist.entry_points = details.pop("provides")
    dist.metadata.author = details.get("author", "")
    dist.metadata.author_email = details.get("author_email", "")
    dist.__dict__.update(details)
    dist.metadata.__dict__.update(details)


def get_repo_files(setup_dir):
    """
    a `setuptools` file finder for finding installable files from a Git repo

    """
    if not currently_discovering:
        return []
    if not setup_dir:
        setup_dir = "."
    return gitsh("ls-files", setup_dir)


def gitsh(command, working_dir):
    """
    return the output of running Git `command` in `working_dir`

    """
    raw_cmd = "git -C {} {}".format(working_dir, command)
    try:
        return subprocess.check_output(
            raw_cmd, stderr=subprocess.STDOUT, shell=True
        ).decode("utf-8")
    except subprocess.CalledProcessError:
        raise PackageRepoError("no Git repo at `{}`".format(working_dir))
