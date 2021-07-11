"""

"""

from __future__ import annotations

import builtins
import glob
import importlib
import inspect
import os
import pathlib
import sys

import pkg_resources

from understory import mkdn, solarized

from . import parse

__all__ = [
    "templates",
    "build",
    "TemplatePackage",
    "Template",
    "CompiledTemplate",
    "TemplateResult",
]


_builtin_names = (
    "dict",
    "enumerate",
    "float",
    "int",
    "bool",
    "list",
    "long",
    "reversed",
    "set",
    "slice",
    "tuple",
    "xrange",
    "abs",
    "all",
    "any",
    "callable",
    "chr",
    "cmp",
    "divmod",
    "filter",
    "hex",
    "id",
    "isinstance",
    "iter",
    "len",
    "sum",
    "max",
    "min",
    "oct",
    "ord",
    "pow",
    "range",
    "True",
    "False",
    "None",
    "__import__",
    "getattr",
    "object",
    "repr",
    "sorted",
    "basestring",
    "str",
    "bytes",
    "type",
    "zip",
    "round",
    "dir",
    "next",
)


def templates(package, *template_paths, base_dir=None, **_globals) -> TemplatePackage:
    """ """
    # XXX if not template_paths:
    path = pkg_resources.resource_filename(package, "templates")
    ns = importlib.import_module(package + ".templates")
    if base_dir:
        path = str(base_dir / path)
    return TemplatePackage(path, ns, **_globals)
    # XXX templates = []
    # XXX for template_path in template_paths:
    # XXX     template_path = str(template_path)
    # XXX     path = pkg_resources.resource_filename(package, template_path)
    # XXX     if os.path.isdir(path):
    # XXX         obj = templates(package, template_path)
    # XXX     else:
    # XXX         with open(path) as fp:
    # XXX             template = fp.read()
    # XXX         obj = Template(template, filename=template_path, globals=_globals)
    # XXX     templates.append(obj)
    # XXX return templates


def build(directory):
    """
    compiles directory of templates to python code

    """
    for dirpath, dirnames, filenames in os.walk(directory):
        with open(os.path.join(dirpath, "__init__.py"), "w") as template:
            print("from mm.parse import *", file=template)
            print("from mm.templating import *", file=template)
            for dirname in dirnames[:]:
                if dirname.startswith("."):
                    dirnames.remove(dirname)
            if dirnames:
                print(file=template)
                for dirname in sorted(dirnames):
                    print("import {}".format(dirname), file=template)
            print(file=template)
            for fn in filenames:
                if fn.startswith((".", "__init__.py")) or fn.endswith("~"):
                    continue
                path = os.path.join(dirpath, fn)
                if "." in fn:
                    name = fn.split(".", 1)[0]
                else:
                    name = fn
                text = open(path).read()
                text = Template.normalize_text(text)
                code = Template.generate_code(text, path)
                code = code.replace("__template__", name, 1)
                print(file=template)
                print(code, end="\n\n", file=template)
                print(
                    '{0} = CompiledTemplate({0}, "{1}")'.format(name, path),
                    file=template,
                )
                print("join_ = {}._join".format(name), file=template)
                print("escape_ = {}._escape".format(name), file=template)


def safestr(obj, encoding="utf-8"):
    r"""
    converts any given object to utf-8 encoded string

        >>> safestr("hello")
        'hello'
        >>> safestr(2)
        '2'

    # TODO >>> safestr("\u1234")
    # TODO '\xe1\x88\xb4'

    """
    if isinstance(obj, str):
        return obj
    # TODO elif isinstance(obj, unicode):
    # TODO     return obj.encode(encoding)
    # XXX elif hasattr(obj, "next") and hasattr(obj, "__iter__"):
    # XXX    return itertools.imap(safestr, obj)
    return str(obj)


html_entities = [
    ("&", "amp"),  # must come first/last during quote/unquote
    ("<", "lt"),
    (">", "gt"),
    ("'", "#39"),
    ('"', "quot"),
]


def htmlquote(text):
    r"""
    encode `text` for raw use in HTML

        >>> htmlquote("<'&\">")
        '&lt;&#39;&amp;&quot;&gt;'

    """
    text = str(text)
    for entity, code in html_entities:
        text = text.replace(entity, "&{};".format(code))
    return text


