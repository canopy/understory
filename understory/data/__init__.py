""""""

import pprint

from understory import web
from understory.web import tx

app = web.application(__name__, prefix="data", args={"table": r"\w+", "key": r"\w+"})


@app.control("")
class Data:
    def get(self):
        return app.view.index(sorted(tx.db.tables))


@app.control("export.bar")
class ExportArchive:
    def get(self):
        web.header("Content-Type", "application/bar")
        return "an export archive"


@app.control(r"tables")
class SQLiteTables:
    """Interface to the SQLite database found at `tx.db`."""

    def get(self):
        ...


@app.control(r"tables/{table}")
class SQLiteTable:
    """A table in `tx.db`."""

    def get(self):
        return app.view.sqlite_table(self.table, tx.db.select(self.table))


@app.control(r"kv")
class RedisDatabase:
    """Interface to the Redis database found at `tx.kv`."""

    def get(self):
        return tx.kv.keys


@app.control(r"kv/{key}")
class RedisKey:
    """A key in `tx.kv`."""

    def get(self):
        return app.view.kv_key(tx.kv.type(self.key), tx.kv[self.key])
