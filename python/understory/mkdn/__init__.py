"""
Render formatted plaintext (Markdown) as HTML.

Plaintext to HTML that strives to use concise, human-readable textual anno-
tations to build rich documents of various size and purpose including but
not limited to status updates, scholarly works, screenwriting and
literate programming.

The guiding philosophy of both the syntax and features is to allow the
user as much freedom as possible to convey a message while automatically
handling the distracting, repetitive details commonly involved with pub-
lishing for the web.

    >>> str(render("foo bar"))
    '<p>foo bar </p>'

>   The idea was to make writing simple web pages ... as easy as writing
>   an email, by allowing you to use much the same syntax and converting
>   it automatically into HTML ... [and] back into Markdown.

--- Aaron Swartz, [Markdown][1] -- March 19, 2004

[1]: http://www.aaronsw.com/weblog/001189

"""

# TODO lettered-list
# TODO talk about typesetting
# TODO bibtex??
# TODO mathtex??
# TODO font-families
# TODO microformats
# TODO code[, var, kbd, ..](`), sub(_), sup(^), em(*), strong(**)
# TODO a, footnote[^abba] (w/ \u21A9), abbr, cite[@Angelo], q (w/ @cite)
# TODO table
# TODO img, figure (w/ figcaption), audio, video
# TODO smart quotes, dashes, ellipses
# TODO widont
# TODO syntax highlight
# TODO table of contents, reheader (# > h2), index, bibliography
# TODO papaya pilcrows
# TODO emoticons
# TODO l10n (charset)
# TODO math
# TODO timestamp
# TODO [tl;dr] as Abstract
# TODO formulae to formul\u00E6
# TODO slidy/S5
# TODO scan for gun violence, etc.
# TODO remove clean_indent in favor of dedent

__all__ = ["render"]

# import os
import re
from inspect import cleandoc as clean_indent
from textwrap import dedent

import lxml
import lxml.html
import lxml.html.builder as E  # noqa
import pygments
import pygments.formatters
import pygments.lexers
from understory import uri

from .titlecase import titlecase

# XXX from understory.pkg import licensing


# from . import hyphenator


# STAGES = (__all__[:], __all__[:])
LINK_CONTAINER_RE = r"\[(?P<text>.+?)\]"


class Block:
    """A block element."""

    def __init__(self, parser):
        self.parser = parser


class HTML(Block):

    """
    a block of raw HyperText

    """

    pattern = r"^<"

    def parse(self, block):
        """"""
        # if re.match(r"^</?[a-z0-9 =-]+>$", block):
        #     return E.PRE(block)  # TODO begin/end tags in blocks
        # XXX print(len(block))
        # XXX print(block)
        # XXX print()
        # XXX print()
        # XXX print()
        try:
            element = lxml.html.fromstring(block)
        except lxml.etree.ParserError:
            element = None
        return element
        # return lxml.html.fromstring(to_lga(block))


class Heading:

    """
    a generic heading

    """

    def process_heading(self, level, lines):
        """
        automatically titlecase so long as text doesn't end with " &"

        """
        sections = []
        for line in lines:
            if line.endswith("  "):
                line = line[:-2] + " <br>"
            sections.append(line)
        text = " ".join(sections)
        id_match = re.match(r".*\{(?P<id>\w[\w\d-]*[\w\d])\}$", text)
        if id_match:
            text = text.rpartition(" {")[0]
            id = id_match.group("id")
        else:
            id = text.lower().replace(" <br> ", "-").replace(" ", "-")
        text = text.rstrip()
        if text.endswith("&"):
            text = text.rstrip(" &")
            id = id.rstrip("-&")
        else:
            text = titlecase(text)
        html = "<h{0} id={1}>{2}</h{0}>"
        element = lxml.html.fromstring(html.format(level, id, text))
        # element= lxml.html.fromstring("<h{0}>{1}</h{0}>".format(level, text))
        # self.parser.toc.append((int(level), str(element.text_content()), id))
        return element


class HashHeading(Block, Heading):

    """
    a hash heading

    """

    pattern = r"^[#]{1,6}"

    def parse(self, block):
        """"""
        level = len(block.partition(" ")[0])
        lines = [line.lstrip("# ") for line in block.splitlines()]
        return self.process_heading(level, lines)


class ReSTHeading(Block, Heading):

    """
    a ReStructuredText (setext) heading

    """

    pattern = r"(?s)^.*\n(=|-)+$"

    def parse(self, block):
        """"""
        level = "1" if block[-1] == "=" else "2"
        lines = block.splitlines()[:-1]
        return self.process_heading(level, lines)


class HorizontalRule(Block):

    """
    a horizontal rule

    """

    pattern = r"^\s*((\*|-|_|:)\s*){3,}$"

    def parse(self, block):
        """"""
        return E.HR()


class List:

    """
    a generic list

    """

    def parse(self, block):
        """"""
        list = self.list_type()
        for inner_block in re.split(self.list_pattern, block)[1:]:
            item = E.LI()
            self.parser.process_blocks(item, clean_indent(inner_block))
            list.append(item)
        return list


class OrderedList(Block, List):

    """
    an ordered list

    """

    pattern = r"^([\w#][.\)]\s{2}|\w{2}[.\)]\s)\S"
    list_pattern = r"(?m)^\w{1,2}\.\s+"
    list_type = E.OL


