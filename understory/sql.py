"""
An opinionated Pythonic SQLite interface.

SQLite is a relational database management system contained in a C
programming library. In contrast to many other database management
systems, SQLite is not a client–server database engine. Rather, it
is embedded into the end program.

"""

# TODO when a new table is created, ask to import from table no longer in use
#      -- deprecate no longer used tables if no longer needed

import contextlib
import datetime
import functools
import json
import logging
import os
import pathlib

import pendulum

try:
    from pysqlite3 import dbapi2 as sqlite3
except (ImportError, NameError):  # NOTE pysqlite3.dbapi2 raises NameError
    logging.info("falling back to sqlite3 in the standard library")
    import sqlite3

from understory import solarized

__all__ = ["db"]


# TODO register and handle JSON type


def from_datetime(val):
    if isinstance(val, datetime.datetime):
        return pendulum.instance(val)
    val = val.decode("utf-8")
    # remove timezone column
    if val[-6] in "-+":
        val = "".join(val.rpartition(":")[::2])
    return pendulum.parse(val)


sqlite3.register_converter("DATETIME", from_datetime)
sqlite3.register_adapter(pendulum.DateTime, lambda val: val.isoformat(" "))


def from_json(val):
    # TODO traverse looking for nested published/updated
    def f(dct):
        def upgrade_date(key):
            if key not in dct:
                return
            item = dct[key]
            if not item[0]:
                return
            tz = None
            if isinstance(item[0], dict):
                val = item[0]["datetime"]
                tz = item[0]["timezone"]
            elif isinstance(item, list):
                val = item[0]
            else:
                val = item
            if val[-6] in "-+":
                val = "".join(val.rpartition(":")[::2])
            try:
                dt = pendulum.parse(val.strip())
            except pendulum.exceptions.ParserError:
                dt = "?"
            else:
                if tz:
                    dt = dt.astimezone(pendulum.timezone(tz))
            dct[key] = [dt]

        upgrade_date("published")
        upgrade_date("updated")
        return dct

    return json.loads(val, object_hook=f)


class Model:
    def __init__(self, name, **schemas):
        self.name = name
        self.schemas = schemas
        self.version = 0
        self.migrations = {}
        self.controllers = {}

    def migrate(self, version):
        if version > self.version:
            self.version = version

        def add_migration(f):
            self.migrations[version] = f
            return f

        return add_migration

    def control(self, controller):
        self.controllers[controller.__name__] = controller
        return controller

    def __call__(self, db):
        return ModelController(self.controllers, db)


class ModelController:
    def __init__(self, controllers, db):
        self.controllers = controllers
        self.db = db

    def __getattr__(self, attr):
        return functools.partial(self.controllers[attr], self.db)


model = Model


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


sqlite3.register_converter("JSON", from_json)
sqlite3.register_adapter(dict, lambda val: JSONEncoder(indent=2).encode(val))


def ors(item, values, fuzzy=False):
    template = "{} LIKE '{}%'" if fuzzy else "{} = '{}'"
    return " OR ".join(template.format(item, v) for v in values)


def adapt(x):
    return x


def get_icu():
    current_dir = pathlib.Path(__file__).parent
    icuext_path = current_dir / "libsqliteicu.so"
    if not icuext_path.exists():
        icuext_source_path = current_dir / "icu.c"
        os.system(
            f"gcc -fPIC -shared {icuext_source_path} "
            f"`pkg-config --libs icu-i18n` -o {icuext_path}"
        )
    return icuext_path


