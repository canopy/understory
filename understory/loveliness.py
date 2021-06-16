"""
A background job queue.

Just a bunch of ladybugs doing their thing.

"""

from gevent import monkey

monkey.patch_all()

import importlib
import json
import pathlib
import time
import traceback

import gevent.queue
import pendulum

from understory import kv, sql, term, web
from understory.web import tx

main = term.application("loveliness", "job queue")
queue = gevent.queue.PriorityQueue()
worker_count = 20


def run_scheduler():  # browser):
    """Check all schedules every minute and enqueue any scheduled jobs."""
    while True:
        now = pendulum.now()
        if now.second:
            time.sleep(0.9)
            continue
        # TODO schedule_jobs()
        time.sleep(1)


# def schedule_jobs():  # browser):
#     # TODO support for days of month, days of week
#     # print("checking schedule")
#     # for host in get_hosts():
#     #     tx = canopy.contextualize(host)
#     #     jobs = tx.db.select("job_schedules AS sch",
#     #                         join="""job_signatures AS sig ON
#     #                                 sch.job_signature_id = sig.rowid""")
#     #     for job in jobs:
#     #         run = True
#     #         minute = job["minute"]
#     #         hour = job["hour"]
#     #         month = job["month"]
#     #         if minute[:2] == "*/":
#     #             if now.minute % int(minute[2]) == 0:
#     #                 run = True
#     #             else:
#     #                 run = False
#     #         if hour[:2] == "*/":
#     #             if now.hour % int(hour[2]) == 0 and now.minute == 0:
#     #                 run = True
#     #             else:
#     #                 run = False
#     #         if month[:2] == "*/":
#     #             if now.month % int(month[2]) == 0 and now.hour == 0 \
#     #                and now.minute == 0:
#     #                 run = True
#     #             else:
#     #                 run = False
#     #         if run:
#     #             canopy.enqueue(getattr(importlib.import_module(job["module"]),
#     #                                    job["object"]))
#     # time.sleep(.9)


def handle_job(host, job_run_id, db):  # , browser):
    """Handle a freshly dequeued job."""
    # TODO handle retries
    tx.host.name = host
    tx.host.db = db
    tx.host.cache = web.cache(db=db)
    # tx.browser = browser
    job = tx.db.select(
        "job_runs AS r",
        what="s.rowid, *",
        join="""job_signatures AS s
                                   ON s.rowid = r.job_signature_id""",
        where="r.job_id = ?",
        vals=[job_run_id],
    )[0]
    _module = job["module"]
    _object = job["object"]
    _args = json.loads(job["args"])
    _kwargs = json.loads(job["kwargs"])
    print(
        f"{host}/{_module}:{_object}",
        *(_args + list(f"{k}={v}" for k, v in _kwargs.items())),
        sep="\n  ",
        flush=True,
    )
    tx.db.update(
        "job_runs",
        where="job_id = ?",
        vals=[job_run_id],
        what="started = STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')",
    )
    status = 0
    try:
        output = getattr(importlib.import_module(_module), _object)(*_args, **_kwargs)
    except Exception as err:
        status = 1
        output = str(err)
        traceback.print_exc()
    tx.db.update(
        "job_runs",
        vals=[status, output, job_run_id],
        what="""finished = STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW'),
                             status = ?, output = ?""",
        where="job_id = ?",
    )
    run = tx.db.select("job_runs", where="job_id = ?", vals=[job_run_id])[0]
    st, rt = run["started"] - run["created"], run["finished"] - run["started"]
    tx.db.update(
        "job_runs",
        where="job_id = ?",
        what="start_time = ?, run_time = ?",
        vals=[
            f"{st.seconds}.{st.microseconds}",
            f"{rt.seconds}.{rt.microseconds}",
            job_run_id,
        ],
    )
    print(flush=True)


def serve(db_prefixes):
    """"""
    # TODO gevent.spawn(run_scheduler)  # , sqldbs)  # , browser)

    def run_worker(db_prefix, kv, db):  # browser):
        for job in kv["jobs"].keep_popping():
            handle_job(db_prefix, job, db)  # , browser)

    for db_prefix in db_prefixes:
        kvdb = kv.db(db_prefix, ":", {"jobs": "list"})
        sqldb = sql.db(f"{db_prefix}.db")
        # browser = agent.browser()
        for _ in range(worker_count):
            gevent.spawn(run_worker, db_prefix, kvdb, sqldb)  # , browser)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:  # TODO capture supervisord's kill signal
        # browser.quit()
        pass


@main.register()
class Serve:
    """Serve the job queue."""

    def run(self, stdin, log):
        """Spawn a scheduler and workers and start sending jobs to them."""
        serve(p.stem for p in pathlib.Path().glob("*.db"))


if __name__ == "__main__":
    main()
