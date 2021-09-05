"""Microsub clients (readers)."""

from understory import web

app = web.application(__name__, prefix="readers")


@app.control(r"text")
class TextReader:
    """A text reader for notes and articles."""

    def get(self):
        """Render the editor."""
        return app.view.text()


@app.control(r"image")
class ImageReader:
    """An image reader for photos and graphics."""

    def get(self):
        """Render the editor."""
        return app.view.image()
