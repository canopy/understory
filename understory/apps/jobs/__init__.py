""""""

from understory import sql, web
from understory.web import tx

app = web.application(__name__, prefix="jobs", args={"job": r"\w+"})
model = sql.model(
    __name__,
    job_signatures={
        "module": "TEXT",
        "object": "TEXT",
        "args": "BLOB",
        "kwargs": "BLOB",
        "arghash": "TEXT",
        "unique": ("module", "object", "arghash"),
    },
    job_runs={
        "job_signature_id": "INTEGER",
        "job_id": "TEXT UNIQUE",
        "created": "DATETIME NOT NULL DEFAULT(STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW'))",
        "started": "DATETIME",
        "finished": "DATETIME",
        "start_time": "REAL",
        "run_time": "REAL",
        "status": "INTEGER",
        "output": "TEXT",
    },
    job_schedules={
        "job_signature_id": "INTEGER",
        "minute": "TEXT",
        "hour": "TEXT",
        "day_of_month": "TEXT",
        "month": "TEXT",
        "day_of_week": "TEXT",
        "unique": (
            "job_signature_id",
            "minute",
            "hour",
            "day_of_month",
            "month",
            "day_of_week",
        ),
    },
)


@app.control(r"")
class Jobs:
    """"""

    def get(self):
        return app.view.jobs(tx.db.select("job_signatures"))
