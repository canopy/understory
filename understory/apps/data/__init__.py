""""""

import pprint

from understory import web
from understory.web import tx

app = web.application(__name__, prefix="data", args={"table": r"\w+", "key": r"\w+"})


@app.control(r"sql")
class SQLiteDatabase:
    """Interface to the SQLite database found at `tx.db`."""

    def get(self):
        return tx.db.tables


@app.control(r"sql/{table}")
class SQLiteTable:
    """A table in `tx.db`."""

    def get(self):
        rows = pprint.pformat([dict(r) for r in tx.db.select(self.table)])
        web.header("Content-Type", "text/html")
        return f"<pre>{rows}</pre>"


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
