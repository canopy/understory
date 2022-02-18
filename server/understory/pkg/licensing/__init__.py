"""
terms of use for software, content & data

"""

import collections
import distutils.version
import json
import pkg_resources
import re

__all__ = ["get_license"]


index = {}
uris = {}
features = collections.defaultdict(list)
pattern = re.compile(
    r"""(?xi)
                         ^
                         ([\s\w]+?)
                         (
                           \s?
                           (license|l)
                           \s?
                         )?
                         (
                           \s?
                           (version|v)
                           \s?
                           ([.\w]+)
                         )?
                         $"""
)


def get_license(identifier):
    """
    return best matching license for given `identifier` (name *or* URI)

    An identifier may contain version information.

        >>> long = get_license("Affero General Public License version 3")
        >>> short = get_license("Affero General Public")
        >>> abbreviated = get_license("AGPL")
        >>> long == short == abbreviated
        True
        >>> long
        <licensing.License: Affero General Public License v3>

    """
    _load()

    if "/" in identifier and " " not in identifier:
        if identifier.startswith(("http://", "https://", "//")):
            identifier = identifier.partition("//")[2]
        try:
            req_name, req_version = uris[identifier]
        except KeyError:
            raise KeyError("`{}` not found in index".format(identifier))
    else:
        identifier = identifier.replace("_", " ")
        try:
            req_name, req_version = pattern.match(identifier).groups()[::5]
        except AttributeError:
            raise KeyError("`{}` not found in index".format(identifier))

    def cmp(kv):
        return distutils.version.LooseVersion(str(kv[0]))

    for name, versions in index.items():
        abbreviation = "".join(w[0] for w in name.split() if w not in {"of"}).lower()
        if req_name.lower().strip() not in (name.lower(), abbreviation):
            continue
        for version, details in sorted(versions.items(), key=cmp):
            if version == req_version:
                break
        if req_version and version != req_version:
            err_msg = "unknown version `{}` for `{}`"
            raise KeyError(err_msg.format(req_version, name))
        return _License(
            name=name,
            version=version,
            abbr=details["abbr"],
            uri=details["uri"],
            features=details.get("features", []),
        )
    raise KeyError("`{}` not found in index".format(identifier))


class _License(collections.namedtuple("License", "name version abbr uri features")):

    """
    a `NamedTuple` for licenses

        >>> license = _License(name="Affero General Public", version="3",
        ...                    abbr="AGPLv3", uri="gnu.org/licenses/agpl.html",
        ...                    features=["dfsg","gpl","fsf","osi","copyleft"])
        >>> license.name
        'Affero General Public'
        >>> license.version
        '3'
        >>> license.uri
        'gnu.org/licenses/agpl.html'
        >>> license.features
        ['dfsg', 'gpl', 'fsf', 'osi', 'copyleft']

        >>> repr(license)  #doctest: +ELLIPSIS
        '<licensing.License: Affero General Public License v3>'
        >>> str(license)
        'Affero General Public License v3 (gnu.org/licenses/agpl.html)'
        >>> license.is_compatible("copyleft")
        True

    """

    @property
    def canonical(self):
        version = ""
        if self.version != "0":
            version = " v" + self.version
        return "".join((self.name, " License", version))

    def is_compatible(self, compatibility):
        return compatibility in self.features

    def __repr__(self):
        return "<licensing.License: {}>".format(self.canonical)

    def __str__(self):
        return "{} ({})".format(self.canonical, self.uri)


def _load():
    """
    populate license index

    """
    global index
    global uris
    global features
    if index:
        return
    licenses = json.loads(
        pkg_resources.resource_string(__name__, "licenses.json").decode("utf-8")
    )
    index.update(licenses.items())
    for name, versions in licenses.items():
        for version, details in versions.items():
            license = name, version
            uris[details["uri"]] = license
            for feature in details.get("features", []):
                features[feature].append(license)