def websafe(val):
    r"""
    return a safe version of text for use in utf-8 encoded HTML, XHTML or XML

        >>> websafe("<'&\">")
        '&lt;&#39;&amp;&quot;&gt;'
        >>> websafe(None)
        ''
        >>> websafe("\u203d")
        '\u203d'

    # TODO >>> websafe("\xe2\x80\xbd")
    # TODO '\u203d'

    """
    if val is None:
        return ""
    # elif isinstance(val, str):
    #     val = val.decode("utf-8")
    # elif not isinstance(val, unicode):
    #     val = unicode(val)
    return htmlquote(val)
    # return htmlquote(str(val))
    # return htmlquote(bytes(val, "utf-8"))


class TemplatePackage:

    """
    a template renderer

        >>> templates = TemplatePackage()  # doctest: +SKIP
        >>> templates.foo()  # doctest: +SKIP
        '<p>bar</p>'

    TemplatePackage are rendered recursively based upon directory layout.

    """

    def __init__(self, directory, ns=None, **kwglobals):
        """
        use the HTML found in in or around given `module`

        """
        self._directory = str(directory)
        if ns:
            self._ns = ns
        else:
            dir_path = pathlib.Path(directory)
            sys.path.insert(0, str(dir_path.parent))
            self._ns = importlib.import_module(dir_path.stem)
        self._globals = {
            k: v
            for k, v in self._ns.__dict__.items()
            if k in getattr(self._ns, "__all__", [])
        }
        self._globals["mkdn"] = mkdn.render
        self._globals.update(kwglobals)
        self._cache = {}

    def __getattr__(self, name) -> Template | TemplatePackage:
        """
        load a template from root module directory

        An `html` subdirectory will be attempted if no template is found.

        """
        try:
            return self._cache[name]
        except KeyError:
            pass
        path = os.path.join(self._directory, name)
        if os.path.isdir(path):
            return TemplatePackage(path, self._ns, **self._globals)
        try:
            path = self._get_filename(path)
        except IndexError:
            raise AttributeError("No template named `{}`".format(name))
        with open(path) as f:
            template = f.read()
        compiled = Template(template, filename=path, globals=self._globals)
        if os.getenv("WEBCTX") != "dev":
            self._cache[name] = compiled
        return compiled

    def _get_filenames(self, path):
        """"""
        return list(sorted(f for f in os.listdir(path) if not f.endswith("~")))

    def _get_filename(self, path):
        """"""
        return list(
            sorted(
                f
                for f in glob.glob(path + ".*")
                if not (f == "__init__.py" or f.endswith("~"))
            )
        )[0]

    def __dir__(self):
        return [
            os.path.split(p)[-1].split(".")[0]
            for p in self._get_filenames(os.path.join(self._directory))
        ]


