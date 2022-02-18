""""""

import importlib

from understory import sql, web
from understory.web import tx

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
app = web.application(
    __name__,
    prefix="jobs",
    args={
        "job_module": r"[\w.]+",
        "job_object": r"\w+",
        "job_arghash": r"\w+",
        "job_run_id": r"\!+",
    },
    model=model.schemas,
)


@app.control(r"")
class Jobs:
    """"""

    def get(self):
        active = tx.db.select(
            "job_runs AS jr",
            join="job_signatures AS js ON js.rowid = jr.job_signature_id",
            where="started IS NOT NULL AND finished IS NULL",
        )
        finished = tx.db.select(
            "job_runs AS jr",
            join="job_signatures AS js ON js.rowid = jr.job_signature_id",
            where="finished IS NOT NULL",
            order="finished DESC",
            limit=20,
        )
        return app.view.index(active, finished)


@app.control(r"schedules")
class Schedules:
    """"""

    def get(self):
        schedules = tx.db.select(
            "job_schedules AS sc",
            join="job_signatures AS si ON si.rowid = sc.job_signature_id",
        )
        return app.view.schedules(schedules)


@app.control(r"{job_module}")
class ByModule:
    """"""

    def get(self):
        jobs = tx.db.select(
            "job_signatures",
            what="rowid AS id, *",
            where="module = ?",
            vals=[self.job_module],
        )
        return app.view.by_module(self.job_module, jobs)


@app.control(r"{job_module}/{job_object}")
class ByObject:
    """"""

    def get(self):
        callable = getattr(importlib.import_module(self.job_module), self.job_object)
        jobs = tx.db.select(
            "job_signatures",
            what="rowid AS id, *",
            where="module = ? AND object = ?",
            vals=[self.job_module, self.job_object],
        )
        return app.view.by_object(self.job_module, self.job_object, callable, jobs)


@app.control(r"{job_module}/{job_object}/{job_arghash}")
class Job:
    """"""

    def get(self):
        callable = getattr(importlib.import_module(self.job_module), self.job_object)
        job = tx.db.select(
            "job_signatures",
            what="rowid AS id, *",
            where="module = ? AND object = ? AND arghash LIKE ?",
            vals=[self.job_module, self.job_object, self.job_arghash + "%"],
        )[0]
        runs = tx.db.select(
            "job_runs",
            where="job_signature_id = ?",
            vals=[job["id"]],
            order="finished DESC",
            limit=100,
        )
        total = tx.db.select(
            "job_runs",
            what="count(*) AS count",
            where="job_signature_id = ?",
            vals=[job["id"]],
            order="finished DESC",
        )[0]["count"]
        return app.view.job(
            self.job_module, self.job_object, callable, job, runs, total
        )


@app.control(r"{job_module}/{job_object}/{job_arghash}/{job_run_id}")
class JobRun:
    """"""

    def get(self):
        callable = getattr(importlib.import_module(self.job_module), self.job_object)
        job = tx.db.select(
            "job_signatures",
            what="rowid AS id, *",
            where="module = ? AND object = ? AND arghash LIKE ?",
            vals=[self.job_module, self.job_object, self.job_arghash + "%"],
        )[0]
        run = tx.db.select(
            "job_runs",
            what="rowid, *",
            where="job_id = ?",
            vals=[self.job_run_id],
            order="finished DESC",
        )[0]
        return app.view.run(self.job_module, self.job_object, callable, job, run)
