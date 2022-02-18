"""A Microsub reader."""

from understory import web

app = web.application(__name__, prefix="reader")


@app.control(r"")
class TextReader:
    """A reader supporting notes and articles."""

    def get(self):
        """Render the timeline."""
        return app.view.timeline()
