"""An opinionated Git interface."""

import collections
import difflib
from pathlib import Path
import re
import textwrap
from typing import List
import xml.sax.saxutils

import pendulum
import sh

__all__ = ["get_repo", "clone_repo", "colorize_diff", "Repository"]


class Repository:
    """A git repository."""

    def __init__(self, location: Path, gpghome: Path = None):
        """
        Return a Repository instance for git repository at given location.

        Use gpghome to provide an alternate GPG directory.

        """
        self.location = location
        if gpghome:
            self.git = sh.git.bake("-C", location, _env={"GNUPGHOME": gpghome})
        else:
            self.git = sh.git.bake("-C", location)

    def add(self, *files):
        """Add files to the index."""
        if not files:
            files = ["*"]
        return self.git("add", *files)

    def config(self, name, value):
        """Set repository options."""
        return self.git("config", name, value)

    def commit(self, message, author=None, key=None):
        """Record changes to the repository."""
        args = []
        if author:
            args.extend(["--author", author])
        if key:
            args.append(f"-S{key}")
        details = self._gitlines("commit", "-m", message, *args)
        short_hash = re.match(r".+ ([\w\d]{7})\]", details[0]).group(1)
        return self[short_hash]

    def fetch_into_bare(self, repository="origin", refspec="master:master"):
        """."""  # TODO
        self.git("fetch", repository, refspec)

    def push(self):
        """Update remote refs along with associated objects."""
        self.git("push")

    def pull(self):
        """Fetch from and integrate with another repository or branch."""
        self.git("pull")

    def show(self, gitobject):
        """Show various types of objects."""
        return str(self.git("--no-pager", "show", gitobject))

    def diff(self, start=None, end=None):
        """Show changes between commits, commit and working tree, etc."""
        args = []
        if start is None:
            start = "HEAD"
        if end is None:
            end = start
            start = end + "^"
        if start and end:
            args.extend((start, end))
        # if start is None and end is None:
        #     args = []
        # if start is not None and end is None:
        #     args = [start + "^", start]
        return self.git("--no-pager", "diff", "--no-color", *args)

    @property
    def files(self):
        """Show information about files in the index and the working tree."""
        return [Path(self.location) / path.strip() for path in self.git("ls-files")]

    @property
    def status(self):
        """Show the working tree status."""
        return self.git("status", "--porcelain")

    @property
    def changed_files(self):
        """Compare files in the working tree and the index."""
        return self.git("diff-files")

    @property
    def remotes(self):
        """Yield 3-tuples of a remote's `name`, `url` and `context`."""
        for remote in self._gitlines("--no-pager", "remote", "-v"):
            if not remote:
                continue
            name, url, context = remote.split()
            yield name, url, context.strip("()")

    def drift_from_push_remote(self):
        """
        Return 2-tuple containing (direction, distance) from push remote.

        Direction is `ahead` or `behind`. Distance is an integer of commits.

        """
        match = re.match(
            r"\[(ahead|behind) (\d+)\]",
            self.git("for-each-ref", "--format", "%(push:track)", "refs/heads").strip(),
        )
        if match:
            return match.groups()

    def create_branch(self, name):
        """Create a new branch."""
        return self.git("branch", name)

    @property
    def branches(self):
        """Return a list of branches."""
        branches = []
        for branch in self._gitlines("branch", "-a", "--no-color"):
            active, _, name = branch.partition(" ")
            branches.append((name, bool(active)))
        return branches

    @property
    def tags(self):
        """Return a list of tags."""
        tags = []
        for tag_id in reversed(self._gitlines("--no-pager", "tag")):
            if not tag_id:
                continue
            details = []
            signature = []

            def get_details(line):
                details.append(line.strip())

            def get_signature(line):
                signature.append(line.strip())

            self.git("tag", "-v", tag_id, _out=get_details, _err=get_signature)
            tag_object, tag_type, _, tag_tagger, _, tag_message = details
            timestamp = pendulum.from_timestamp(float(tag_tagger.split()[-2]))
            tags.append(
                (tag_id, tag_object.split()[1], timestamp, signature[1].split()[-1])
            )
        return tags

    def log(self, selector=None) -> list:
        """
        Return a list of commits.

        `selector` can be a number of recent commits (-1, -2, etc.) or the
        hash of a specific commit.

        """
        entries = collections.OrderedDict()
        current_hash = None

        def get_lines(line):
            nonlocal current_hash
            if line.startswith("commit "):
                current_hash = line.split()[1]
                entries[current_hash] = {"hash": current_hash, "message": ""}
            elif line.startswith("gpg:                using"):
                entries[current_hash]["pubkey"] = line.split()[-1]
            elif line.startswith("Author:"):
                (
                    entries[current_hash]["author_name"],
                    _,
                    entries[current_hash]["author_email"],
                ) = (
                    line.partition(": ")[2].strip(">\n").partition(" <")
                )
            elif line.startswith("Date:"):
                dt = pendulum.from_format(
                    line.partition(":   ")[2], "YYYY-MM-DD HH:mm:ss Z"
                )
                entries[current_hash]["timestamp"] = dt.in_timezone("UTC")
            elif not line.startswith("gpg: "):
                entries[current_hash]["message"] += line

        args = []
        if selector:
            args.append(selector)
        self.git(
            "--no-pager",
            "log",
            "--date=iso",
            "--no-color",
            "--show-signature",
            *args,
            _out=get_lines,
        )
        for commit in entries.keys():
            entries[commit]["message"] = textwrap.dedent(
                entries[commit]["message"]
            ).strip()
        return entries

    def __getitem__(self, hash):
        """Return the commit for given hash."""
        return list(self.log(hash).values())[0]

    def _gitlines(self, *args, **kwargs) -> list:
        """Return a list of the result of a git command split by lines."""
        return self.git(*args, **kwargs).rstrip().split("\n")


