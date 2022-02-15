"""Social web platform."""

from understory import (indieauth,  # , micropub, microsub, webmention, websub
                        web)

# from understory.apps import (cache, data, jobs, owner, providers, search,
#                              sites, system, text_editor, text_reader, tracker)

app = web.application(
    __name__,
    db=True,
    mounts=(
        # owner.app,
        # jobs.app,
        # providers.app,
        # sites.app,
        # search.app,
        # cache.app,
        # data.app,
        # system.app,
        # tracker.app,
        # indieauth.server.app,
        indieauth.client.app,
        # micropub.server.posts.app,
        # micropub.server.media.app,
        # micropub.server.content.app,
        # text_editor.app,
        # webmention.app,
        # websub.app,
        # microsub.server.app,
        # text_reader.app,
    ),
)


# def template(handler, app):
#     """Wrap response with site-wide template."""
#     yield
#     if web.tx.response.headers.content_type == "text/html" and web.tx.response.claimed:
#         if not isinstance(web.tx.response.body, str):
#             web.tx.response.body = app.view.template(web.tx.response.body)
#
#
# def doctype_html(handler, app):
#     """Add the HTML doctype to the response."""
#     yield
#     if web.tx.response.headers.content_type == "text/html" and web.tx.response.claimed:
#         web.tx.response.body = "<!doctype html>" + str(web.tx.response.body)
#
#
# app.wrappers.insert(0, template)
# app.wrappers.append(doctype_html)


@app.control("")
class Home:
    def get(self):
        return "home"


# XXX @app.control("sign-in")  # TODO MOVE TO `OWNER`
# XXX class SignIn:
# XXX     """Sign in as owner or guest."""
# XXX
# XXX     def get(self):
# XXX         """Show sign-in page."""
# XXX         return_url = web.form(return_url="").return_url
# XXX         return app.view.sign_in(return_url)
