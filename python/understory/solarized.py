"""
A color palette that adapts to the time of day.

Solarized is a sixteen color palette (eight monotones and eight accents)
designed with both precise CIELAB lightness relationships and a refined
set of hues based on fixed color wheel relationships. It is intended for
use with terminal and GUI applications.

The [Solarized][1] color palette is designed by @[Ethan Schoonover][2].

[1]: http://ethanschoonover.com/solarized
[2]: http://ethanschoonover.com

Styles based upon the original implementation `pygments-style-solarized`
by @[Shoji Kumagai](mailto:take.this.2.your.grave@gmail.com) and released
under the MIT license.

"""

# TODO import uuid

from lxml.html import builder
import lxml.html
import pygments
import pygments.formatters
import pygments.lexers
import pygments.style
from pygments.token import (Keyword, Name, Comment, String, Error,
                            Text, Number, Operator, Generic, Whitespace,
                            Other, Literal, Punctuation)  # Token

__all__ = ["highlight", "Solar", "Lunar"]


bases = _b = {"03": "002b36", "0": "839496",
              "02": "073642", "1": "93a1a1",
              "01": "586e75", "2": "eee8d5",
              "00": "657b83", "3": "fdf6e3"}
dark_bases = (_b["03"], _b["02"], _b["01"], _b["0"], _b["1"])
light_bases = (_b["3"], _b["2"], _b["0"], _b["00"], _b["01"])
colors = _c = {"yellow": "b58900", "orange": "cb4b16", "red": "dc322f",
               "magenta": "d33682", "violet": "6c71c4", "blue": "268bd2",
               "cyan": "2aa198", "green": "859900"}
palette = tuple(list(bases.values()) + list(colors.values()))
accented = [(_b["02"], _b["01"], _b["0"], _b["1"], _c["red"]),
            (_b["03"], _b["02"], _b["01"], _b["00"], _c["yellow"]),
            (_b["00"], _b["1"], _b["2"], _b["3"], _c["blue"]),
            (_b["00"], _b["0"], _b["1"], _b["2"], _c["orange"]),
            (_b["02"], _b["1"], _b["2"], _c["magenta"], _c["violet"])]


def highlight(code, filename, lines=True, starting_line=1, focus=None,
              coverage=None, failures=None):
    """Highlight given code."""
    if filename.endswith(".py"):
        lexer = pygments.lexers.Python3Lexer()
    else:
        try:
            lexer = pygments.lexers.get_lexer_for_filename(filename)
        except pygments.util.ClassNotFound:
            return code
    lexer.add_filter("codetagify")
    # TODO random_id = uuid.uuid4()
    formatter = pygments.formatters.HtmlFormatter(linenos=lines,
                                                  # TODO style="Solar",
                                                  # TODO linespans=random_id,
                                                  linespans=filename,
                                                  linenostart=starting_line)
    html = pygments.highlight(code, lexer, formatter)
    if focus:
        if isinstance(focus, int):
            focus = [focus]
        for focus_line in focus:
            # TODO given_id = "{}-{}".format(random_id, focus_line)
            given_id = focus_line
            html = html.replace(given_id, '{}" class="focus'.format(given_id))
    if coverage:
        for line, covered in coverage:
            if int(covered):
                class_name = "covered"
            else:
                class_name = "uncovered"
            current_id = '{}-{}"'.format(filename, line)
            html = html.replace(current_id,
                                '{} class="{}"'.format(current_id, class_name))
    if failures:
        for line in failures:
            current_id = "{}-{}".format(filename, line)
            html = html.replace(current_id,
                                '{}" class="failed'.format(current_id))
    doc = lxml.html.fromstring(html)
    linenos = doc.cssselect(".linenodiv pre")[0]
    ending_line = linenos.text_content().rpartition("\n")[2]
    linenos.text = ""
    for line in range(starting_line, int(ending_line) + 1):
        linenos.append(builder.A(str(line), "\n",
                                 href="#{}-{}".format(filename, line)))
    for span in doc.cssselect(".highlight pre > span"):
        if span.text:
            span.text = span.text.replace(" ", "\u00a0")
    return lxml.html.tostring(doc).decode("utf-8")