class UnorderedList(Block, List):

    """
    an unordered list

    """

    pattern = r"^(\*|\-|\+)[ ]{3}\S"
    list_pattern = r"(?m)^[\*\-\+][ ]{3}"
    list_type = E.UL


class DefinitionList(Block):

    """
    a definition list

    """

    pattern = r"^[\w\s]+\n:\s{3}\S"

    def parse(self, block):
        """"""
        list = E.DL()
        for inner_block in re.split(r"(?m)\n    \n(?=\w)", block):
            term_block, _, definition_block = inner_block.partition("\n:   ")
            for term in term_block.splitlines():
                list.append(E.DT(term))
            for def_block in definition_block.split("\n:   "):
                definition = E.DD()
                self.parser.process_blocks(definition, clean_indent(def_block))
                list.append(definition)
        return list


class Pre(Block):

    """
    a block of preformatted text

    """

    pattern = r"^[ ]{4}"

    def parse(self, block):
        """"""
        text = dedent(block)
        if text.startswith(">>> "):
            lexer = pygments.lexers.PythonConsoleLexer()
            lexer.add_filter("codetagify")
            formatter = pygments.formatters.HtmlFormatter(cssclass="doctest")
            code = pygments.highlight(text, lexer, formatter)
            html = lxml.html.fromstring(code)
        else:
            html = E.PRE(text)
        return html


class Blockquote(Block):

    """
    a block quotation

    The block quotation is used to denote a passage significant enough to
    stand alone.

        >   when & where?
        >
        >   >   Joe's @ Noon

        # TODO >>> str(render('''
        # TODO ... >   when & where?
        # TODO ... >
        # TODO ... >   >   Joe's @ Noon'''))
        # TODO <blockquote>
        # TODO     <p>when &amp; where?</p>
        # TODO     <blockquote>
        # TODO         <p>Joe's @ Noon</p>
        # TODO     </blockquote>
        # TODO </blockquote>

    """

    pattern = r"^>"

    def parse(self, block):
        """"""
        inner_blocks = "\n".join(l[2:] for l in block.splitlines())
        tree = E.BLOCKQUOTE()
        self.parser.process_blocks(tree, inner_blocks)
        return tree


class Paragraph(Block):

    """
    a paragraph

    The paragraph is the simplest block type as well as the fallback.

        Lorem ipsum dolor sit amet.

    Lorem ipsum dolor sit amet.

        >>> str(render("Lorem ipsum dolor sit amet."))
        '<p>Lorem ipsum dolor sit amet. </p>'

    """

    pattern = r".*"

    def parse(self, block):
        """"""
        lines = []
        for line in block.splitlines():
            if line.endswith("  "):
                lines.append(line[:-2])
                lines.append(E.BR())
            else:
                lines.append(line + " ")
        return E.P(*lines)


class Inline:
    """An inline element."""

    # def __init__(self, text):
    #     self.text = text

    # def str(self):
    #     return self.template.format(**self.parse(re.match(self.pattern,
    #                                                       self.text)))


class Link(Inline):

    """

    >>> str(render("[Example](http://example.org/)"))
    '<p><a href="http://example.org">Example</a> </p>'

    """

    split_pattern = r"\[.+?\]\(.+?\)"
    pattern = LINK_CONTAINER_RE + r"(?P<uri>\(.+?\))"

    def parse(self, match):
        given_url = match.group("uri")
        if given_url.startswith(("(#", "(/")):
            url = given_url[1:-1]
        else:
            if given_url.endswith(' "wikilink")'):
                url = uri.parse(self.parser.context)
                url.path = given_url[1:-12]
            else:
                url = uri.parse(given_url[1:-1])
            url = url.normalized
        text = match.group("text")
        return f'<a href="{url}">{text}</a>'
        # return E.A(text, href=url.normalized)


class AutoLink(Inline):

    """ """

    split_pattern = r"https?://\S+"
    pattern = r"(?P<uri>https?://\S+)"

    def parse(self, match):
        url = uri.parse(match.group("uri"))
        self.parser.mentioned_urls.append(url)
        return f"<a href={url.normalized}>{url.minimized}</a>"
        # return E.A(url.minimized, href=url.normalized)


class WikiLink(Inline):

    """ """

    pattern = r"\[\[(?P<page>.+?)\]\]"

    def parse(self, match):
        # TODO define wiki prefix in renderer config
        page = match.group("page")
        path = page.replace(" ", "")  # TODO CamelCase
        return f"<a href=/pages/{path}>{page}</a>"


class Mention(Inline):

    """ """

    split_pattern = r"@[A-Za-z0-9.]+"
    pattern = r"@(?P<person>[A-Za-z0-9.]+)"

    def parse(self, match):
        if self.parser.child.tag == "a":
            self.parser.child.attrib["class"] = "h-card"
            return f"@{match.groups()[0]}"
        # TODO rel=tag for "entry" context
        person = match.group("person")
        self.parser.at_mentions.append(person)
        return f"<a class=h-card href=/people/{person}>{person}</a>"
        # return E.A(person, E.CLASS("h-card"), href=f"/people/{person}")


