## understory.web
tools for metamodern web development

    >>> import web

## Browser

uses Firefox via Selenium

    >>> # browser = web.firefox()
    >>> # browser.go("en.wikipedia.org/wiki/Pasta")
    >>> # browser.shot("wikipedia-pasta.png")

## Cache

uses SQLite

    >>> cache = web.cache()
    >>> cache["indieweb.org/note"].entry["summary"]
    'A note is a post that is typically short unstructured* plain text, written & posted quickly, that has its own permalink page.'
    >>> cache["indieweb.org/note"].entry["summary"]  # served from cache
    'A note is a post that is typically short unstructured* plain text, written & posted quickly, that has its own permalink page.'

## Templating

Full Python inside string templates.

    >>> str(web.template("$def with (name)\n$name")("Alice"))
    'Alice'

## Markdown

Strict syntax subset (there should be one and only one way).

Picoformat support eg. @person, @@org, #tag, %license

    >>> str(web.mkdn("*lorem* ipsum."))
    '<p><em>lorem</em> ipsum. </p>'

## URL parsing

Defaults to safe-mode and raises DangerousURL eagerly. Up-to-date public
suffix and HSTS support.

    >>> url = web.uri("example.cnpy.gdn/foo/bar?id=38")
    >>> url.host
    'example.cnpy.gdn'
    >>> url.suffix
    'cnpy.gdn'
    >>> url.is_hsts()
    True

### Microformat parsing

Parse `mf2` from HTML. Analyze vocabularies for stability/interoperability.
