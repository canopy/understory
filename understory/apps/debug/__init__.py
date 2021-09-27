""""""

from understory import web
from understory.web import tx

app = web.application(__name__, prefix="debug")


@app.control(r"")
class Debug:
    """Render information about the application structure."""

    def get(self):
        return app.view.index(tx.app)
