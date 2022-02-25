""""""

import pprint

import web

app = web.application(__name__, prefix="data", args={"table": r"\w+", "key": r"\w+"})


@app.control("")
class Data:
    def get(self):
        return app.view.index(sorted(web.tx.db.tables))


@app.control("tables")
class SQLiteTables:
    """Interface to the SQLite database found at `web.tx.db`."""

    def get(self):
        ...


@app.control("tables/{table}")
class SQLiteTable:
    """A table in `web.tx.db`."""

    def get(self):
        return app.view.sqlite_table(self.table, web.tx.db.select(self.table))


@app.control("export.bar")
class ExportArchive:
    def get(self):
        web.header("Content-Type", "application/bar")
        return "an export archive"


# @app.control(r"kv")
# class RedisDatabase:
#     """Interface to the Redis database found at `web.tx.kv`."""
#
#     def get(self):
#         return web.tx.kv.keys


# @app.control(r"kv/{key}")
# class RedisKey:
#     """A key in `web.tx.kv`."""
#
#     def get(self):
#         return app.view.kv_key(web.tx.kv.type(self.key), web.tx.kv[self.key])