class Solar(pygments.style.Style):
    """A Pygments style based upon Solarized's light palette."""

    background_color = "#fdf6e3"
    default_style = ""

    styles = {Text:                   "#657b83",         # base00
              Whitespace:             "#fdf6e3",         # base3   w
              Error:                  "#dc322f",         # red     err
              Other:                  "#657b83",         # base00  x

              Comment:                "italic #93a1a1",  # base1   c
              Comment.Multiline:      "italic #93a1a1",  # base1   cm
              Comment.Preproc:        "italic #93a1a1",  # base1   cp
              Comment.Single:         "italic #93a1a1",  # base1   c1
              Comment.Special:        "italic #93a1a1",  # base1   cs

              Keyword:                "#859900",         # green   k
              Keyword.Constant:       "#859900",         # green   kc
              Keyword.Declaration:    "#859900",         # green   kd
              Keyword.Namespace:      "#cb4b16",         # orange  kn
              Keyword.Pseudo:         "#cb4b16",         # orange  kp
              Keyword.Reserved:       "#859900",         # green   kr
              Keyword.Type:           "#859900",         # green   kt

              Operator:               "#657b83",         # base00  o
              Operator.Word:          "#859900",         # green   ow

              Name:                   "#586e75",         # base01  n
              Name.Attribute:         "#657b83",         # base00  na
              Name.Builtin:           "#268bd2",         # blue    nb
              Name.Builtin.Pseudo:    "bold #268bd2",    # blue    bp
              Name.Class:             "#268bd2",         # blue    nc
              Name.Constant:          "#b58900",         # yellow  no
              Name.Decorator:         "#cb4b16",         # orange  nd
              Name.Entity:            "#cb4b16",         # orange  ni
              Name.Exception:         "#cb4b16",         # orange  ne
              Name.Function:          "#268bd2",         # blue    nf
              Name.Property:          "#268bd2",         # blue    py
              Name.Label:             "#657b83",         # base00  nc
              Name.Namespace:         "#b58900",         # yellow  nn
              Name.Other:             "#657b83",         # base00  nx
              Name.Tag:               "#859900",         # green   nt
              Name.Variable:          "#cd4b16",         # orange  nv
              Name.Variable.Class:    "#268bd2",         # blue    vc
              Name.Variable.Global:   "#268bd2",         # blue    vg
              Name.Variable.Instance: "#268bd2",         # blue    vi

              Number:                 "#2aa198",         # cyan    m
              Number.Float:           "#2aa198",         # cyan    mf
              Number.Hex:             "#2aa198",         # cyan    mh
              Number.Integer:         "#2aa198",         # cyan    mi
              Number.Integer.Long:    "#2aa198",         # cyan    il
              Number.Oct:             "#2aa198",         # cyan    mo

              Literal:                "#657b83",         # base00  l
              Literal.Date:           "#657b83",         # base00  ld

              Punctuation:            "#657b83",         # base00  p

              String:                 "#2aa198",         # cyan    s
              String.Backtick:        "#2aa198",         # cyan    sb
              String.Char:            "#2aa198",         # cyan    sc
              String.Doc:             "#2aa198",         # cyan    sd
              String.Double:          "#2aa198",         # cyan    s2
              String.Escape:          "#cb4b16",         # orange  se
              String.Heredoc:         "#2aa198",         # cyan    sh
              String.Interpol:        "#cb4b16",         # orange  si
              String.Other:           "#2aa198",         # cyan    sx
              String.Regex:           "#2aa198",         # cyan    sr
              String.Single:          "#2aa198",         # cyan    s1
              String.Symbol:          "#2aa198",         # cyan    ss

              Generic:                "#657b83",         # base00  g
              Generic.Deleted:        "#657b83",         # base00  gd
              Generic.Emph:           "#657b83",         # base00  ge
              Generic.Error:          "#657b83",         # base00  gr
              Generic.Heading:        "#657b83",         # base00  gh
              Generic.Inserted:       "#657b83",         # base00  gi
              Generic.Output:         "#657b83",         # base00  go
              Generic.Prompt:         "#657b83",         # base00  gp
              Generic.Strong:         "#657b83",         # base00  gs
              Generic.Subheading:     "#657b83",         # base00  gu
              Generic.Traceback:      "#657b83",         # base00  gt
              }