class Tag(Inline):

    """ """

    split_pattern = r"#[A-Za-z0-9]+"
    pattern = r"#(?P<tag>[A-Za-z0-9]+)"

    def parse(self, match):
        # TODO rel=tag for "entry" context
        tag = match.group("tag")
        self.parser.tags.append(tag)
        return f"<a class=p-category href=/tags/{tag}>{tag}</a>"
        # return E.A(tag, E.CLASS("p-category"), href=f"/tags/{tag}")


class PythonFunc(Inline):

    """ """

    pattern = r"""\$\{(?P<function>[A-Za-z0-9.'"\(\),]+)\}"""

    def parse(self, match):
        return eval(match.group("function"), self.parser.globals)


# ----------------------------------------------------------------------


class SmartQuotes:

    """"""

    pattern = r".*"

    def parse(self, match):
        punct = r"""[!"#\$\%'()*+,-.\/:;<=>?\@\[\\\]\^_`{|}~]"""
        text = match.group(0)

        # Special case if the very first character is a quote followed by
        # punctuation at a non-word-break. Close the quotes by brute force:
        text = re.sub(r"""^'(?=%s\\B)""" % (punct,), r"""&#8217;""", text)
        text = re.sub(r"""^"(?=%s\\B)""" % (punct,), r"""&#8221;""", text)

        # Special case for double sets of quotes, e.g.:
        #   <p>He said, "'Quoted' words in a larger quote."</p>
        text = re.sub(r""""'(?=\w)""", """&#8220;&#8216;""", text)
        text = re.sub(r"""'"(?=\w)""", """&#8216;&#8220;""", text)

        # Special case for decade abbreviations (the '80s):
        text = re.sub(r"""\b'(?=\d{2}s)""", r"""&#8217;""", text)

        close_class = r"""[^\ \t\r\n\[\{\(\-]"""
        dec_dashes = r"""&#8211;|&#8212;"""

        # Get most opening single quotes:
        opening_single_quotes_regex = re.compile(
            r"""
                (
                    \s          |   # a whitespace char, or
                    &nbsp;      |   # a non-breaking space entity, or
                    --          |   # dashes, or
                    &[mn]dash;  |   # named dash entities
                    %s          |   # or decimal entities
                    &\#x201[34];    # or hex
                )
                '                 # the quote
                (?=\w)            # followed by a word character
                """
            % (dec_dashes,),
            re.VERBOSE,
        )
        text = opening_single_quotes_regex.sub(r"""\1&#8216;""", text)

        closing_single_quotes_regex = re.compile(
            r"""
                (%s)
                '
                (?!\s | s\b | \d)
                """
            % (close_class,),
            re.VERBOSE,
        )
        text = closing_single_quotes_regex.sub(r"""\1&#8217;""", text)

        closing_single_quotes_regex = re.compile(
            r"""
                (%s)
                '
                (\s | s\b)
                """
            % (close_class,),
            re.VERBOSE,
        )
        text = closing_single_quotes_regex.sub(r"""\1&#8217;\2""", text)

        # Any remaining single quotes should be opening ones:
        text = re.sub(r"""'""", r"""&#8216;""", text)

        # Get most opening double quotes:
        opening_double_quotes_regex = re.compile(
            r"""
                (
                    \s          |  # a whitespace char, or
                    &nbsp;      |  # a non-breaking space entity, or
                    --          |  # dashes, or
                    &[mn]dash;  |  # named dash entities
                    %s          |  # or decimal entities
                    &\#x201[34];   # or hex
                )
                "                  # the quote
                (?=\w)             # followed by a word character
                """
            % (dec_dashes,),
            re.VERBOSE,
        )
        text = opening_double_quotes_regex.sub(r"""\1&#8220;""", text)

        # Double closing quotes:
        closing_double_quotes_regex = re.compile(
            r"""
                #(%s)?  # character that indicates the quote should be closing
                "
                (?=\s)
                """
            % (close_class,),
            re.VERBOSE,
        )
        text = closing_double_quotes_regex.sub(r"""&#8221;""", text)

        closing_double_quotes_regex = re.compile(
            r"""
                (%s)   # character that indicates the quote should be closing
                "
                """
            % (close_class,),
            re.VERBOSE,
        )
        text = closing_double_quotes_regex.sub(r"""\1&#8221;""", text)

        # Any remaining quotes should be opening ones.
        text = re.sub(r'"', r"""&#8220;""", text)

        lsquo = r"""<span class="lsquo"><span>'</span></span>"""
        rsquo = r"""<span class="rsquo"><span>'</span></span>"""
        ldquo = r"""<span class="ldquo"><span>"</span></span>"""
        rdquo = r"""<span class="rdquo"><span>"</span></span>"""

        text = text.replace("&#8216;", lsquo)
        text = text.replace("&#8217;", rsquo)
        text = text.replace("&#8220;", ldquo)
        text = text.replace("&#8221;", rdquo)

        return text


class AutoMagnet(Inline):

    """ """

    pattern = r"(?P<uri>magnet:.+?)"

    def parse(self, match):
        uri = match.group("uri")
        return '<a href="{0}">{0}</a>'.format(uri)