class Database:
    """"""

    IntegrityError = sqlite3.IntegrityError
    OperationalError = sqlite3.OperationalError
    ProgrammingError = sqlite3.ProgrammingError

    def __init__(self, path):
        self.path = path
        for command in (
            "pragma",
            "create",
            "rename_table",
            "drop",
            "insert",
            "replace",
            "select",
            "update",
            "delete",
            "columns",
            "add_column",
            "drop_column",
            "rename_column",
        ):

            def single_statement_cursor(command):
                @functools.wraps(getattr(Cursor, command))
                def proxy(_self, *args, **kwargs):
                    with self.transaction as cur:
                        return getattr(cur, command)(_self, *args, **kwargs)

                return proxy

            setattr(self, command, single_statement_cursor(command))

        conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
        # TODO conn.cursor().execute("PRAGMA foreign_keys = ON;")
        try:
            conn.enable_load_extension(True)
        except AttributeError:
            pass
        else:
            icuext_path = get_icu()
            try:
                conn.load_extension(str(icuext_path))
            except sqlite3.OperationalError:
                pass  # TODO make ICU available for all platforms
            else:
                conn.enable_load_extension(False)
                conn.execute("SELECT icu_load_collation('en_US', 'UNICODE');")
        conn.row_factory = sqlite3.Row
        # conn.execute("PRAGMA user_version")
        self.conn = conn

        self.debug = False

    def __repr__(self):
        return f"sql.db: {self.path}"

    # XXX def define(self, table, **schema):
    # XXX     """define multiple tables at once migrating them if necessary"""
    # XXX     # TODO bump version a la "PRAGMA user_version = 1;" and store change
    # XXX     # TODO store backups
    # XXX     try:
    # XXX         self.create(
    # XXX             table,
    # XXX             ", ".join(
    # XXX             f"{row} {definition}" for row, definition in list(schema.items())
    # XXX             ),
    # XXX         )
    # XXX     except self.OperationalError:
    # XXX         pass
    # XXX     # while table_schemas:
    # XXX     #     for table, schema in list(table_schemas.items()):
    # XXX     #         print(table)
    # XXX     #         import textwrap
    # XXX     #         print(textwrap.dedent(schema))
    # XXX     #         table_schemas.pop(table)
    # XXX     #         new_table = "new_{}".format(table)
    # XXX     #         self.create(table, schema)
    # XXX     #         self.create(new_table, schema)
    # XXX     #         with self.transaction as cur:
    # XXX     #             old_columns = cur.columns(table)
    # XXX     #             new_columns = cur.columns(new_table)
    # XXX     #             if old_columns == new_columns:
    # XXX     #                 cur.drop(new_table)
    # XXX     #                 continue
    # XXX     #             old_names = {col[0] for col in old_columns}
    # XXX     #             new_names = {col[0] for col in new_columns}
    # XXX     #             cols = list(old_names.intersection(new_names))
    # XXX     #             print("Migrating table `{}`..".format(table), end=" ")
    # XXX     #             for row in cur.select(table, what=", ".join(cols)):
    # XXX     #                 cur.insert(new_table, dict(zip(cols, list(row))))
    # XXX     #             cur.drop(table)
    # XXX     #             cur.cur.execute(f"""ALTER TABLE {new_table}
    # XXX     #                                 RENAME TO {table}""")
    # XXX     #         print("success")

    @property
    def tables(self):
        return [
            r[0]
            for r in self.select("sqlite_master", what="name", where="type='table'")
        ]

    @property
    @contextlib.contextmanager
    def transaction(self):
        """
        enter a transaction context and return its `Cursor`

            >>> with Database().transaction as cur:  # doctest: +SKIP
            ...    cur.insert(...)
            ...    cur.insert(...)
            ...    cur.select(...)
            ...    cur.insert(...)

        """
        # TODO log transaction begin, complete, etc..
        with self.conn:
            cursor = Cursor(self.conn.cursor())
            cursor.debug = self.debug
            yield cursor
        # with sqlite3.connect(self.path,
        #                      detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        #     # conn.cursor().execute("PRAGMA foreign_keys = ON;")
        #     conn.enable_load_extension(True)
        #     icuext_path = pathlib.Path(__file__).parent / "libsqliteicu"
        #     conn.load_extension(str(icuext_path))
        #     conn.enable_load_extension(False)
        #     conn.execute("SELECT icu_load_collation('en_US', 'UNICODE');")
        #     conn.row_factory = sqlite3.Row
        #     cursor = Cursor(conn.cursor())
        #     cursor.debug = self.debug
        #     yield cursor

    def destroy(self):
        pathlib.Path(self.path).unlink()