class Lunar(pygments.style.Style):
    """A Pygments style based upon Solarized's dark palette."""

    background_color = "#002b36"
    default_style = ""

    styles = {Text:                   "#839496",         # base0
              Whitespace:             "#002b36",         # base03 w
              Error:                  "#dc322f",         # red    err
              Other:                  "#839496",         # base0  x

              Comment:                "italic #586e75",  # base01 c
              Comment.Multiline:      "italic #586e75",  # base01 cm
              Comment.Preproc:        "italic #586e75",  # base01 cp
              Comment.Single:         "italic #586e75",  # base01 c1
              Comment.Special:        "italic #586e75",  # base01 cs

              Keyword:                "#859900",         # green  k
              Keyword.Constant:       "#859900",         # green  kc
              Keyword.Declaration:    "#859900",         # green  kd
              Keyword.Namespace:      "#cb4b16",         # orange kn
              Keyword.Pseudo:         "#cb4b16",         # orange kp
              Keyword.Reserved:       "#859900",         # green  kr
              Keyword.Type:           "#859900",         # green  kt

              Operator:               "#839496",         # base0  o
              Operator.Word:          "#859900",         # green  ow

              Name:                   "#93a1a1",         # base1  n
              Name.Attribute:         "#839496",         # base0  na
              Name.Builtin:           "#268bd2",         # blue   nb
              Name.Builtin.Pseudo:    "bold #268bd2",    # blue   bp
              Name.Class:             "#268bd2",         # blue   nc
              Name.Constant:          "#b58900",         # yellow no
              Name.Decorator:         "#cb4b16",         # orange nd
              Name.Entity:            "#cb4b16",         # orange ni
              Name.Exception:         "#cb4b16",         # orange ne
              Name.Function:          "#268bd2",         # blue   nf
              Name.Property:          "#268bd2",         # blue   py
              Name.Label:             "#839496",         # base0  nc
              Name.Namespace:         "#b58900",         # yellow nn
              Name.Other:             "#839496",         # base0  nx
              Name.Tag:               "#859900",         # green  nt
              Name.Variable:          "#cd4b16",         # orange nv
              Name.Variable.Class:    "#268bd2",         # blue   vc
              Name.Variable.Global:   "#268bd2",         # blue   vg
              Name.Variable.Instance: "#268bd2",         # blue   vi

              Number:                 "#2aa198",         # cyan   m
              Number.Float:           "#2aa198",         # cyan   mf
              Number.Hex:             "#2aa198",         # cyan   mh
              Number.Integer:         "#2aa198",         # cyan   mi
              Number.Integer.Long:    "#2aa198",         # cyan   il
              Number.Oct:             "#2aa198",         # cyan   mo

              Literal:                "#839496",         # base0  l
              Literal.Date:           "#839496",         # base0  ld

              Punctuation:            "#839496",         # base0  p

              String:                 "#2aa198",         # cyan   s
              String.Backtick:        "#2aa198",         # cyan   sb
              String.Char:            "#2aa198",         # cyan   sc
              String.Doc:             "#2aa198",         # cyan   sd
              String.Double:          "#2aa198",         # cyan   s2
              String.Escape:          "#cb4b16",         # orange se
              String.Heredoc:         "#2aa198",         # cyan   sh
              String.Interpol:        "#cb4b16",         # orange si
              String.Other:           "#2aa198",         # cyan   sx
              String.Regex:           "#2aa198",         # cyan   sr
              String.Single:          "#2aa198",         # cyan   s1
              String.Symbol:          "#2aa198",         # cyan   ss

              Generic:                "#839496",         # base0  g
              Generic.Deleted:        "#839496",         # base0  gd
              Generic.Emph:           "#839496",         # base0  ge
              Generic.Error:          "#839496",         # base0  gr
              Generic.Heading:        "#839496",         # base0  gh
              Generic.Inserted:       "#839496",         # base0  gi
              Generic.Output:         "#839496",         # base0  go
              Generic.Prompt:         "#839496",         # base0  gp
              Generic.Strong:         "#839496",         # base0  gs
              Generic.Subheading:     "#839496",         # base0  gu
              Generic.Traceback:      "#839496",         # base0  gt
              }
