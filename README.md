# understory
The tools that power the canopy

## Install

    pip install understory

## Usage

### A simple web application

Install [Python Poetry][0] and configure it.

Create a directory for your project and create a module `hello.py` inside:

    from understory import web

    app = web.application("HelloWorld")

    @app.route(r"")
    class SayHey:
        def get(self):
            return "What's up world?"

From inside your project directory:

    poetry init
    poetry add understory
    poetry run web install hello:app hello_app
    poetry run web serve hello_app
    poetry version prerelease
    poetry build
    poetry publish

Host using [Ghost][1].

#### Add support for the IndieWeb

IndieAuth client/server, Micropub client/server, Microsub, WebSub, Webmention

    from understory import indieweb

    app.mount(indieweb.indieauth.server)
    app.mount(indieweb.micropub.server)
    app.mount(indieweb.content)

[0]: https://python-poetry.org
[1]: https://gh.ost.lol
