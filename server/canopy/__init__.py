"""Social web platform."""

from understory import indieauth, micropub, web, webmention, websub  # microsub
from understory.apps import (cache, data, jobs,  # text_editor, text_reader
                             owner, providers, search, sites, system, tracker)

app = web.application(
    __name__,
    db=True,
    mounts=(
        owner.app,
        jobs.app,
        providers.app,
        sites.app,
        search.app,
        cache.app,
        data.app,
        system.app,
        tracker.app,
        indieauth.server.app,
        indieauth.client.app,
        micropub.server.posts.app,
        micropub.server.media.app,
        micropub.server.content.app,
        # text_editor.app,
        webmention.app,
        websub.app,
        # microsub.server.app,
        # text_reader.app,
    ),
)


def template(handler, app):
    """Wrap response with site-wide template."""
    yield
    if web.tx.response.headers.content_type == "text/html" and web.tx.response.claimed:
        if not isinstance(web.tx.response.body, str):
            web.tx.response.body = app.view.template(web.tx.response.body)


def doctype_html(handler, app):
    """Add the HTML doctype to the response."""
    yield
    if web.tx.response.headers.content_type == "text/html" and web.tx.response.claimed:
        web.tx.response.body = "<!doctype html>" + str(web.tx.response.body)


app.wrappers.insert(0, template)
app.wrappers.append(doctype_html)


@app.control("sign-in")  # TODO MOVE TO `OWNER`
class SignIn:
    """Sign in as owner or guest."""

    def get(self):
        """Show sign-in page."""
        return_url = web.form(return_url="").return_url
        return app.view.sign_in(return_url)