class Template:

    """ """

    globals = {}
    builtins = dict(
        (name, getattr(builtins, name))
        for name in _builtin_names
        if name in builtins.__dict__
    )

    def __init__(
        self,
        template,
        filename="<template>",
        globals=None,
        builtins=None,
        extensions=None,
    ):
        self.extensions = extensions or []
        try:
            with template as fp:
                template = fp.read()
        except AttributeError:
            pass
        self._template = template
        text = Template.normalize_text(str(template))
        code = self.compile_template(text, filename)

        if globals is None:
            globals = self.globals
        if builtins is None:
            builtins = self.builtins

        self.filename = filename
        _globals = {
            "get_obj_name": lambda o: o.__name__,
            "get_obj_docstring": inspect.getdoc,
            "mkdn": mkdn.render,
        }

        _globals.update(**globals)
        self._globals = _globals
        self._builtins = builtins
        if code:
            self.template = self._compile(code)  # XXX
        else:
            self.template = lambda: ""

    @staticmethod
    def normalize_text(text):
        """
        normalizes template text by correcting `\r\n`, tabs and BOM chars

        """
        text = text.replace("\r\n", "\n").replace("\r", "\n").expandtabs()
        if not text.endswith("\n"):
            text += "\n"
        BOM = "\xef\xbb\xbf"  # XXX support unicode? u"\ufeff"
        if isinstance(text, str) and text.startswith(BOM):
            text = text[len(BOM) :]
        return text

    def __add__(self, other):
        try:
            new_text = other._template
        except AttributeError:
            new_text = other
        return Template(self._template + new_text)

    def _repr_html_(self):
        return solarized.highlight(self._template, ".html")

    def __call__(self, *args, **kwargs):
        """
        return rendered template

        As a side effect the current transaction's headers are updated
        according to content type of template.

        """
        types = {
            "txt": "text/plain",
            "xml": "text/xml",
            "html": "text/html",
            "md": "text/x-markdown",
            "css": "text/css",
            "js": "text/javascript",
            "json": "application/json",
            "py": "text/x-python",
            "svg": "image/svg+xml",
        }
        output = self.template(*args, **kwargs)
        ext = os.path.splitext(self.filename)[1][1:]
        output.content_type = types.get(ext, "text/html")
        # output.content_type = "text/html"
        return output

    @staticmethod
    def generate_code(text, filename, parser=None):
        parser = parser or parse.Parser()
        rootnode = parser.parse(text, filename)
        code = rootnode.emit(indent="").strip()
        return safestr(code)

    def create_parser(self):
        p = parse.Parser()
        for ext in self.extensions:
            p = ext(p)
        return p

    def compile_template(self, template_string, filename):
        code = Template.generate_code(
            template_string, filename, parser=self.create_parser()
        )

        def get_source_line(filename, lineno):
            try:
                lines = open(filename).read().splitlines()
                return lines[lineno]
            except Exception:
                return None

        try:
            compiled_code = compile(code, filename, "exec")
        except SyntaxError as err:
            # display template line that caused the error along with traceback
            lineno = get_source_line(err.filename, err.lineno - 1)
            try:
                msg = "\n\nTemplate traceback:\n    File {}, line {}\n    {}"
                err.msg += msg.format(repr(err.filename), err.lineno - 5, lineno)
            except Exception:
                pass
            raise
        return compiled_code

    def _compile(self, code):
        env = self.make_env(self._globals or {}, self._builtins)
        exec(code, env)
        return env["__template__"]

    def make_env(self, globals, builtins):
        return dict(
            globals,
            __builtins__=builtins,
            ForLoop=parse.ForLoop,
            TemplateResult=TemplateResult,
            escape_=self._escape,
            join_=self._join,
        )

    def _join(self, *items):
        return u"".join(items)

    def _escape(self, value, escape=False):
        if value is None:
            value = ""
        value = str(value)
        if escape:
            value = websafe(value)
        return value


class CompiledTemplate(Template):

    """ """

    def __init__(self, f, filename):
        super(CompiledTemplate, self).__init__("", filename)
        self.template = f

    def compile_template(self, *a):
        return None

    def _compile(self, *a):
        return None


class TemplateResult(dict):

    """
    a dictionary like object for storing template output

    The result of a template execution is a `body` string and often a col-
    lection of attributes set using `$var: ...`. This class provides both a
    simple dictionary like interface for accessing these attributes as well
    as a string like interface for accessing the text output of the tem-
    plate.

    When the template is in execution, the output is generated part by part
    and those parts are combined at the end. Parts are added to the
    TemplateResult by calling the `extend` method and the parts are combined
    seemlessly when __body__ is accessed.

        >>> template = TemplateResult("hello, world", x="foo")
        >>> template
        <TemplateResult: 'hello, world' {'x': 'foo'}>
        >>> str(template)
        'hello, world'
        >>> template["x"]
        'foo'

        >>> template = TemplateResult()
        >>> template.extend([u"hello", u"world"])
        >>> template
        <TemplateResult: 'helloworld' {}>

    """

    __all__ = ["body"]

    def __init__(self, *a, **kw):
        self._body = None
        super().__init__(**kw)
        self._parts = []
        self.extend = self._parts.extend
        self.extend(a)

    @property
    def body(self):
        if self._body is None:
            self._body = "".join(str(p) if p else "" for p in self._parts)
        return self._body

    def __str__(self):
        return str(self.body).strip()

    # def __bytes__(self):
    #     return bytes(self.body, "utf-8")

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError("attr `{}` not found".format(name))

    def __add__(self, other):
        self._body = self.body + other.body
        return self

    def __bool__(self):
        return bool(self.body)

    def __repr__(self):
        return "<TemplateResult: '{}' {}>".format(self, super().__repr__())