class Reference(Inline):

    """

    # TODO >>> str(render('''[Example][1]
    # TODO ...
    # TODO ... [1]: http://example.org'''))
    # TODO '<a href="http://example.org">Example</a>'

    """

    pattern = LINK_CONTAINER_RE + r"\[(?P<reference_id>.+?)\]"
    template = '<a href="{uri}">{text}</a>'

    def parse(self, match):
        text = match.group("text")
        reference_id = match.group("reference_id")
        try:
            uri = self.parser.refs[reference_id]
        except KeyError:
            uri = ""  # XXX catch in parser and store as warning
            # raise ReferenceError("no reference for " + reference_id)
        return self.template.format(uri=uri, text=text)


class AutoReference:

    """ """

    pattern = LINK_CONTAINER_RE
    template = '<a href="{uri}">{text}</a>'

    def parse(self, match):
        text = match.group("text")
        # XXX reference = lxml.html.fromstring(from_lga(text)).text_content()
        reference = lxml.html.fromstring(text).text_content()
        try:
            uri = self.parser.refs[reference]
        except KeyError:
            return match.group(0)
        return self.template.format(uri=uri, text=text)


class ImageLink(Link):

    """"""

    pattern = "!" + Link.pattern

    def parse(self, match):
        """"""
        text = match.group("text")
        uri = match.group("uri").strip("()")
        try:
            return '<img src="{0}" alt="{1}">'.format(uri, text)
        except KeyError:
            return match.group(0)


class ImageReference(Reference):

    """"""

    pattern = "!" + Reference.pattern

    def parse(self, match):
        text = match.group("text")
        reference_id = match.group("reference_id")
        try:
            uri = self.parser.refs[reference_id]
        except KeyError:
            return text
        return '<img src="{0}" alt="{1}">'.format(uri, text)


class ImageAutoReference(AutoReference):

    """"""

    pattern = "!" + AutoReference.pattern

    def parse(self, match):
        text = match.group("text")
        try:
            uri = self.parser.refs[text]
        except KeyError:
            return ""
        return '<img src="{0}" alt="{1}">'.format(uri, text)


# class LicenseLink(Link):
#
#     """"""


# class LicenseReference(Reference):
#
#     """"""


# class LicenseAutoReference(AutoReference):
#
#     """"""
#
#     pattern = "%" + AutoReference.pattern
#
#     def parse(self, match):
#         alias = match.group(1)
#         try:
#             uri, name, version = licensing.get_license(alias)
#         except licensing.LookupError:
#             return alias
#         anchor_template = '<a href="http://{}" rel=license>{} License</a>'
#         return anchor_template.format(uri, name)


# class OrgLink(Link):
#
#     """"""
#
#     template = """"""


# class OrgReference(Reference):
#
#     """"""
#
#     template = '<span class="vcard h-card"><a class="fn p-fn '
#                'org h-org url u-url" href="{0}">{1}</a></span>'


# class OrgAutoReference(AutoReference):
#
#     """"""
#
#     pattern = "@@" + AutoReference.pattern
#     template = """<span class=h-card>{0}</span>"""
#
#     def parse(self, match):
#         text = match.group(1)
#         wrapper = '<span class="vcard h-card">{0}</span>'
#         try:
#             uri = self.parser.refs[text]
#         except KeyError:
#             return self.template.format('<span class="fn '
#                                         'org">{0}</span>'.format(text))
#         return wrapper.format('<a class="fn org url" '
#                               'href="{0}">{1}</a>'.format(uri, text))


# class PersonLink(Link):
#
#     """
#
#     """
#
#     pattern = "@" + Link.pattern
#     format_string = """<span class="vcard h-card">
#                        <a class="fn p-fn org h-org url u-url"
#                        href="{uri}">{text}</a>
#                        </span>"""


# class PersonReference(Reference):
#
#     """"""
#
#     template = """<span class="vcard h-card"><a class="fn """
#                """p-fn url u-url" href="{0}">{1}</a></span>"""


# class PersonAutoReference(AutoReference):
#
#     """"""
#
#     def parse(self, match):
#         """"""
#         text = match.group(1)
#         wrapper = u'<span class="vcard h-card">{0}</span>'
#         try:
#             uri = self.parser.refs[text]
#         except KeyError:
#             if "{" in text:
#                 text = text.replace("}", "</span>")
#                 z = re.compile(r"\{(?P<semantics>[\w,-]+):")
#
#                 def y(m):
#                     semantics = m.group("semantics").split(",")
#                     classes = " ".join(pr[2:] + " " + pr for pr in semantics)
#                     return u'<span class="{0}">'.format(classes)
#
#                 return wrapper.format(z.sub(y, text))
#             return wrapper.format(u'<span class="fn '
#                                   u'p-fn">{0}</span>'.format(text))
#         return wrapper.format(u'<a class="fn p-fn url u-url" '
#                               u'href="{0}">{1}</a>'.format(uri, text))


class Section:

    """"""

    pattern = r"(?P<symbol>SS?)\s+(?P<section>[\d.]+)"

    def parse(self, match):
        symbol = match.group("symbol")
        section = match.group("section")
        html = '<span class="x-section"><span>S</span></span>'
        return "&nbsp;".join((" ".join([html] * len(symbol)), section))


class Widow:

    """"""

    pattern = r"(?P<before>[\w\[\]]+)\s(?P<after>[\w'\[\]]+[\.,)]*\s*)$"

    def parse(self, match):
        return "&nbsp;".join((match.group("before"), match.group("after")))


