"""
[Public Suffix List][1] support

    >>> split("www.example.org")
    Domain(subdomain='www', domain='example', suffix='org')

Based upon the original implementation [`publicsuffix`][2] copyright
@[Tomaž Solc][3] and released under an MIT license.

[1]: //publicsuffix.org/list/
[2]: //pypi.python.org/pypi/publicsuffix
[3]: //tablix.org

"""

import codecs
import collections

import pkg_resources
import requests

_suffixes = None
Domain = collections.namedtuple("Domain", "subdomain domain suffix")


def split(hostname):
    """
    return the subdomain and domain of given `hostname`

        >>> split("www.example.org")
        Domain(subdomain='www', domain='example', suffix='org')
        >>> split("www.example.org.uk")
        Domain(subdomain='www', domain='example', suffix='org.uk')

    """
    # TODO handle Punycode decoding
    if _suffixes is None:
        _initialize()
    parts = hostname.lower().lstrip(".").split(".")
    hits = [None] * len(parts)
    _suffixes.lookup(hits, 1, parts)
    for i, what in enumerate(hits):
        if what is not None and what == 0:
            return Domain(".".join(parts[:i]), parts[i], ".".join(parts[i + 1 :]))


def _initialize():
    global _suffixes
    _suffixes = _PublicSuffixList()


class _PublicSuffixList:

    """
    reads and parses the public suffix list

    """

    def __init__(self):
        input_path = pkg_resources.resource_filename(
            "understory.uri", "public_suffix_list.dat"
        )
        try:
            with codecs.open(input_path, "r", "utf8") as fp:
                self._build_structure(fp)
        except FileNotFoundError:
            res = requests.get(
                "https://publicsuffix.org/list/" "public_suffix_list.dat"
            )
            with codecs.open(input_path, "w", "utf8") as fp:
                fp.write(res.text)
            with codecs.open(input_path, "r", "utf8") as fp:
                self._build_structure(fp)

    def lookup(self, matches, depth, parts, parent=None):
        if parent is None:
            parent = self.root
        if parent in (0, 1):
            negate = parent
            children = None
        else:
            negate, children = parent
        matches[-depth] = negate
        if depth < len(parts) and children:
            for name in ("*", parts[-depth]):
                child = children.get(name, None)
                if child is not None:
                    self.lookup(matches, depth + 1, parts, child)

    def _build_structure(self, fp):
        root = [0]
        for line in fp:
            line = line.strip()
            if line.startswith("//") or not line:
                continue
            self._add_rule(root, line.split()[0].lstrip("."))
        self.root = self._simplify(root)

    def _add_rule(self, root, rule):
        if rule.startswith("!"):
            negate = 1
            rule = rule[1:]
        else:
            negate = 0
        parts = rule.split(".")
        self._find_node(root, parts)[0] = negate

    def _find_node(self, parent, parts):
        if not parts:
            return parent
        if len(parent) == 1:
            parent.append({})
        assert len(parent) == 2
        negate, children = parent
        child = parts.pop()
        child_node = children.get(child, None)
        if not child_node:
            children[child] = child_node = [0]
        return self._find_node(child_node, parts)

    def _simplify(self, node):
        if len(node) == 1:
            return node[0]
        return (node[0], dict((k, self._simplify(v)) for (k, v) in node[1].items()))
