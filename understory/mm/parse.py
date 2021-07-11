"""
parser and parsing-related tools

Design
------

Template string is split into tokens and the tokens are combined into
nodes. Parse tree is a nodelist. TextNode and ExpressionNode are simple
nodes and for-loop, if-loop, etc. are block nodes, which contain multi-
ple child nodes.

Each node can emit some python string. python string emitted by the root
node is validated for safeeval and executed using python in the given
environment.

Enough care is taken to make sure the generated code and the template
has line to line match, so that the error messages can point to exact
line number in template. (It still doesn't work in some cases.)

Grammar
-------

    template -> defwith sections
    defwith -> "$def with (" arguments ")" | ""
    sections -> section*
    section -> block | assignment | line

    assignment -> "$ " <assignment expression>
    line -> (text|expr)*
    text -> <any characters other than $>
    expr -> "$" pyexpr | "$(" pyexpr ")" | "${" pyexpr "}"
    pyexpr -> <python expression>

"""

import collections
import re
import token
import tokenize

__all__ = ["ParseError", "SecurityError", "ForLoop"]


class Error(Exception):

    """"""


class ParseError(Error):

    """"""


class SecurityError(Error):

    """the template seems to be trying to do something naughty"""


_indent = " " * 4


def splitline(text):
    r"""
    splits `text` at first newline (modified string `partition`)

        >>> splitline("foo\nbar")
        ('foo\n', 'bar')
        >>> splitline('foo')
        ('foo', '')
        >>> splitline("")
        ('', '')

    """
    before, partition, after = text.partition("\n")
    return before + partition, after


class Node:

    """ """


class DefWith(Node):

    """ """

    def __init__(self, defwith, suite):
        if defwith:
            self.defwith = defwith.replace("with", "__template__") + ":"
            offset = 4  # encoding, __lineoffset__, loop & self
        else:
            self.defwith = "def __template__():"
            offset = 5  # encoding, __template__, __lineoffset__, loop & self
        self.defwith += "\n    __lineoffset__ = -{0}".format(offset)
        self.defwith += "\n    loop = ForLoop()"
        self.defwith += "\n    self = TemplateResult()"
        self.defwith += "\n    e_ = self.extend"
        self.suite = suite

    def emit(self, indent):
        return "\n".join(
            (self.defwith, self.suite.emit(indent + _indent), "    return self")
        )

    def __repr__(self):
        return "<defwith: {0}, {1}>".format(self.defwith, self.suite)


class Var(Node):

    """ """

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def emit(self, indent, text_indent):
        return indent + "self[{0}] = {1}\n".format(repr(self.name), self.value)

    def __repr__(self):
        return "<var: {0} = {1}>".format(self.name, self.value)


class Text(Node):

    """ """

    def __init__(self, value):
        self.value = value

    def emit(self, indent, begin_indent=""):
        return repr(self.value)

    def __repr__(self):
        return "t" + repr(self.value)


class Expression:

    """ """

    def __init__(self, value, escape=True):
        self.value = value.strip()
        if value.startswith("{") and value.endswith("}"):  # ${...} to $(...)
            self.value = "(" + self.value[1:-1] + ")"
        self.escape = escape

    def emit(self, indent, begin_indent=""):
        return "escape_({0}, {1})".format(self.value, bool(self.escape))

    def __repr__(self):
        if self.escape:
            escape = ""
        else:
            escape = ":"
        return "${0}{1}".format(escape, self.value)


class Assignment:

    """ """

    def __init__(self, code):
        self.code = code

    def emit(self, indent, begin_indent=""):
        return indent + self.code + "\n"

    def __repr__(self):
        return "<assignment: {0}>".format(repr(self.code))


class Line:

    """ """

    def __init__(self, nodes):
        self.nodes = nodes

    def emit(self, indent, text_indent="", name=""):
        text = [node.emit("") for node in self.nodes]
        if text_indent:
            text = [repr(text_indent)] + text
        return indent + "e_([{0}])\n".format(", ".join(text))

    def __repr__(self):
        return "<line: {0}>".format(repr(self.nodes))


class Code:

    """ """

    def __init__(self, stmt, block, begin_indent=""):
        # compensate one line for $code:
        self.code = "\n" + block

    def emit(self, indent, text_indent=""):
        rx = re.compile("^", re.M)
        return rx.sub(indent, self.code).rstrip(" ")

    def __repr__(self):
        return "<code: {0}>".format(repr(self.code))