# class SmallCapitals:
#
#     pattern = r"""
#         (?x)
#         \b
#         (?P<acronym>
#             AT&T | Q&A |
#             [A-Z\d][A-Z\d\./]{2,} |
#             [A-Z]{2,}
#         )
#         \b
#     """
#
#     def parse(self, match):
#         html = "<span class=x-small-caps>{0}</span>"
#         acronym = match.group("acronym")
#         # if self.roman_numeral_pattern.match(acronym).group("numeral"):
#         #     # html = "<span class=x-suggest-caps>{0}</span>"
#         #     return acronym
#         #     # if self.config["stage"] == "publish":
#         #     #     if acronym not in self.config["proofed"]:
#         #     #         return acronym
#         #     # else:
#         #     #     html = "<span class=x-suggest-caps>{0}</span>"
#         return html.format(acronym)
#
#     # Copyright (c) 2009, Mark Pilgrim, BSD License
#     roman_numeral_pattern = re.compile(r"""(?x)
#                                            (?P<numeral>
#                                                M{0,4}            # thousands
#                                                (CM|CD|D?C{0,3})  # hundreds
#                                                (XC|XL|L?X{0,3})  # tens
#                                                (IX|IV|V?I{0,3})  # ones
#                                            )""")


class StrongEm(Inline):

    # pattern = r"""\*{3}([\w\s\-.,'"]+)\*{3}"""
    pattern = r"""\*{3}(.+?)\*{3}"""

    def parse(self, match):
        text = match.group(1)
        return "<strong><em>{0}</em></strong>".format(text)


class Strong(Inline):

    # pattern = r"""\*{2}([\w\s\-.,'"]+)\*{2}"""
    pattern = r"""\*{2}(.+?)\*{2}"""

    def parse(self, match):
        text = match.group(1)
        return "<strong>{0}</strong>".format(text)


class Em(Inline):

    # pattern = r"""\*([\w\s\-.,'"]+)\*"""
    pattern = r"""\*(.+?)\*"""

    def parse(self, match):
        text = match.group(1)
        return "<em>{0}</em>".format(text)


class Small(Inline):

    # pattern = r"""~([\w\s\-/<>%!.,'"]+)~"""
    pattern = r"""(?s)~(.+?)~"""

    def parse(self, match):
        text = match.group(1)
        return "<small>{0}</small>".format(text)


class Code(Inline):

    pattern = r"""(?s)`(.+?)`"""

    def parse(self, match):
        text = match.group(1)
        return "<code>{0}</code>".format(text)


class Ampersand(Inline):

    pattern = r" %!amp!% "

    def parse(self, match):
        return " <span class=x-amp>%!amp!%</span> "


class Copyright(Inline):

    pattern = r" \(c\) "

    def parse(self, match):
        return " &copy; "


class Ellipsis(Inline):

    pattern = r"\.\.\."

    def parse(self, match):
        # return "<span class=ellipsis><span>...</span></span>"
        return "&hellip;"


class QuotationDash(Inline):

    pattern = r"^---"

    def parse(self, match):
        return "<span class=quotation-dash><span>---</span></span>"


class DblEmDash(Inline):

    pattern = r"----"

    def parse(self, match):
        # return "<span class=em-dash><span>--</span></span>" * 2
        return "&emdash;" * 2


class EmDash(Inline):

    pattern = r"---"

    def parse(self, match):
        return "<span class=em-dash><span>&#x2014;</span></span>"


class InnerEmDash(Inline):

    pattern = r" --- "

    def parse(self, match):
        # return '<span class="em-dash inner"><span> --- </span></span>'
        return "&thinsp;&#x2014;&thinsp;"


class EnDash(Inline):

    pattern = r"--"

    def parse(self, match):
        return "<span class=en-dash><span>&#x2013;</span></span>"


class InnerEnDash(Inline):

    pattern = r" -- "

    def parse(self, match):
        # return '<span class="en-dash inner"><span>--</span></span>'
        return "&thinsp;&#x2013;&thinsp;"


class LigatureAE(Inline):

    pattern = r"(?i)(ae)"

    def parse(self, match):
        html = '<span class="x-ligature-ae x-{0}"><span>{1}</span></span>'
        cases = {"ae": "lower", "AE": "upper", "Ae": "upper"}
        m = match.group(1)
        return html.format(cases[m], m)


class Heart(Inline):

    pattern = r" <3 "

    def parse(self, match):
        return " &#x2764; "


# class Hyphenate(Inline):
#
#     # pattern = r"(?<!%!amp!%nbsp;)(?P<word>\w{4,}[\., \n])"
#     pattern = r"(?P<word>\w{4,}[\., \n])"
#
#     def parse(self, match):
#         hyphen_dict = os.path.dirname(__file__) + "/hyph_en_US.dic"
#         hyphenate = hyphenator.Hyphenator(hyphen_dict)
#         word = match.group("word")
#         sections = []
#         for section in word.split("-"):
#             sections.append(hyphenate.inserted(section).replace("-",
#                                                                 "&shy;"))
#         hyphenated = "-".join(sections)
#         start, _, final = hyphenated.rpartition("&shy;")
#         if len(final.strip()) < 3:  # or (final.endswith(".") and
#                                     # len(final.strip()) < 4):  # an-oth-er.
#             hyphenated = start + final
#         return hyphenated


