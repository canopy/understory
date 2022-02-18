"""
Tools for metamodern software development.

Includes support for testing, syntax checking and metrics measurement
using pytest, flake8, radon respectively.

Provides code analysis and package/interface introspection.

"""

# TODO issue tracking, code review
# TODO code analysis via pysonar2, psydiff
# TODO facilitate anonymous A/B testing in the canopy

import collections
import importlib
import inspect
import os
import pathlib
import pkgutil
import re
import subprocess  # TODO use `sh`
import textwrap
import xml.etree.ElementTree

import radon.complexity
from radon.complexity import cc_rank as rank_cc
import radon.metrics
from radon.metrics import mi_rank as rank_mi
import radon.raw
from understory import pkg

from . import git

__all__ = ["git", "get_api", "get_metrics", "rank_cc", "rank_mi"]


languages = {"py": "Python", "c": "C", "html": "HTML", "css": "CSS", "js": "Javascript"}


def get_metrics(code):
    """
    Return metrics for given code.

    Uses radon to analyze line counts, complexity and maintainability.

    """
    return {
        "lines": radon.raw.analyze(code),
        "complexity": radon.complexity.cc_visit(code),
        "maintainability": radon.metrics.mi_visit(code, True),
    }


def test(pkgdir="."):
    """Test pkgdir with pytest and return test results."""
    packages = pkg.discover(pkgdir).pop("packages", [])
    cmd = [
        "pytest",
        "--doctest-modules",
        "--ignore",
        "setup.py",
        "--pep8",
        "--cov",
        ",".join(packages),
        "--cov-report",
        "xml:coverage.xml",
        "--junit-xml",
        "test_results.xml",
    ]
    proc = subprocess.Popen(
        cmd, env=os.environ, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _, err = [x.decode("utf-8") for x in proc.communicate()]
    return _parse_junit(), _parse_coverage(), err


def _parse_junit(path="test_results.xml"):
    suite_tag = xml.etree.ElementTree.parse(str(path)).getroot()
    _suite = dict(suite_tag.attrib)
    suite = {
        "tests": _suite["tests"],
        "errors": _suite["errors"],
        "failures": _suite["failures"],
        "skips": _suite["skips"],
        "cases": collections.defaultdict(collections.OrderedDict),
    }
    for case_tag in suite_tag:
        case = dict(case_tag.attrib)
        outcome = {"type": "success"}
        try:
            child = case_tag.getchildren()[0]
        except IndexError:
            pass
        else:
            if child.tag == "failure":
                outcome["type"] = "failure"
                outcome["message"] = child.attrib["message"]
                outcome["code"] = child.text
            elif child.tag == "system-out":
                outcome["output"] = child.text
        test_identifier = ":".join((case["classname"], case["name"]))
        details = {"line": case["line"], "time": case["time"], "outcome": outcome}
        suite["cases"][case["file"]][test_identifier] = details
    return suite


def _parse_coverage(path="test_coverage.xml"):
    coverage_tag = xml.etree.ElementTree.parse(str(path)).getroot()
    root = pathlib.Path(coverage_tag.getchildren()[1].getchildren()[0].text)
    coverage = {}
    for _package in coverage_tag.getchildren()[1].getchildren():
        for case in _package.getchildren()[0].getchildren():
            lines = []
            for line in case.getchildren()[1].getchildren():
                lines.append((line.attrib["number"], line.attrib["hits"]))
            coverage[root / case.attrib["filename"]] = (
                float(case.attrib["line-rate"]) * 100,
                lines,
            )
    return coverage


# def count_sloc(self):
#     """
#     count Source Lines Of Code
#
#     """
#     # TODO accrue statistics
#     line_counts = collections.defaultdict(int)
#
#     def handle(file):
#         line_count = 0
#         suffix = file.suffix.lstrip(".")
#         if suffix in languages:
#             with file.open() as fp:
#                 lines = fp.readlines()
#                 for line in lines[:10]:
#                     if line.rstrip() == "# noqa":
#                         break
#                 else:
#                     line_count = len(lines)
#                     line_counts[suffix] += line_count
#         yield
#         if line_count:
#             print(" /d,lg/{}/X/".format(line_count), end="")
#             self.position += 3 + len(str(line_count))
#         yield
#
#     def summarize():
#         # TODO commify
#         print("Source Lines of Code:")
#         # print("--------------------", end="\n\n")  TODO markdown output
#         # (`cli` feature to uniform output to HTML for pipe to web agent)
#         total = 0
#         for suffix, line_count in line_counts.items():
#             print("  {:15}{:>10}".format(languages[suffix], line_count))
#             total += line_count
#         print("  {:>25}".format(total))
#
#     return handle, summarize


def get_api(mod, pkg=None) -> dict:
    """Return a dictionary containing contents of given module."""
    if pkg:
        mod = ".".join((pkg, mod))
    try:
        module = importlib.import_module(mod)
    except Exception as err:
        print(err)
        module = None
    members = []
    if module:
        members = _get_namespace_members(module)
    details = {"name": mod, "mod": module, "members": members, "descendants": {}}
    try:
        mod_location = module.__path__
        for _, _mod, __ in pkgutil.iter_modules(mod_location):
            details["descendants"][_mod] = get_api(_mod, pkg=mod)
    except AttributeError:
        pass
    return details


def get_doc(obj):
    """Return a two-tuple of object's first line and rest of docstring."""
    docstring = obj.__doc__
    if not docstring:
        return "", ""
    return inspect.cleandoc(docstring).partition("\n\n")[::2]


def _get_namespace_members(mod):  # NOQA FIXME
    modules = inspect.getmembers(mod, inspect.ismodule)
    # for name, m in inspect.getmembers(m, inspect.ismodule):
    #     if inspect.getmodule(mod) != m:
    #         continue
    #     modules.append((name, m))
    exceptions = []
    for name, exc in inspect.getmembers(mod, _isexception):
        if inspect.getmodule(exc) != mod:
            continue
        exceptions.append((name, exc))
    functions = []
    for name, func in get_members(mod, "function"):
        if inspect.getmodule(func) != mod:
            continue
        functions.append((name, func))
    classes = []
    for name, cls in get_members(mod, "class"):
        # if inspect.getmodule(cls) != mod:
        #     continue
        if (name, cls) in exceptions:
            continue
        classes.append((name, cls))
    global_mems = []
    defaults = (
        "__all__",
        "__builtins__",
        "__cached__",
        "__doc__",
        "__file__",
        "__loader__",
        "__name__",
        "__package__",
        "__spec__",
    )
    for global_mem in inspect.getmembers(mod):
        if (
            global_mem in modules
            or global_mem in exceptions
            or global_mem in functions
            or global_mem in classes
            or global_mem[0] in defaults
        ):
            continue
        global_mems.append(global_mem)
    return modules, global_mems, exceptions, functions, classes


def _isexception(obj):
    return inspect.isclass(obj) and issubclass(obj, Exception)


# XXX def _isfunction_or_datadescriptor(obj):
# XXX     return inspect.isfunction(obj) or inspect.isdatadescriptor(obj)


def get_members(obj, pred, hidden=True):
    """Return a list of object's members."""
    pub = []
    hid = []
    keywords = {
        "function": ("def ", "("),
        "class": ("class ", ":("),
        "datadescriptor": ("def ", "("),
        "function_or_datadescriptor": ("def ", "("),
    }
    document_order = []
    for line in get_code(obj).splitlines():
        keyword, delimiter = keywords[pred]
        if line.lstrip().startswith(keyword):
            match = re.search(r" ([A-Za-z0-9_]+)[{}]".format(delimiter), line)
            document_order.append(match.groups()[0])
    try:
        pred_handler = getattr(inspect, "is" + pred)
    except AttributeError:
        pred_handler = globals().get("is" + pred)
    members = dict(inspect.getmembers(obj, pred_handler))
    for name in document_order:
        try:
            _obj = members[name]
        except KeyError:
            continue
        (hid if name.startswith("_") else pub).append((name, _obj))
    return (pub + hid) if hidden else pub


def get_source(obj):
    """
    Return the string representation of given object's code.

    Comments are stripped and code is dedented for easy parsing.

    """
    lines, lineno = inspect.getsourcelines(obj)
    code = "".join(line for line in lines if not line.lstrip().startswith("#"))
    docstring = getattr(obj, "__doc__", None)
    if docstring is not None:
        code = code.replace('"""{}"""'.format(docstring), "", 1)
    return textwrap.dedent(code), lineno


def get_code(obj):
    """
    Return a string containing the source code of given object.

    The declaration statement and any associated docstring will be removed.

    """
    # TODO use sourcelines to return line start no
    try:
        source = inspect.getsource(obj)
    except (OSError, TypeError):
        source = ""
    if obj.__doc__:
        source = source.partition('"""')[2].partition('"""')[2]
    if not source.strip():
        source = source.partition("\n")[2]
    return textwrap.dedent(source)
