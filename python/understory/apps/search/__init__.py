""""""

from understory import web
from understory.web import tx

app = web.application(__name__, prefix="search")


@app.control(r"")
class Search:
    """Search locally and globally."""

    def get(self):
        """Return a search box or search results."""
        try:
            query = web.form("q").q
        except web.BadRequest:
            return app.view.search()
        results = tx.cache.search(query)
        return app.view.results(query, results)
