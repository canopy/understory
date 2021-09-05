"""Micropub clients (editors)."""

from understory import web

app = web.application(__name__, prefix="editors")


@app.control(r"text")
class TextEditor:
    """A text editor for notes and articles."""

    def get(self):
        """Render the editor."""
        return app.view.text()


@app.control(r"image")
class ImageEditor:
    """An image editor for photos and graphics."""

    def get(self):
        """Render the editor."""
        return app.view.image()