gun_violence = {
    "Ammunition": "facts, evidence",
    "armed with the facts": "well-informed",
    "aim for": "hope to achieve",
    "ask point blank": "ask directly",
    "bite the bullet": "just do it",
    "bullet points": "specifics, key points",
    "bullet-proof": "invincible",
    "caught in the crossfire": "caught in the middle",
    "cheap shot": "unfair criticism",
    "dodged a bullet": "avoided trouble",
    "don't shoot the messenger": "not responsible",
    "even shot": "50/50 chance",
    "faster than a speeding bullet": "turbo speed",
    "'Fire Away!'": "'Get started!'",
    "firing blanks": "not succeeding",
    "fire back": "responding quickly",
    "going great guns": "succeeding beyond expectations",
    "gun it": "floor it",
    "gun shy": "reticent",
    "gunning for someone": "planning to harm",
    "half-cocked": "reckless",
    "high caliber": "exceptional",
    "hired gun": "paid specialist",
    "hold a gun to my head": "threaten",
    "hot shot": "show-off, braggart",
    "in the crosshairs": "scrutinized",
    "jumped the gun": "started too early",
    "'Just shoot me!'": "'I give up!'",
    "kill joy": "spoil sport",
    "killer instinct": "ruthless",
    "like shooting fish in a barrel": "too easy",
    "lock, stock and barrel": "all inclusive",
    "locked-and-loaded": "ready, prepared",
    "magic bullet": "perfect solution",
    "misfired": "erred",
    "missed the mark": "imperfect, fell short",
    "moving target": "hard to pin down",
    "outgunned": "outmatched",
    "on target": "accurate",
    "point blank": "direct, precise, simple",
    "point & shoot": "camera reference",
    "pot shots": "jabs",
    "pull the trigger": "get going",
    "quick on the trigger": "rash, hasty",
    "rapid fire": "quickly",
    "'Ready, aim, fire!'": "'Go!'",
    "riding shot gun": ("occupying the passenger seat", "protecting a companion"),
    "rifle through files": "search",
    "'She/he is a pistol!'": "'She/he has spunk!'",
    "shoot first, ask later": "impetuous",
    "shoot for": "try",
    "shoot for the moon": "set high goals",
    "shoot from the hip": "impulsive",
    "shoot me an email": "send me an email",
    "shoot off your mouth": "talk recklessly",
    "shoot out": "confrontation",
    "shoot the breeze": "chat, visit",
    "shot down my idea": "rejected",
    "shot in the dark": "wild guess",
    "shot myself in the foot": "made a mistake",
    "silver bullet": "perfect solution",
    "smoking gun": "proof beyond doubt",
    "'Son of a gun!'": "'Darn!'",
    "stick to my guns": "uncompromising",
    "straight shooter": "frank & honest",
    "sweating bullets": "really worried",
    "take aim": "focus",
    "take a shot at": "give it a try",
    "target market": "audience segment",
    "top gun": "recognized expert",
    "trigger a response": "elicit a response",
    "trigger alerts": "heads up, warnings",
    "trigger happy": "impulsive",
    "trip your trigger": "make you happy",
    "under fire": "being criticized",
    "under the gun": "feeling time pressured",
    "whole shooting match": "in total",
    "with guns blazing": "all-out effort",
    "worth a shot": "worth trying",
    "'You're killing me!'": "'You're too much!'",
}

# ---- PARSER.PY --------------------------------------------------------------

import zlib  # TODO more useful hash?

import lxml.html
import lxml.html.builder as E  # noqa
import regex as re

block_elements = [
    HTML,
    Pre,
    HashHeading,
    ReSTHeading,
    HorizontalRule,
    OrderedList,
    UnorderedList,
    DefinitionList,
    Blockquote,
    Paragraph,
]

inline_elements = [  # "SmartQuotes",
    # # "SmallCapitals",
    # # "LicenseLink", "LicenseReference",
    # #   "LicenseAutoReference",
    # # "OrgLink", "OrgReference", "OrgAutoReference",
    # # "PersonLink", "PersonReference", "PersonAutoReference",
    ImageLink,
    ImageReference,
    ImageAutoReference,
    # "WikiLink",
    # "Reference", "AutoReference",
    # "AutoMagnet",
    # "Section", "Widow",
    StrongEm,
    Strong,
    Em,
    Small,
    Code,
    Link,
    AutoLink,
    WikiLink,
    Mention,
    Tag,
    PythonFunc,
    # "Ampersand", "Copyright", "Ellipsis", "LigatureAE",
    #    "Heart",
    # "QuotationDash", "DblEmDash",
    # "InnerEmDash",
    EmDash,
    # "InnerEnDash",
    EnDash,
    # # "Hyphenate",
]

_LT = "%!lt!%"
_GT = "%!gt!%"
_LTS = "%!lts!%"
_GTS = "%!gts!%"
_AMP = "%!amp!%"

reference_pattern = re.compile(r"\s*\[([\w\s-]+)\]:\s+(.{2,})")
abbreviation_pattern = re.compile(r"\s*\*\[([\w\s-]+)\]:\s+(.{2,})")


def obfuscate_references(mahna):
    """TODO."""
    references = {}
    for chunk in re.split(r"\n{2,}", mahna):
        reference_match = reference_pattern.match(chunk)
        if reference_match:
            for id, uri in reference_pattern.findall(chunk):
                references.update({id + "---" + str(zlib.adler32(uri)): uri})
            continue
    for id in references.keys():
        before = "[{}]".format(id.partition("---")[0])
        after = "[{}]".format(id)
        mahna = mahna.replace(before, after)
    return mahna