def get_repo(
    location: str = ".", init=False, bare=False, gpghome: str = None
) -> Repository:  # NoQA FIXME
    """Return a Repository for given location."""
    location = Path(location)
    if gpghome:
        gpghome = Path(gpghome)
    # if not Path(location).exists():
    if init:
        args = ["init", str(location)]
        if bare:
            args.append("--bare")
        sh.git(*args)
    # else:
    #     raise FileNotFoundError("repository does not exist "
    #                             "at {}".format(str(location)))
    return Repository(location, gpghome=gpghome)


def clone_repo(source, destination, bare=False) -> Repository:  # NoQA FIXME
    """Clone source repository and return a Repository of destination."""
    args = []
    if bare:
        args.append("--bare")
    sh.git("clone", str(source), str(destination), *args)
    return Repository(destination)


def colorize_diff(diff) -> List:
    """Return HTML for presenting given unified diff."""
    files = []
    for filediff in re.split(r"diff --git [\w/._]+ [\w/._]+\n", str(diff))[1:]:
        lines = filediff.split("\n")
        current = {"changes": []}
        current["index"] = lines[0]
        current["from"], current["to"] = lines[1], lines[2]
        changes = re.split(
            r"^@@ (-\d+,\d+ \+\d+,\d+) @@(.*)$",
            "\n".join(lines[3:]),
            flags=re.MULTILINE,
        )[1:]
        grouped_changes = zip(*(changes[i::3] for i in (0, 1, 2)))
        for changed_linespec, _, changed_lines in grouped_changes:
            changed_linenos = re.match(
                r"-(\d+),(\d+) \+(\d+),(\d+)", changed_linespec
            ).groups()
            current["changes"].append((changed_linenos, changed_lines))
        # diff_spec = re.match(r"@@ -(\d+),(\d+) +(\d+),(\d+) @@.+", lines[3])
        # fromstart, fromlength, tostart, tolength = diff_spec.groups()
        # current["from"].append()
        # current["lines"] = [first_line]
        # current["lines"].extend(lines[4:-1])
        files.append(current)
    return files

    # html = ["<div class=diff>"]
    # for line in diff.split("\n"):
    #     html.append("<div class=''>{}</div>".format(line))
    # html.append("</div>")
    # return "\n".join(html)


def _colorize_diff(diff):  # NoQA FIXME
    lines = diff.splitlines()
    lines.reverse()
    while lines and not lines[-1].startswith("@@"):
        lines.pop()
    yield "<div class=diff>"
    while lines:
        line = lines.pop()
        klass = ""
        if line.startswith("@@"):
            klass = "control"
        elif line.startswith("-"):
            klass = "delete"
            if lines:
                _next = []
                while lines and len(_next) < 2:
                    _next.append(lines.pop())
                if _next[0].startswith("+") and (
                    len(_next) == 1 or _next[1][0] not in ("+", "-")
                ):
                    aline, bline = _line_diff(line[1:], _next.pop(0)[1:])
                    yield "<div class=delete>-{}</div>".format(aline)
                    yield "<div class=insert>+{}</div>".format(bline)
                    if _next:
                        lines.append(_next.pop())
                    continue
                lines.extend(reversed(_next))
        elif line.startswith("+"):
            klass = "insert"
        yield "<div class={}>{}</div>".format(klass, _escape(line))
    yield "</div>"


def _line_diff(a, b):
    aline = []
    bline = []
    tpl = "<span class=highlight>{}</span>"
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b).get_opcodes():
        if tag == "equal":
            aline.append(_escape(a[i1:i2]))
            bline.append(_escape(b[j1:j2]))
            continue
        aline.append(tpl.format(_escape(a[i1:i2])))
        bline.append(tpl.format(_escape(b[j1:j2])))
    return "".join(aline), "".join(bline)


def _escape(text):
    return xml.sax.saxutils.escape(text, {" ": "&nbsp;"})