class Statement:

    """ """

    def __init__(self, stmt):
        self.stmt = stmt

    def emit(self, indent, begin_indent=""):
        return indent + self.stmt

    def __repr__(self):
        return "<stmt: {0}>".format(repr(self.stmt))


class Suite:

    """
    suite is a list of sections

    """

    def __init__(self, sections):
        self.sections = sections

    def emit(self, indent, text_indent=""):
        content = []
        for section in self.sections:
            content.append(section.emit(indent, text_indent))
        return "\n" + "".join(content)

    def __repr__(self):
        return repr(self.sections)


class Block:

    """ """

    def __init__(self, stmt, block, begin_indent=""):
        self.stmt = stmt
        self.suite = Parser().read_suite(block)
        self.begin_indent = begin_indent

    def emit(self, indent, text_indent=""):
        text_indent = self.begin_indent + text_indent
        out = self.suite.emit(indent + _indent, text_indent)
        return indent + self.stmt + out

    def __repr__(self):
        return "<block: {0}, {1}>".format(repr(self.stmt), repr(self.suite))


class Def(Block):

    """ """

    def __init__(self, *a, **kw):
        Block.__init__(self, *a, **kw)
        code = Code("", "")
        code.code = "self = TemplateResult(); e_ = self.extend\n"
        self.suite.sections.insert(0, code)
        code = Code("", "")
        code.code = "return self\n"
        self.suite.sections.append(code)

    def emit(self, indent, text_indent=""):
        text_indent = self.begin_indent + text_indent
        out = self.suite.emit(indent + _indent, text_indent)
        return indent + "__lineoffset__ -= 3\n" + indent + self.stmt + out


class If(Block):

    pass


class Else(Block):

    pass


class Elif(Block):

    pass


class For(Block):

    """ """

    def __init__(self, stmt, block, begin_indent=""):
        self.original_stmt = stmt
        tok = Tokenizer(stmt)
        tok.consume_till("in")
        a = stmt[: tok.index]  # for i in
        b = stmt[tok.index : -1]  # rest of for stmt excluding :
        stmt = a + " loop.setup(" + b.strip() + "):"
        Block.__init__(self, stmt, block, begin_indent)

    def __repr__(self):
        return "<block: {0}, {1}>".format(repr(self.original_stmt), repr(self.suite))


class ForLoop:

    """
    wrapper for expression in for stament to support loop.xxx helpers

            >>> loop = ForLoop()
            >>> for x in loop.setup(["a", "b", "c"]):
            ...     loop.index, loop.revindex, loop.parity, x
            ...
            (1, 3, 'odd', 'a')
            (2, 2, 'even', 'b')
            (3, 1, 'odd', 'c')
            >>> loop.index
            Traceback (most recent call last):
                    ...
            AttributeError: index

    """

    def __init__(self):
        self._ctx = None

    def __getattr__(self, name):
        if self._ctx is None:
            raise AttributeError(name)
        else:
            return getattr(self._ctx, name)

    def setup(self, seq):
        self._push()
        return self._ctx.setup(seq)

    def _push(self):
        self._ctx = ForLoopContext(self, self._ctx)

    def _pop(self):
        self._ctx = self._ctx.parent


class ForLoopContext:

    """
    stackable context for ForLoop to support nested for loops

    """

    index0 = property(lambda self: self.index - 1)
    first = property(lambda self: self.index == 1)
    last = property(lambda self: self.index == self.length)
    odd = property(lambda self: self.index % 2 == 1)
    even = property(lambda self: self.index % 2 == 0)
    parity = property(lambda self: ["odd", "even"][self.even])
    revindex0 = property(lambda self: self.length - self.index)
    revindex = property(lambda self: self.length - self.index + 1)

    def __init__(self, forloop, parent):
        self._forloop = forloop
        self.parent = parent

    def setup(self, seq):
        try:
            self.length = len(seq)
        except:
            self.length = 0
        self.index = 0
        for a in seq:
            self.index += 1
            yield a
        self._forloop._pop()


