"""Microsub clients (readers)."""

from understory import web

__all__ = ["app"]

app = web.application("MicrosubReaders", mount_prefix="readers")
templates = web.templates(__name__)


@app.route(r"text")
class TextReader:
    """A text reader for notes and articles."""

    def get(self):
        """Render the editor."""
        return templates.text()


@app.route(r"image")
class ImageReader:
    """An image reader for photos and graphics."""

    def get(self):
        """Render the editor."""
        return templates.image()
