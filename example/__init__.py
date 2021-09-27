"""Example IndieWeb-enabled personal site."""

from understory import web
from understory.apps import (cache, content, data, indieauth_client,
                             indieauth_server, micropub_server,
                             microsub_server, owner, search, text_editor,
                             text_reader, webmention_receiver,
                             websub_publisher, websub_subscriber)

app = web.application(
    __name__,
    db=True,
    mounts=(
        owner.app,
        search.app,
        cache.app,
        data.app,
        web.debug_app,
        indieauth_server.app,
        indieauth_client.app,
        websub.publisher.app,  # websub must come before micropub/microsub
        websub.subscriber.app,
        text_editor.app,
        micropub_server.app,
        microsub_server.app,
        text_reader.app,
        webmention_sender.app,
        webmention_receiver.app,
        content.app,  # has no prefix, must remain last
    ),
    wrappers=(
        owner.wrap,
        micropub_server.wrap,
        microsub.server.wrap,
        indieauth_server.wrap,
        indieauth_client.wrap,
        webmention.wrap,
        websub.publisher.wrap,
        template,
    ),
)
templates = web.templates(__name__)


# TODO @app.wrap
def template(handler, app):
    """Wrap response with site-wide template."""
    yield
    if web.tx.response.headers.content_type == "text/html":
        web.tx.response.body = templates.template(web.tx.response.body)


app.add_wrappers(template)