def preprocess_lga(text):
    text = text.replace("<", _LT)
    text = text.replace(">", _GT)
    text = text.replace("&lt;", _LTS)
    text = text.replace("&gt;", _GTS)
    text = text.replace("&", _AMP)
    return text


def postprocess_lga(text):
    text = str(text)
    text = text.replace(_LT, "<")
    text = text.replace(_GT, ">")
    text = text.replace(_AMP, "&")
    return text


def preprocess_script_style_pre_textarea(mahna):
    def esc(m):
        return m.group(0).replace("\n", "%!nl!%")

    mahna = re.sub(r"(?s)<script.*?>(.*?)</script>", esc, mahna)
    mahna = re.sub(r"(?s)<style.*?>(.*?)</style>", esc, mahna)
    mahna = re.sub(r"(?s)<pre.*?>(.*?)</pre>", esc, mahna)
    mahna = re.sub(r"(?s)<textarea.*?>(.*?)</textarea>", esc, mahna)
    return mahna


def preprocess_inline_code(mahna):
    # TODO !!! escape from inside <pre></pre>
    return mahna
    # TODO handle "an inline code block, `\`<div>\``, preprocessor"

    def escape_match_handler(m):
        return "<code>{0}</code>".format(preprocess_lga(m.group(0).strip("`")))

    return re.sub(r"`(.*?)`", escape_match_handler, mahna)


def preprocess_hyphens(mahna):
    new_lines = []
    queue = []
    for line in mahna.splitlines():
        if line != "-" and not line.endswith("--") and line.endswith("-"):
            queue.append(line[:-1])
            continue
        queued = ""
        if len(queue) > 0:
            queued += queue[0]
            line = line.lstrip(" >")
        if len(queue) > 1:
            queued += "".join(line.strip(" >") for line in queue[1:])
        new_lines.append(queued + line)
        queue = []
    return "\n".join(new_lines)


def postprocess_script_style_pre_textarea_code(html):
    html = html.replace("%!nl!%", "\n")
    html = html.replace("%!lts!%", "&lt;")
    html = html.replace("%!gts!%", "&gt;")
    return html