def db(path, *models) -> Database:
    """
    return a connection to a `SQLite` database

    Database supplied by given `path` or in environment variable `$SQLDB`.

    Note: `table_schemas` should not include a table (dict key) named "path".

    """
    # XXX if not path:
    # XXX     path = os.environ.get("SQLDB", None)
    # XXX if path:

    dbi = Database(path)
    current_models = {}
    try:
        dbi.create("_models", "name TEXT, version INTEGER")
    except dbi.OperationalError:
        for model in dbi.select("_models"):
            current_models[model["name"]] = model["version"]
    for model in models:
        try:
            current_version = current_models[model.name]
        except KeyError:  # doesn't exist, create all tables in model
            for table, schema in model.schemas.items():
                fts = schema.get("FTS", False)
                if fts:
                    dbi.create(
                        table,
                        ", ".join(f"{col}" for col in schema),
                        fts=True,
                    )
                else:
                    dbi.create(
                        table,
                        ", ".join(
                            f"{col} {definition}" for col, definition in schema.items()
                        ),
                        fts=False,
                    )
            dbi.insert("_models", name=model.name, version=model.version)
            current_models[model.name] = model.version
            continue
        if current_version == model.version:
            # TODO check schema in code against schema in db, suggest migration
            continue  # model exists and is up-to-date
        elif current_version > model.version:
            raise Exception("Your database version is ahead of your software version.")
        elif current_version < model.version:
            for migration in range(current_version + 1, model.version + 1):
                model.migrations[migration](dbi)
            dbi.update(
                "_models", where="name = ?", vals=[model.name], version=model.version
            )
    return dbi