class Parser:

    """ """

    keywords = ("pass", "break", "continue", "return")
    statement_nodes = {
        "for": For,
        "while": Block,
        "if": If,
        "elif": Elif,
        "else": Else,
        "def": Def,
        "code": Code,
    }

    def __init__(self):
        self.statement_nodes = self.statement_nodes
        self.keywords = self.keywords

    def parse(self, text, name="<template>"):
        self.text = text
        self.name = name
        defwith, text = self.read_defwith(text)
        suite = self.read_suite(text)
        return DefWith(defwith, suite)

    def read_defwith(self, text):
        if text.startswith("$def with"):
            defwith, text = splitline(text)
            defwith = defwith[1:].strip()  # strip $ and spaces
            return defwith, text
        else:
            return "", text

    def read_section(self, text):
        r"""
        reads one section from the given text

            section -> block | assignment | line

            >>> read_section = Parser().read_section
            >>> read_section("foo\nbar\n")
            (<line: [t'foo\n']>, 'bar\n')
            >>> read_section("$ a = b + 1\nfoo\n")
            (<assignment: 'a = b + 1'>, 'foo\n')

            # TODO >>> read_section("$for i in range(10):\n  A $i\nB")
            # TODO (<block: 'for i in range(10):', [<line: [t'A ', $i, t'\n']>]>, 'B')

        """
        if text.lstrip(" ").startswith("$"):
            index = text.index("$")
            begin_indent, text2 = text[:index], text[index + 1 :]
            ahead = self.python_lookahead(text2)
            if ahead == "var":
                return self.read_var(text2)
            elif ahead in self.statement_nodes:
                return self.read_block_section(text2, begin_indent)
            elif ahead in self.keywords:
                return self.read_keyword(text2)
            elif ahead.strip() == "":
                # assignments starts with a space after $
                # ex: $ a = b + 2
                return self.read_assignment(text2)
        return self.readline(text)

    def read_var(self, text):
        r"""
        reads a `var` statement

        >>> read_var = Parser().read_var
        >>> read_var("var x=10\nfoo")
        (<var: x = 10>, 'foo')
        >>> read_var("var x: hello $name\nfoo")
        (<var: x = join_('hello ', escape_(name, True))>, 'foo')

        """
        line, text = splitline(text)
        tokens = self.python_tokens(line)
        if len(tokens) < 4:
            raise SyntaxError("Invalid var statement")
        name = tokens[1]
        sep = tokens[2]
        value = line.split(sep, 1)[1].strip()
        if sep == "=":
            pass  # no need to process value
        elif sep == ":":
            # FIXME hack for backward-compatability
            if tokens[3] == "\n":  # multi-line var statement
                block, text = self.read_indented_block(text, "        ")
                lines = [self.readline(x)[0] for x in block.splitlines()]
                _nodes = []
                for x in lines:
                    _nodes.extend(x.nodes)
                    _nodes.append(Text("\n"))
            else:  # single-line var statement
                linenode, _ = self.readline(value)
                _nodes = linenode.nodes
            parts = [node.emit("") for node in _nodes]
            value = "join_({0})".format(", ".join(parts))
        else:
            raise SyntaxError("Invalid var statement")
        return Var(name, value), text

    def read_suite(self, text):
        r"""
        reads section by section till end of text

        >>> read_suite = Parser().read_suite
        >>> read_suite("hello $name\nfoo\n")
        [<line: [t'hello ', $name, t'\n']>, <line: [t'foo\n']>]

        """
        sections = []
        while text:
            section, text = self.read_section(text)
            sections.append(section)
        return Suite(sections)

    def readline(self, text):
        r"""
        reads one line from the text

        Newline is supressed if the line ends with \.

        >>> readline = Parser().readline
        >>> readline("hello $name!\nbye!")
        (<line: [t'hello ', $name, t'!\n']>, 'bye!')
        >>> readline("hello $name!\\\nbye!")
        (<line: [t'hello ', $name, t'!']>, 'bye!')
        >>> readline("$f()\n\n")
        (<line: [$f(), t'\n']>, '\n')

        """
        line, text = splitline(text)
        # supress new line if line ends with \
        if line.endswith("\\\n"):
            line = line[:-2]
        _nodes = []
        while line:
            node, line = self.read_node(line)
            _nodes.append(node)
        return Line(_nodes), text

    def read_node(self, text):
        r"""
        reads a node from the given text and returns the node and
        remaining text

            >>> read_node = Parser().read_node
            >>> read_node("hello $name")
            (t'hello ', '$name')
            >>> read_node("$name")
            ($name, '')

        """
        if text.startswith("$$"):
            return Text("$"), text[2:]
        elif text.startswith("$#"):  # comment
            line, text = splitline(text)
            return Text("\n"), text
        elif text.startswith("$"):
            text = text[1:]  # strip $
            if text.startswith(":"):
                escape = False
                text = text[1:]  # strip `:`
            else:
                escape = True
            return self.read_expr(text, escape=escape)
        else:
            return self.read_text(text)

    def read_text(self, text):
        r"""
        reads a text node from the given text

            >>> read_text = Parser().read_text
            >>> read_text("hello $name")
            (t'hello ', '$name')

        """
        index = text.find("$")
        if index < 0:
            return Text(text), ""
        else:
            return Text(text[:index]), text[index:]

    def read_keyword(self, text):
        line, text = splitline(text)
        return Statement(line.strip() + "\n"), text

    def read_expr(self, text, escape=True):
        """
        reads a python expression from the text and returns the expression
        and remaining text

            expr -> simple_expr | paren_expr
            simple_expr -> id extended_expr
            extended_expr -> attr_access | paren_expr extended_expr | ""
            attr_access -> dot id extended_expr
            paren_expr -> [ tokens ] | ( tokens ) | { tokens }

            >>> read_expr = Parser().read_expr
            >>> read_expr("name")
            ($name, '')
            >>> read_expr("a.b and c")
            ($a.b, ' and c')
            >>> read_expr("a. b")
            ($a, '. b')
            >>> read_expr("name</h1>")
            ($name, '</h1>')
            >>> read_expr("(limit)ing")
            ($(limit), 'ing')
            >>> read_expr('a[1, 2][:3].f(1+2, "weird string[).", 3 + 4) done')
            ($a[1, 2][:3].f(1+2, "weird string[).", 3 + 4), ' done')

        """
        parens = {"(": ")", "[": "]", "{": "}"}

        def simple_expr():
            identifier()
            extended_expr()

        def identifier():
            next(tokens)

        def extended_expr():
            lookahead = tokens.lookahead()
            if lookahead is None:
                return
            elif lookahead.value == ".":
                attr_access()
            elif lookahead.value in parens:
                paren_expr()
                extended_expr()
            else:
                return

        def attr_access():
            tokens.lookahead()
            # XXX dot = tokens.lookahead()
            if tokens.lookahead2().type == token.NAME:
                next(tokens)  # XXX can remove comment? -- # consume dot
                identifier()
                extended_expr()

        def paren_expr():
            begin = next(tokens).value
            end = parens[begin]
            while True:
                if tokens.lookahead().value in parens:
                    paren_expr()
                else:
                    t = next(tokens)
                    if t.value == end:
                        break
            return

        def get_tokens(text):
            """
            tokenizes `text` using python tokenizer

            Python tokenizer ignores spaces, but they might be important in
            some cases. This function introduces dummy space tokens when it
            identifies any ignored space. Each token is a `NamedTuple` with
            attributes type, value, begin and end.

            """
            readline = iter([text]).__next__
            end = None
            for t in tokenize.generate_tokens(readline):
                t = Token(type=t[0], value=t[1], begin=t[2], end=t[3])
                if end is not None and end != t.begin:
                    _, x1 = end
                    _, x2 = t.begin
                    yield Token(type=-1, value=text[x1:x2], begin=end, end=t.begin)
                end = t.end
                yield t

        class BetterIter:

            """
            iterator-like object with support for 2 look-aheads

            """

            def __init__(self, items):
                self.iteritems = iter(items)
                self.items = []
                self.position = 0
                self.current_item = None

            def lookahead(self):
                if len(self.items) <= self.position:
                    self.items.append(self._next())
                return self.items[self.position]

            def _next(self):
                try:
                    return next(self.iteritems)
                except StopIteration:
                    return None

            def lookahead2(self):
                if len(self.items) <= self.position + 1:
                    self.items.append(self._next())
                return self.items[self.position + 1]

            def __next__(self):
                self.current_item = self.lookahead()
                self.position += 1
                return self.current_item

        tokens = BetterIter(get_tokens(text))
        if tokens.lookahead().value in parens:
            paren_expr()
        else:
            simple_expr()
        row, col = tokens.current_item.end
        return Expression(text[:col], escape=escape), text[col:]

    def read_assignment(self, text):
        r"""
        reads assignment statement from text

        >>> read_assignment = Parser().read_assignment
        >>> read_assignment("a = b + 1\nfoo")
        (<assignment: 'a = b + 1'>, 'foo')

        """
        line, text = splitline(text)
        return Assignment(line.strip()), text

    def python_lookahead(self, text):
        """
        returns the first python token from the given text

        >>> python_lookahead = Parser().python_lookahead
        >>> python_lookahead("for i in range(10):")
        'for'
        >>> python_lookahead("else:")
        'else'
        >>> python_lookahead(" x = 1")
        ' '

        """
        readline = iter([text]).__next__
        tokens = tokenize.generate_tokens(readline)
        return next(tokens)[1]

    def python_tokens(self, text):
        readline = iter([text]).__next__
        tokens = tokenize.generate_tokens(readline)
        return [t[1] for t in tokens]

    def read_indented_block(self, text, indent):
        r"""
        reads a block of text

        A block is what typically follows a `for` or `if` statement. It can
        be in the same line as that of the statement or an indented block.

        >>> read_indented_block = Parser().read_indented_block
        >>> read_indented_block("    a\n    b\nc", "    ")
        ('a\nb\n', 'c')
        >>> read_indented_block("    a\n        b\n    c\nd", "    ")
        ('a\n    b\nc\n', 'd')
        >>> read_indented_block("    a\n\n        b\nc", "    ")
        ('a\n\n    b\n', 'c')

        """
        if indent == "":
            return "", text
        block = ""
        while text:
            line, text2 = splitline(text)
            if line.strip() == "":
                block += "\n"
            elif line.startswith(indent):
                block += line[len(indent) :]
            else:
                break
            text = text2
        return block, text

    def read_statement(self, text):
        r"""
        reads a python statement

            >>> read_statement = Parser().read_statement
            >>> read_statement("for i in range(10): hello $name")
            ('for i in range(10):', ' hello $name')

        """
        tok = Tokenizer(text)
        tok.consume_till(":")
        return text[: tok.index], text[tok.index :]

    def read_block_section(self, text, begin_indent=""):
        r"""
        TODO

            >>> read_block_section = Parser().read_block_section
            >>> read_block_section("for i in range(10): hi $i\nB")
            (<block: 'for i in range(10):', [<line: [t'hi ', $i, t'\n']>]>, 'B')
            >>> read_block_section("for i in range(10):\n      hi $i\n    B",
            ...                    begin_indent="    ")
            (<block: 'for i in range(10):', [<line: [t'hi ', $i, t'\n']>]>, '    B')
            >>> read_block_section("for i in range(10):\n    hi $i\nB")
            (<block: 'for i in range(10):', [<line: [t'hi ', $i, t'\n']>]>, 'B')

        """
        line, text = splitline(text)
        stmt, line = self.read_statement(line)
        keyword = self.python_lookahead(stmt)
        # if there is some thing left in the line
        if line.strip():
            block = line.lstrip()
        else:

            def find_indent(text):
                rx = re.compile("    +")
                match = rx.match(text)
                first_indent = match and match.group(0)
                return first_indent or ""

            # find the indentation of the block by looking at the first line
            first_indent = find_indent(text)[len(begin_indent) :]
            # TODO fix this special case
            if keyword == "code":
                indent = begin_indent + first_indent
            else:
                indent = begin_indent + min(first_indent, _indent)
            block, text = self.read_indented_block(text, indent)
        return self.create_block_node(keyword, stmt, block, begin_indent), text

    def create_block_node(self, keyword, stmt, block, begin_indent):
        if keyword in self.statement_nodes:
            return self.statement_nodes[keyword](stmt, block, begin_indent)
        else:
            raise ParseError("Unknown statement: {0}".format(repr(keyword)))


