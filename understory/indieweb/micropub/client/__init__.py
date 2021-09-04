"""Micropub clients (editors)."""

from understory import web

__all__ = ["app"]

app = web.application("MicropubEditors", mount_prefix="editors")
templates = web.templates(__name__)


@app.route(r"text")
class TextEditor:
    """A text editor for notes and articles."""

    def get(self):
        """Render the editor."""
        return templates.text()


@app.route(r"image")
class ImageEditor:
    """An image editor for photos and graphics."""

    def get(self):
        """Render the editor."""
        return templates.image()