class Cursor:

    """"""

    IntegrityError = sqlite3.IntegrityError
    OperationalError = sqlite3.OperationalError

    def __init__(self, cur):
        self.cur = cur
        self.debug = False

    def pragma(self, command, value=None):
        if value is None:
            self.cur.execute(f"PRAGMA {command}")
            return self.cur.fetchone()[command]
        self.cur.execute(f"PRAGMA {command} = {value}")

    def create(self, table, schema, fts=False):
        """
        create a table with given column schema

        """
        if fts:
            sql = f"CREATE VIRTUAL TABLE {table} USING fts5 ({schema})"
        else:
            sql = f"CREATE TABLE {table} ({schema})"
        self.cur.execute(sql)

    def rename_table(self, table, new_table):
        """Rename a table."""
        self.cur.execute(f"ALTER TABLE {table} RENAME TO {new_table}")

    def drop(self, *tables):
        """
        drop one or more tables

        """
        for table in tables:
            self.cur.execute(f"DROP TABLE {table}")

    def insert(self, table, *records, _force=False, **record):
        return self._insert("insert", table, *records, _force=False, **record)

    def replace(self, table, *records, _force=False, **record):
        return self._insert("replace", table, *records, _force=False, **record)

    def _insert(self, operation, table, *records, _force=False, **record):
        """Insert one or more records into given table."""
        if record:
            if records:
                raise TypeError("use `record` *or* `records` not both")
            records = (record,)  # XXX += (record,)
        values = []
        for record in records:
            for column, val in record.items():
                if isinstance(val, dict):
                    record[column] = JSONEncoder().encode(val)
            columns, vals = zip(*record.items())
            values.append(vals)
        sql = "{} INTO {}({})".format(
            operation.upper(), table, ", ".join(columns)
        ) + " VALUES ({})".format(", ".join("?" * len(vals)))
        if self.debug:
            print(sql)
        try:
            if len(values) == 1:
                self.cur.execute(sql, vals)
                self.cur.execute("SELECT last_insert_rowid()")
                return self.cur.fetchone()[0]
            else:
                self.cur.executemany(sql, values)
        except sqlite3.IntegrityError as err:
            if not _force:
                raise err

    def select(
        self,
        table,
        what="*",
        where=None,
        order=None,
        group=None,
        join=None,
        limit=None,
        offset=None,
        vals=None,
    ):
        """
        select records from one or more tables

        """
        sql = self._select_sql(
            table,
            what=what,
            where=where,
            order=order,
            group=group,
            join=join,
            limit=limit,
            offset=offset,
            vals=vals,
        )[1:-1]
        if self.debug:
            print(sql)
            if vals:
                print(" ", vals)
        if vals:
            self.cur.execute(sql, vals)
        else:
            self.cur.execute(sql)

        class Results:
            def __init__(innerself, results):
                innerself.results = list(results)

            def pop(innerself, index):
                return innerself.results.pop(index)

            def __getitem__(innerself, index):
                return innerself.results[index]

            def __len__(innerself):
                return len(innerself.results)

            def _repr_html_(innerself):
                results = "<tr>"
                types = {}
                for column in self.columns(table):
                    types[column[0]] = column[1]
                    results += f"<td>{column[0]} " f"<small>{column[1]}</small></td>"
                results += "</tr>"
                for result in innerself.results:
                    results += "<tr>"
                    for key, value in dict(result).items():
                        if types[key] == "JSON":
                            encoded_json = JSONEncoder(indent=2).encode(value)
                            value = solarized.highlight(encoded_json, ".json")
                        results += f"<td>{value}</td>"
                    results += "</tr>"
                return f"<table>{results}</table>"

        return Results(self.cur.fetchall())

    def _select_sql(
        self,
        table,
        what="*",
        where=None,
        order=None,
        group=None,
        join=None,
        limit=None,
        offset=None,
        vals=None,
        suffix="",
    ):
        sql_parts = ["SELECT {}".format(what), "FROM {}".format(table)]
        if join:
            if not isinstance(join, (list, tuple)):
                join = [join]
            for join_statement in join:
                sql_parts.append("LEFT JOIN {}".format(join_statement))
        if where:
            # if vals:
            #     where = where.format(*[str(adapt(v)) for v in vals])
            sql_parts.append("WHERE {}".format(where))
        if group:
            sql_parts.append("GROUP BY {}".format(group))
        if order:
            sql_parts.append("ORDER BY {}".format(order))
        if limit:
            limitsql = "LIMIT {}".format(limit)
            if offset:
                limitsql += " {}".format(offset)
            sql_parts.append(limitsql)
        return "({}) {}".format("\n".join(sql_parts), suffix).rstrip()

    def update(self, table, what=None, where=None, vals=None, **record):
        """
        update one or more records

        Use `what` *or* `record`.

        """
        sql_parts = ["UPDATE {}".format(table)]
        if what:
            what_sql = what
        else:
            keys, values = zip(*record.items())
            what_sql = ", ".join("{}=?".format(key) for key in keys)
            if vals is None:
                vals = []
            vals = list(values) + vals
        sql_parts.append("SET {}".format(what_sql))
        if where:
            sql_parts.append("WHERE {}".format(where))
        sql = "\n".join(sql_parts)
        if self.debug:
            print(sql)
            if vals:
                print(vals)
        if vals:
            self.cur.execute(sql, vals)
        else:
            self.cur.execute(sql)

    def delete(self, table, where=None, vals=None):
        """
        delete one or more records

        """
        sql_parts = ["DELETE FROM {}".format(table)]
        if where:
            sql_parts.append("WHERE {}".format(where))
        sql = "\n".join(sql_parts)
        if vals:
            self.cur.execute(sql, vals)
        else:
            self.cur.execute(sql)

    def columns(self, table):
        """Return columns for given table."""
        return [
            list(column)[1:]
            for column in self.cur.execute("PRAGMA table_info({})".format(table))
        ]

    def add_column(self, table, column_def):
        """Add a column to given table."""
        self.cur.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")

    def drop_column(self, table, column):
        """Add a column to given table."""
        self.cur.execute(f"ALTER TABLE {table} DROP COLUMN {column}")

    def rename_column(self, table, column, new_column):
        """Rename a column of given table."""
        self.cur.execute(f"ALTER TABLE {table} RENAME COLUMN {column} TO {new_column}")