Token = collections.namedtuple("Token", "type, value, begin, end")


class Tokenizer:

    """
    utility wrapper over `tokenize` token generator

    """

    def __init__(self, text):
        self.text = text
        readline = iter([text]).__next__
        self.tokens = tokenize.generate_tokens(readline)
        self.index = 0

    def consume_till(self, delim):
        """
        consume tokens until colon

            >>> tok = Tokenizer("for i in range(10): hello $i")
            >>> tok.consume_till(":")
            >>> tok.text[:tok.index]
            'for i in range(10):'
            >>> tok.text[tok.index:]
            ' hello $i'

        """
        try:
            while True:
                t = next(self)
                if t.value == delim:
                    break
                elif t.value == "(":
                    self.consume_till(")")
                elif t.value == "[":
                    self.consume_till("]")
                elif t.value == "{":
                    self.consume_till("}")
                # if end of line is found, it is an exception.
                # Since there is no easy way to report the line number,
                # leave the error reporting to the python parser later
                # TODO this should be fixed
                if t.value == "\n":
                    break
        except:
            # error_msg = "Expected {}, found end of line."
            # raise ParseError(error_msg.format(repr(delim)))
            # Raising ParseError doesn"t show the line number. If this error
            # is ignored then it will be caught when compiling the python code
            return

    def __next__(self):
        type, t, begin, end, line = next(self.tokens)
        row, col = end
        self.index = col
        return Token(type=type, value=t, begin=begin, end=end)
