""""""

from understory import web
from understory.web import tx

app = web.application(__name__, prefix="jobs", args={"job": r"\w+"})


@app.control(r"")
class Jobs:
    """"""

    def get(self):
        return app.view.jobs(tx.db.select("job_signatures"))
