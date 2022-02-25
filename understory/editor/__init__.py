"""Micropub editor."""

import web

app = web.application(__name__, prefix="editor")


@app.control("")
class Editor:
    """The editor."""

    def get(self):
        """Return the editor."""
        return app.view.editor()


@app.control("preview/markdown")
class PreviewMarkdown:
    """"""

    def get(self):
        return (
            "<form method=post>"
            "<textarea name=content></textarea>"
            "<button>Preview</button>"
            "</form>"
        )

    def post(self):
        form = web.form("content", context=None)
        rendered = str(
            web.mkdn(form.content, form.context, globals=micropub.markdown_globals)
        )
        web.header("Content-Type", "application/json")
        return {
            "content": rendered,
            "readability": micropub.readability.Readability(form.content).metrics,
        }


@app.control("preview/resource")
class PreviewResource:
    """"""

    def get(self):
        url = web.form(url=None).url
        web.header("Content-Type", "application/json")
        if not url:
            return {}
        resource = web.get(url)
        return resource.entry

        # XXX data = cache.parse(url)
        # XXX if "license" in data["data"]["rels"]:
        # XXX     data["license"] = data["data"]["rels"]["license"][0]
        # XXX try:
        # XXX     edit_page = data["html"].cssselect("#ca-viewsource a")[0]
        # XXX except IndexError:
        # XXX     # h = html2text.HTML2Text()
        # XXX     # try:
        # XXX     #     data["content"] = h.handle(data["entry"]["content"]).strip()
        # XXX     # except KeyError:
        # XXX     #     pass
        # XXX     try:
        # XXX         markdown_input = ("html", data["entry"]["content"])
        # XXX     except (KeyError, TypeError):
        # XXX         markdown_input = None
        # XXX else:
        # XXX     edit_url = web.uri.parse(str(data["url"]))
        # XXX     edit_url.path = edit_page.attrib["href"]
        # XXX     edit_page = fromstring(requests.get(edit_url).text)
        # XXX     data["mediawiki"] = edit_page.cssselect("#wpTextbox1")[0].value
        # XXX     data["mediawiki"] = (
        # XXX         data["mediawiki"].replace("{{", r"{!{").replace("}}", r"}!}")
        # XXX     )
        # XXX     markdown_input = ("mediawiki", data["mediawiki"])

        # XXX if markdown_input:
        # XXX     markdown = str(
        # XXX         sh.pandoc(
        # XXX         "-f", markdown_input[0], "-t", "markdown", _in=markdown_input[1]
        # XXX         )
        # XXX     )
        # XXX     for n in range(1, 5):
        # XXX         indent = "    " * n
        # XXX         markdown = markdown.replace(f"\n{indent}-",
        # XXX                                     f"\n{indent}\n{indent}-")
        # XXX     markdown = re.sub(r'\[(\w+)\]\(\w+ "wikilink"\)', r"[[\1]]", markdown)
        # XXX     markdown = markdown.replace("–", "--")
        # XXX     markdown = markdown.replace("—", "---")
        # XXX     data["content"] = markdown

        # XXX data.pop("html")
        # XXX # XXX data["category"] = list(set(data["entry"].get("category", [])))
        # XXX web.header("Content-Type", "application/json")
        # XXX return dump_json(data)