class Document:
    """A Markdown parser."""

    def __init__(self, text, context=None, globals=None):
        """Return a  after parsing the Markdown text."""
        self.abbrs = {}
        self.refs = {}
        self.toc = []
        self.tags = []
        self.at_mentions = []
        self.mentioned_urls = []
        self.context = context
        self.globals = globals if globals else {}
        self.process(text)

    def process(self, mahna):  # , options=None):
        # document = render(mahna)  # TODO prerender?
        # document = "<meta charset=utf-8>\n" + mahna
        mahna = "\n\n" + str(mahna).strip()
        mahna = preprocess_script_style_pre_textarea(mahna)
        mahna = preprocess_inline_code(mahna)
        mahna = preprocess_hyphens(mahna)

        body = E.DIV()
        self.process_blocks(body, mahna)
        output = lxml.html.tostring(body, encoding="utf-8").decode("utf-8")

        output = output.replace("<p>" + _LT, "<")
        output = output.replace(_GT + "</p>", ">")
        output = postprocess_lga(output)

        dom = lxml.html.fromstring(output)
        dom = E.BODY(dom)
        dom[0].drop_tag()

        for handler in inline_elements:
            # XXX handler = getattr(inline, name)()
            self.proc_inlines(handler(), dom)
            output = lxml.html.tostring(dom, encoding="utf-8").decode("utf-8")
            output = postprocess_lga(output)
            dom = lxml.html.fromstring(output)

        # self.process_inlines(0, dom)
        # output = lxml.html.tostring(dom, encoding="utf-8").decode("utf-8")
        # output = postprocess_lga(output)
        # dom = lxml.html.fromstring(output)

        dom = E.BODY(dom)

        # TODO repeat setup and teardown for each inline handler as hacked
        #      below for hyphenation -- isolate link creation as root cause?

        # self.process_inlines(1, dom)
        # output = lxml.html.tostring(dom, encoding="utf-8").decode("utf-8")
        # output = postprocess_lga(output)
        # dom = lxml.html.fromstring(output)

        self.process_abbreviations(dom)

        output = lxml.html.tostring(dom, pretty_print=True, encoding="utf-8").decode(
            "utf-8"
        )
        output = lxml.html.tostring(dom, pretty_print=True).decode("utf-8")

        output = postprocess_lga(output)
        output = postprocess_script_style_pre_textarea_code(output)

        # XXX here be dragons -- skips jumps in hierarchy (e.g. h5 follows h3)
        top_heading_level = 1

        def tocify(_toc, curr):
            section = E.OL()
            i = 0
            for level, text, id in _toc:
                i += 1
                if level == top_heading_level:
                    continue
                if level < curr:
                    return section
                if level == curr:
                    section.append(
                        E.LI(E.A(text, href="#" + id), tocify(_toc[i:], curr + 1))
                    )
            return section

        toc = tocify(self.toc, top_heading_level + 1)
        toc.set("id", "toc")  # toc["id"] = "toc"
        for ol in toc.cssselect("ol"):  # XXX two words, rhymes with bucket
            if ol.getparent() is not None and not len(ol):
                ol.drop_tag()
        output = output.replace("<p>[Contents] </p>", str(lxml.html.tostring(toc)))

        # if options and options.document:
        #     try:
        #         title = document.title
        #     except AttributeError:
        #         title = body.cssselect("h1")[0].text_content()
        #     self.stylesheet = "<style>{0}</style>".format(self.stylesheet)
        #     try:
        #         style = self.stylesheet + document.stylesheet
        #     except AttributeError:
        #         style = self.stylesheet
        #     output = html.template(options.language, title, style, output)
        # XXX sometimes `lxml` wraps with a <div> .. sometimes it doesn't
        # XXX probably something to do with fromstring/tostring    fffuuuuuu
        # elif output.startswith("<div>"):
        output = output.strip()
        if output.startswith("<body>"):
            output = output[6:-7]
        output = output.strip()
        if output.startswith("<div>"):
            output = output[5:-6]
        output = output.strip()
        if output.startswith("<p></p>"):
            output = output[8:]
        # XXX if inline:
        # XXX     html = html[html.find(">")+1:html.rfind("<")]
        self.html = output

    def process_blocks(self, parent, mahna):
        for chunk in re.split(r"\n{2,}", mahna):
            reference_match = reference_pattern.match(chunk)
            if reference_match:
                self.refs.update(reference_pattern.findall(chunk))
                continue
            abbreviation_match = abbreviation_pattern.match(chunk)
            if abbreviation_match:
                self.abbrs.update(abbreviation_pattern.findall(chunk))
                continue
            for handler in block_elements:
                # XXX handler = getattr(block, name)(self)
                handler = handler(self)
                match = re.match(handler.pattern, chunk)
                if match:
                    # XXX try:
                    # XXX     encoded_chunk = chunk.decode("utf-8")
                    # XXX except UnicodeEncodeError:
                    # XXX     encoded_chunk = chunk
                    encoded_chunk = chunk

                    # try:
                    element = handler.parse(encoded_chunk)
                    if element is not None:
                        parent.append(element)
                    # except ValueError:
                    #     chunk = "".join(c if ord(c) < 128 else
                    #                     c+"!?" for c in chunk)
                    #     print("Found non Unicode or ASCII char in chunk:",
                    #                 chunk, sep="\n\n", file=sys.stderr)
                    #     sys.exit(1)
                    break

    def proc_inlines(self, handler, parent):
        for child in parent:
            if child.tag in ("script", "style", "pre", "code", "textarea"):
                continue
            handler.parser = self
            self.child = child
            if child.text:
                child.text = re.sub(handler.pattern, handler.parse, child.text)
            if child.tail:
                child.tail = re.sub(handler.pattern, handler.parse, child.tail)
            if child.text:
                child.text = preprocess_lga(child.text)
            if child.tail:
                child.tail = preprocess_lga(child.tail)
            self.proc_inlines(handler, child)

    # def process_inlines(self, stage, parent):
    #     for child in parent:
    #         if child.tag in ("script", "style", "pre", "code", "textarea"):
    #             continue
    #         handler_names = inline.__all__ if stage == 0 else ["Hyphenate"]
    #         for handler_name in handler_names:
    #             handler = getattr(inline, handler_name)()
    #             handler.parser = self
    #             # XXX self.child = child
    #             # XXX self.parent = parent

    #             if child.text:
    #                 while True:
    #                     found = re.split(f"({handler.split_pattern})",
    #                                      child.text)
    #                     print()
    #                     print(handler_name, child.text)
    #                     # print(handler.pattern)
    #                     # print(child.text)
    #                     print(found)
    #                     if len(found) < 3:
    #                         break
    #                     before = "".join(found[:-2])
    #                     matched_text, after = found[-2:]
    #                     child.text = before
    #                     match = re.match(handler.pattern, matched_text)
    #                     replacement = handler.parse(match)
    #                     # if isinstance(replacement, lxml.html.HtmlElement):
    #                     replacement.tail = after
    #                     child.insert(0, replacement)
    #                     # print(lxml.html.tostring(replacement))
    #                     # else:
    #                     #     child.text += replacement + after
    #                     # print(child.text)
    #                     # print(lxml.html.tostring(child))

    #             # if child.text:
    #             #     child.text = re.sub(handler.pattern, handler.parse,
    #             #                         child.text)

    #             # if child.tail:
    #             #     child.tail = re.sub(handler.pattern, handler.parse,
    #             #                         child.tail)
    #         if child.text:
    #             child.text = preprocess_lga(child.text)
    #         if child.tail:
    #             child.tail = preprocess_lga(child.tail)
    #         self.process_inlines(stage, child)

    def process_abbreviations(self, parent):
        for child in parent:
            if child.tag in ("script", "style", "pre", "code", "textarea"):
                continue
            for abbr, full in self.abbrs.items():
                html = '<abbr title="{}">{}</abbr>'.format(full, abbr)
                if child.text:
                    child.text = preprocess_lga(child.text.replace(abbr, html))
                if child.tail:
                    child.tail = preprocess_lga(child.tail.replace(abbr, html))
            self.process_abbreviations(child)

    def __str__(self):
        return self.html


render = Document
