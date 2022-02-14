"""
Render Python powered string templates.

>   But you're right, it is "yet another template language". And I'm not
>   going to apologize for it.

--- Aaron Swartz

Syntax
------

*   secure Python via [Templetor]
*   a strict superset dialect of [Markdown]
*   literate programming aided by [reStructuredText]
*   mathematical formulae a la [LaTeX]

Features
--------

*   spell check based upon GNU's Aspell (91 countries)
*   style conformance according to:

    *   [The Elements of Style]
    *   [The Elements of Typographic Style]

The following example demonstrates headings, block quotation, paragraphs,
ellipses, em dash, smart quotes, Microformats (hCard), lowercased figures,
title case, auto-reference and spell check.

(217 characters to 450+ including X codes.)

    # TODO >>> mana('''
    # TODO ... On nonsnse in prose  {nonsense}
    # TODO ... ===============================
    # TODO ...
    # TODO ... > ...
    # TODO ... > Beware the Jubjub bird, and shun
    # TODO ... > The frumious Bandersnatch!
    # TODO ... > ...
    # TODO ...
    # TODO ... --- @[Lewis Carroll], "Through the Looking-Glass,
    # TODO ...                        and What Alice Found There" 1872
    # TODO ... ''', stage='proof')  #doctest: +NORMALIZE_WHITESPACE
    # TODO '<h1 id=nonsense><a href=#nonsense>On <span class=x-spelling><span
    # TODO class=x-error>Nonsnse</span> (<span class=x-suggestions>Nonsense,
    # TODO Nonsenses, Nansen's, Nonsense's, Ninon's, Jonson's</span>)</span> in
    # TODO Prose</a></h1><blockquote><p>&#x; Be&shy;ware the Jub&shy;jub bird,
    # TODO and shun<br>The frumious Bandersnatch!&nbsp;&#x;</p></blockquote><p>&#x;
    # TODO <span class=h-card>Lew&shy;is Carroll</span>, &#x;Through the
    # TODO Look&shy;ing-Glass, and What Al&shy;ice Found There&#x;&nbsp;<span
    # TODO class=>1872</span></p>'

"""

from .templating import Template, TemplatePackage, build, templates

__all__ = ["templates", "build", "Template", "TemplatePackage"]
