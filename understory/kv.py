"""
An opinionated Redis interface.

Redis is an open-source, networked, in-memory, key-value data store with
optional durability. This module provides an interface to a database that
maps Redis keys' data structures to their Python equivalents.

    # >>> db = Database("/tmp/kv-test", {"foo": "list"})
    # >>> db["foo"] = ["bar", "bat", "baz"]
    # >>> "bar" in db["foo"]
    # True
    # >>> len(db["foo"])
    # 3

"""

# TODO Bytes in addition to String

# XXX import contextlib
import re
import time
import typing

import redis
import sh

__all__ = ["db", "Database"]


class ConnectionError(Exception):
    """Error connecting to database."""


Number = typing.TypeVar("Number", int, float)


class Database:
    """A Redis database interface."""

    def __init__(self, location=None, schema=None, delimiter=":"):
        """Return a Database instance."""
        try:
            host, port = location.split(":")
            port = int(port)
        except (AttributeError, ValueError):
            if location:
                host = location
            else:
                host = "localhost"
            port = 6379
        self.host = host
        self.port = port
        self.db = redis.StrictRedis(host, port)
        self.pubsub = self.db.pubsub
        # self.db = redis.StrictRedis(unix_socket_path=location)
        self.partition = None
        if schema is None:
            schema = {}
        self.schema = schema
        self.delimiter = delimiter

    def define(self, *schemas):
        d = self.delimiter
        for schema in schemas:
            for key, key_type in schema.items():
                key_template = d.join(
                    ([self.partition] if self.partition else []) + [key]
                )
                nskey = key_template.format(**self.patterns).rstrip(d)
                self.schema.update({nskey: key_type})

    @property
    def cursor(self):
        cur = Cursor(self.schema, self.db, self.delimiter)
        cur.db_prefix = self.partition
        return cur

    @property
    def keys(self):
        return self.cursor.keys()

    def type(self, key):
        return self.cursor.type(key)

    def get_value(self, key):
        class_name = self.db.type(key).decode("utf-8").capitalize()
        return globals()[class_name](self.db, key)

    def intersection(self, *sets):
        keys = []
        for set in sets:
            key, key_type = self.cursor._gen_key(set)
            if key_type != "set":
                raise TypeError("intersection may only be applied to sets")
            keys.append(key)
        # XXX ??? return map(int, self.cursor.db.sinter(*keys))
        return [v.decode("utf-8") for v in self.cursor.db.sinter(*keys)]

    def __getitem__(self, key):
        return self.cursor[key]

    def __setitem__(self, key, value):
        self.cursor[key] = value

    def __delitem__(self, key):
        del self.cursor[key]

    def __contains__(self, key):
        return key in self.cursor


def db(
    prefix: str = None, delimiter=":", *schemas, socket=None, **patterns
) -> Database:
    """
    Return a connection to a `redis` database.

    Socket specified by given `socket` or in environment variable `$KVDB`.

    Note: `schema` should not include a key named "socket".

    """
    # if socket is None:
    #     socket = os.environ.get("KVDB", None)
    # if not socket:
    #     raise ConnectionError("error connecting to Redis using "
    #                           "file socket at `{}`".format(socket))
    # if socket is None:
    #     return  # TODO raise exception
    db = Database(delimiter=delimiter)
    patterns = {k: r"(?P<{}>{})".format(k, v) for k, v in patterns.items()}
    db.partition = prefix
    db.patterns = patterns
    db.define(*schemas)
    return db


class Cursor:
    """Redis database interface."""

    # >>> db = Database(".")
    # >>> db.set("foo", "bar")
    # >>> db.get("foo")
    # "bar"
    # >>> db["fnord1337"] = "abba-zaba"
    # >>> db[db("fnord", 1337)]
    # "abba-zaba"
    # >>> with db.namespace("a", "b", "c", 1, 2, 3):
    # ...     db["ZZZ"] = "zzz"
    # >>> db["a/b/c/1/2/3/ZZZ"]
    # "zzz"
    # >>> db.format("test")
    # "example/test"

    db_prefix = None
    prefix = None
    scope = None

    def __init__(self, schema, db, delimiter=":"):
        self.__dict__.update(schema=schema, db=db, args={}, delimiter=delimiter)

    def flushall(self):
        """Remove all keys from all databases."""
        self.db.flushall()

    def flushdb(self):
        """Remove all keys from the current database."""
        self.db.flushdb()

    def keys(self):
        """"""
        return [
            k[len(self.db_prefix) + 1 :].decode()
            for k in self.db.keys()
            if k.startswith(self.db_prefix.encode("utf-8"))
        ]

    def random_key(self):
        """"""
        return self.db.randomkey()

    def type(self, key):
        return self._gen_key(key)[1]

    def transaction(self, handler, *args):
        """"""

        def wrapped_handler(pipe):
            return handler(Pipe(self.schema, pipe))

        # FIXME _get has since changed
        wrapped_args = [self._get(arg) for arg in args]
        return self.db.transaction(wrapped_handler, *wrapped_args)

    # XXX @contextlib.contextmanager
    # XXX def namespace(self, *namespaces):
    # XXX     """"""
    # XXX     scope = self.scope
    # XXX     if scope:
    # XXX         namespaces = (scope,) + namespaces
    # XXX     self.scope = self._delimit(*namespaces)
    # XXX     yield
    # XXX     self.scope = scope

    # @property
    # def db(self):
    #     """[re]establish a connection instance"""
    #     # TODO utilize os.environ
    #     if "_db" not in self.__dict__:
    #         self._db = redis.Redis()
    #     return self._db

    def _delimit(self, *namespaces):
        """return a delimited namespace"""
        return self.delimiter.join(map(str, namespaces))

    def _get(self, template):
        key, key_type = self._gen_key(template)
        return globals()[key_type.lower().capitalize()](self.db, key)

    def _gen_key(self, template):
        parts = [
            p
            for p in ([self.db_prefix] if self.db_prefix else [])
            + [self.prefix, self.scope]
            if p
        ]
        if isinstance(template, (list, tuple)):
            template = self._delimit(*template)
        for key_template, key_type in self.schema.items():
            key = self._delimit(*(parts + [template]))
            match = re.match("^" + key_template + "$", key)
            if match:
                break
        else:
            raise KeyError("unknown schema for `{}`".format(template))
        return key, key_type

    def __getitem__(self, key_template):
        return self._get(key_template)

    def __setitem__(self, key_template, value):
        self._get(key_template)._set(value)

    def __delitem__(self, key_template):
        key = self._gen_key(key_template)[0]
        self.db.delete(key)

    def __contains__(self, key_template):
        try:
            key = self._gen_key(key_template)[0]
        except KeyError:
            key = key_template
        return self.db.exists(key)

    def __getattr__(self, name):
        try:
            return self.args[name]
        except KeyError as err:
            raise AttributeError(err)

    def __setattr__(self, name, value):
        if name in ("db_prefix", "prefix", "scope", "delimiter"):
            self.__dict__[name] = value
        self.args[name] = value

    __call__ = _delimit


class Pipe(Cursor):
    def multi(self):
        return self.db.multi()


class Key:
    """"""

    def __init__(self, db, key, value=None):
        self.db = db
        self.key = key
        if value:
            self._set(value)

    # TODO dump, migrate, pexpire, pexpireat, restore

    def delete(self):
        """delete a key"""
        return self.db.delete(self.key)

    @property
    def exists(self):
        """determine if a key exists"""
        return self.db.exists(self.key)

    def expire(self, seconds):
        """set a key's time to live in seconds"""
        return self.db.expire(self.key, seconds)

    def expireat(self, key, timestamp):
        """set the expiration for a key as a unix timestamp"""

    def keys(self, pattern):
        """find all keys matching the given pattern"""

    def move(self, key, db):
        """move a key to another database"""

    def object(self, subcommand, *arguments):
        """inspect the internals of redis objects"""

    def persist(self, key):
        """remove the expiration from a key"""

    def randomkey(self):
        """return a random key from the keyspace"""

    def rename(self, key, newkey):
        """rename a key"""

    def renamenx(self, key, newkey):
        """rename a key, only if the new key does not exist"""

    # def sort(self, key, ...):
    #     """
    #     key [by pattern] [limit offset count] [get pattern [get
    #     pattern ...]] [asc|desc] [alpha] [store destination] sort
    #     the elements in a list, set or sorted set
    #
    #     """

    def type(self, key):
        """determine the type stored at key"""

    ##########################################################################

    def ttl(self):
        """get the time to live for a key"""
        return self.db.ttl(self.key)

    def pttl(self):
        return self.db.pttl(self.key)

    def __delete__(self):  # XXX ?
        self.delete()


class Hash(Key):
    """A hash abstraction."""

    # TODO hincrbyfloat

    def hdel(self, key, *fields):
        """delete one or more hash fields"""

    def hexists(self, key, field):
        """determine if a hash field exists"""

    def hget(self, field):
        """get the value of a hash field"""
        value = self.db.hget(self.key, field)
        if value is None:
            raise KeyError("no key {}".format(field))
        return value.decode("utf-8")

    def hgetbytes(self, field):
        """get the value of a hash field"""
        value = self.db.hget(self.key, field)
        if value is None:
            raise KeyError("no key {}".format(field))
        return value

    def hgetall(self):
        """get all the fields and values in a hash"""
        data = {}
        for k, v in self.db.hgetall(self.key).items():
            try:
                k = k.decode("utf-8")
            except UnicodeDecodeError:
                pass
            try:
                v = v.decode("utf-8")
            except UnicodeDecodeError:
                pass
            data[k] = v
        return data

    def hincrby(self, key, field, increment):
        """increment the integer value of a hash field by the given number"""
        return self.db.hincrby(self.format(key), field, increment)

    def hkeys(self, key):
        """get all the fields in a hash"""

    def hlen(self, key):
        """get the number of fields in a hash"""

    def hmget(self, key, *fields):
        """get the values of all the given hash fields"""

    def hset(self, key, value):
        """set the string value of a hash field"""
        return self.db.hset(self.key, key, value)

    def hsetnx(self, key, value):
        """set the value of a hash field, only if the field does not exist"""
        return self.db.hsetnx(self.key, key, value)

    def hvals(self, key):
        """get all the values in a hash"""

    ##########################################################################

    # TODO hmget

    def get(self, item, default=None):
        try:
            return self[item]
        except KeyError:
            return default

    def items(self):
        return self.hgetall().items()

    def keys(self):
        return [k.decode("utf-8") for k in self.db.hkeys(self.key)]

    def values(self):
        return self.db.hvals(self.key)

    def set_once(self, item, value):
        return self.db.hsetnx(self.key, item, value)

    def hmset(self, **items):
        """set multiple hash fields to multiple values"""
        if not len(items):
            self.db.delete(self.key)
            return
        return self.db.hmset(self.key, items)

    update = hmset

    def preview(self):
        return self.items()

    def _set(self, value):
        """"""
        self.hmset(**dict(value))

    def __add__(self, other):
        handlers = {int: self.db.hincrby, float: self.db.hincrbyfloat}
        handlers[type(other)](self.key, other)

    def __contains__(self, name):
        try:
            self.hget(name)
        except KeyError:
            return False
        return True

    def __getitem__(self, name):
        item = self.hget(name)
        if item is None:
            raise KeyError(name)
        return item

    def __setitem__(self, name, value):
        self.db.hset(self.key, name, value)

    def __delitem__(self, name):
        return self.db.hdel(self.key, name)

    # TODO def __contains__(self, name):
    # TODO     return self.exists(name)

    def __len__(self):
        return self.db.hlen(self.key)

    def __str__(self):
        return str(self.hgetall())

    def __repr__(self):
        return '<hash: "{}">'.format(str(self))


class Set(Key):
    """
    A set abstraction.

        >>> # db = Database("/tmp/kv-test", {"foo": "set"})
        >>> # db["src"]["member"] >> db["dst"]
        >>> # fnord = db["foo"] - db["bar"] - db["bat"]
        >>> # db["fnord"] = db["foo"] - db["bar"] - db["bat"]

    """

    def sadd(self, *members):
        """add one or more members to a set"""
        return self.db.sadd(self.key, *members)

    def scard(self, key):
        """get the number of members in a set"""

    def sdiff(self, *keys):
        """subtract multiple sets"""

    def sdiffstore(self, destination, *keys):
        """subtract multiple sets and store the resulting set in a key"""

    def sinter(self, *keys):
        """intersect multiple sets"""
        return self.db.sinter(self.key, *keys)

    def sinterstore(self, destination, *keys):
        """intersect multiple sets and store the resulting set in a key"""

    def sismember(self, key, member):
        """determine if a given value is a member of a set"""

    def smembers(self):
        """get all the members in a set"""
        # return self.db.smembers(self.format(key))
        return {m.decode("utf-8") for m in self.db.smembers(self.key)}

    def smove(self, source, destination, member):
        """move a member from one set to another"""

    def spop(self):
        """remove and return a random member from a set"""
        return self.db.spop(self.key).decode("utf-8")

    def srandmember(self, key):
        """get a random member from a set"""

    def srem(self, *members):
        """remove one or more members from a set"""
        return self.db.srem(self.key, *members)

    def sunion(self, *keys):
        """add multiple sets"""
        return self.db.sunion(self.key, *keys)

    def sunionstore(self, destination, *keys):
        """add multiple sets and store the resulting set in a key"""

    ##########################################################################

    # TODO move, diff[store], inter[store], union[store]

    def add(self, *members):
        """add one or more members"""
        return self.sadd(*members)

    def pop(self, *members):
        """remove and return a random member or given members"""
        if members:
            return self.srem(*members)
        return self.spop()

    def random(self, count=1):
        """get `count` random members"""
        return self.db.srandmember(self.key, count)

    def preview(self):
        return self.smembers()

    def _set(self, value):
        """"""
        self.db.delete(self.key)
        self.add(*list(value))

    def __or__(self, member):
        return self.smembers() | member.smembers()

    def __delitem__(self, member):
        self.db.srem(self.key, member)

    def __iter__(self):
        return iter(self.smembers())

    def __contains__(self, member):
        return self.db.sismember(self.key, member)

    def __len__(self):
        return self.db.scard(self.key)

    def __str__(self):
        return str(self.smembers())


class Zset(Key):
    """A sorted set abstraction."""

    def zadd(self, *args, **kwargs):
        """
        Add one or more members to a sorted set.

        Update its score if it already exists.

        """
        return self.db.zadd(self.key, *args, **kwargs)

    def zcard(self, key):
        """Get the number of members in a sorted set."""

    def zcount(self, key, min, max):
        """
        Count the members in a sorted set with scores within the given values.

        """

    def zincrby(self, key, increment, member):
        """increment the score of a member in a sorted set"""

    # def zinterstore(self):
    #     """
    #     destination numkeys key [key ...] [weights weight [weight ...]]
    #     [aggregate sum|min|max] intersect multiple sorted sets and store
    #     the resulting sorted set in a new key
    #
    #     """

    def zrange(self, start, stop, withscores=True):
        """return a range of members in a sorted set, by index"""
        return self.db.zrange(self.key, start, stop, withscores=withscores)

    def zrangebyscore(self, min, max, withscores=True, limit=None):
        """return a range of members in a sorted set, by score"""
        for item, score in self.db.zrangebyscore(
            self.key, min, max, withscores=withscores
        ):
            yield item.decode("utf-8"), score

    def zrank(self, key, member):
        """determine the index of a member in a sorted set"""

    def zrem(self, *members):
        """remove one or more members from a sorted set"""
        return self.db.zrem(self.key, *members)

    def zremrangebyrank(self, start, stop):
        """remove all members in a sorted set within the given indexes"""
        return self.db.zremrangebyrank(self.key, start, stop)

    def zremrangebyscore(self, key, min, max):
        """remove all members in a sorted set within the given scores"""

    def zrevrange(self, start, stop, withscores=True):
        """return a range of members in a sorted set, by index, with
        scores ordered from high to low"""
        return self.db.zrevrange(self.key, start, stop, withscores=withscores)

    def zrevrangebyscore(self, max, min, withscores=True, limit=None):
        """return a range of members in a sorted set, by score, with
        scores ordered from high to low"""
        return self.db.zrevrangebyscore(
            self.key, max, min, withscores=withscores, limit=limit
        )

    def zrevrank(self, key, member):
        """determine the index of a member in a sorted set, with scores
        ordered from high to low"""

    def zscore(self, member):
        """get the score associated with the given member in a sorted set"""
        return self.db.zscore(self.key, member)

    # def zunionstore(self):
    #     """
    #     destination numkeys key [key ...] [weights weight [weight ...]]
    #     [aggregate sum|min|max] add multiple sorted sets and store the
    #     resulting sorted set in a new key
    #
    #     """

    ##########################################################################

    def add(self, *args, **kwargs):
        return self.zadd(*args, **kwargs)

    def __iter__(self):
        return ((item.decode("utf-8"), score) for item, score in self.zrange(0, -1))

    def keep_popping(self):
        while True:
            try:
                item, score = self.zrange(0, 0)[0]
            except IndexError:
                time.sleep(0.1)
                continue
            yield item.decode("utf-8"), score

    def __setitem__(self, item, score):
        return self.add(score, item)

    def __getitem__(self, item):
        return self.zscore(item)

    def __contains__(self, item):
        if self.zscore(item) is None:
            return False
        return True

    def __str__(self):
        return str(self.zrange(0, -1))


class List(Key):

    """A list abstraction."""

    def blpop(self, timeout, *keys):
        """remove and get the first element in a list, or block until one
        is available"""

    def brpop(self, timeout, *keys):
        """remove and get the last element in a list, or block until one
        is available"""

    def brpoplpush(self, timeout, source, destination):
        """pop a value from a list, push it to another list and return
        it; or block until one is available"""

    def lindex(self, key, index):
        """get an element from a list by its index"""

    def linsert(self, key, position, pivot, value):
        """insert an element before or after another element in a list"""

    def llen(self, key):
        """get the length of a list"""

    def lpop(self):
        """remove and get the first element in a list"""
        return self.db.lpop(self.key)

    def lpush(self, *values):
        """prepend one or multiple values to a list"""
        return self.db.lpush(self.key, *values)

    def lpushx(self, key, value):
        """prepend a value to a list, only if the list exists"""

    def lrange(self, start, stop):
        """get a range of elements from a list"""
        return self.db.lrange(self.key, start, stop)

    def lrem(self, count, value):
        """remove elements from a list"""
        return self.db.lrem(self.key, count, value)

    def lset(self, index, value):
        """set the value of an element in a list by its index"""
        try:
            self.db.lset(self.key, index, value)
        except redis.exceptions.ResponseError:
            self.db.lpush(self.key, value)

    def ltrim(self, start, stop):
        """trim a list to the specified range"""
        return self.db.ltrim(self.key, start, stop)

    def rpop(self, key):
        """remove and get the last element in a list"""

    def rpoplpush(self, source, destination):
        """remove the last element in a list, append it to another list
        and return it"""

    def rpush(self, *values):
        """append one or multiple values to a list"""
        return self.db.rpush(self.key, *values)

    def rpushx(self, key, value):
        """append a value to a list, only if the list exists"""

    ##########################################################################

    def append(self, *values):
        """"""
        return self.rpush(*values)

    extend = append

    def prepend(self, *values):
        """"""
        self.lpush(*values)

    def _set(self, value):
        """"""
        self.db.delete(self.key)
        for item in list(value):
            self.append(item)
        # lval = list(value)
        # for i, item in enumerate(lval):
        #     self[i] = item
        # self.ltrim(0, len(lval) - 1)

    def __getitem__(self, index):
        """"""
        if isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            return (item.decode("utf-8") for item in self.lrange(start, stop)[::step])
        item = self.db.lindex(self.key, index)
        if item is None:
            raise IndexError("list index out of range")
        try:
            return item.decode("utf-8")
        except UnicodeDecodeError:
            return item

    def __setitem__(self, index, value):
        """"""
        return self.lset(index, value)

    def __len__(self):
        """"""
        return self.db.llen(self.key)

    def remove(self, value, count=0):
        """"""
        return self.lrem(count, value)

    def pop(self):
        value = self.db.lpop(self.key)
        if value:
            try:
                value = value.decode()
            except UnicodeDecodeError:
                pass
        return value

    def keep_popping(self, block=True):
        func = self.db.lpop
        if block:
            func = self.db.blpop
        while True:
            value = func(self.key)
            if not value:
                break
            if block:
                value = value[1]
            try:
                final_value = value.decode()
            except UnicodeDecodeError:
                final_value = value
            yield final_value

    # TODO slices and ranges

    def __iter__(self):
        """"""
        return iter(self[i] for i in range(len(self)))

    def __str__(self):
        preview = self.lrange(0, 10)
        if len(self) > 10:
            preview += ["..."]
        return str(preview)


class String(Key):
    """A string abstraction."""

    def append(self, value: str) -> str:
        """
        append a value to a key

        """
        return self.db.append(self.key, value)

    def decr(self, decrement: Number = 1) -> Number:
        """
        decrement the integer value of a key by the given number

        """
        if isinstance(decrement, int):
            retval = self.db.decr(self.key, decrement)
        elif isinstance(decrement, float):
            retval = self.db.incrbyfloat(self.key, -decrement)
        else:
            raise TypeError("decrement value not a Number")
        return type(decrement)(retval)

    def get(self):
        """
        get the value of a key

        """
        # TODO combine get_string() & get_bytes() (using kwarg?)

    def _get_string(self):
        val = self.db.get(self.key)
        if val is None:
            return ""
        return val.decode("utf-8").replace("\r\n", "\n")

    def _get_bytes(self):
        val = self.db.get(self.key)
        if val is None:
            return b""
        return val
        # _bytes = val.decode("utf-8")
        # stripped_bytes = _bytes[2:-1]
        # return bytes(stripped_bytes, "utf-8")

    def incr(self, increment: Number = 1) -> Number:
        """
        increment the integer value of a key by the given number

        """
        if isinstance(increment, int):
            retval = self.db.incr(self.key, increment)
        elif isinstance(increment, float):
            retval = self.db.incrbyfloat(self.key, increment)
        else:
            raise TypeError("increment value not a Number")
        return type(increment)(retval)

    def mget(self, *keys):
        """
        get the values of all the given keys

        """
        return self.db.mget([self.format(key) for key in keys])

    def set(self, value):
        """
        set the string value of a key

        """
        # TODO handle EX, PX, NX, XX optional args
        return self.db.set(self.key, value)

    def _set_bytes(self, value):
        self.set(value)

    def setnx(self, value):
        """
        set the value of a key, only if the key does not exist

        """
        return self.db.setnx(self.key, value)  # XXX format(self.key), value)

    def strlen(self):
        """
        get the length of the value stored in a key

        """
        return self.db.strlen(self.key)

    # ------------------------------------------------------------------

    # TODO bitcount, bitfield, bitop, bitpos, getbit, setbit

    def getrange(self, start, end):
        """
        get a substring of the string stored at a key

        """
        raise NotImplementedError

    def getset(self, value):
        """
        set the string value of a key and return its old value

        """
        raise NotImplementedError

    def mset(self, **pairs):
        """
        set multiple keys to multiple values

        """
        raise NotImplementedError

    def msetnx(self, **pairs):
        """
        set multiple keys to multiple values, only if none of the keys exist

        """
        raise NotImplementedError

    def psetex(self, seconds, value):
        """
        set the value and expiration in milliseconds of a key

        """
        raise NotImplementedError

    def setex(self, seconds, value):
        """
        set the value and expiration of a key

        """
        raise NotImplementedError

    def setrange(self, offset, value):
        """
        overwrite part of a string at key starting at the specified offset

        """
        raise NotImplementedError

    # ------------------------------------------------------------------

    def preview(self):
        val = self.db.get(self.key)
        if val is None:
            return None
        try:
            return val.decode("utf-8").replace("\r\n", "\n")
        except UnicodeDecodeError:
            return val

    def _set(self, value):
        self.set(str(value))

    def __add__(self, other):
        if isinstance(other, str):
            self.append(other)
            return self._get_string()
        elif isinstance(other, (int, float)):
            return self.incr(other)
        raise TypeError("unsupported operand type(s) for +")

    __radd__ = __add__

    def __iadd__(self, other):
        print("iadd", other)
        if isinstance(other, str):
            self.append(other)
            return self._get_string()
        elif isinstance(other, (int, float)):
            return self.incr(other)
        raise TypeError("unsupported operand type(s) for += ")  # TODO

    def __sub__(self, decrement):
        self.decr(decrement)

    def __int__(self):
        return int(self._get_string())

    def __float__(self):
        return float(self._get_string())

    def __str__(self):
        return self._get_string()
        # return self.get_bytes().decode("utf-8")

    def __eq__(self, comparison):
        return self._get_string() == comparison

    def __len__(self):
        return self.strlen()

    def __bool__(self):
        return bool(self.exists)

    def __repr__(self):
        return '<string: "{}">'.format(self._get_string())


class XXX:

    #########################################################################

    # TODO evalsha, script_exists, script_flush, script_kill, script_load

    def eval(self, script, numkeys, **commands):
        """execute a lua script server side"""

    #########################################################################

    def discard(self):
        """discard all commands issued after multi"""

    def execute(self):
        """execute all commands issued after multi"""

    def multi(self):
        """mark the start of a transaction block"""

    def unwatch(self):
        """forget about all watched keys"""

    def watch(self, *keys):
        """watch the given keys to determine execution of the
        multi/exec block"""

    #########################################################################

    def auth(self, password):
        """authenticate to the server"""

    def echo(self, message):
        """echo the given string"""

    def ping(self):
        """ping the server"""

    def quit(self):
        """close the connection"""

    def select(self, index):
        """change the selected database for the current connection"""

    #########################################################################

    def psubscribe(self, *patterns):
        """listen for messages published to channels matching the
        given patterns"""

    def publish(self, channel, message):
        """post a message to a channel"""

    def punsubscribe(self, *patterns):
        """stop listening for messages posted to channels matching the
        given patterns"""

    def subscribe(self, *channels):
        """listen for messages published to the given channels"""

    def unsubscribe(self, *channels):
        """stop listening for messages posted to the given channels"""

    #########################################################################

    # TODO client_kill, client_list, time

    def bgrewriteaof(self):
        """asynchronously rewrite the append-only file"""

    def bgsave(self):
        """asynchronously save the dataset to disk"""

    def config_get(self):
        """get the value of a configuration parameter"""

    def config_set(self):
        """value set a configuration parameter to the given value"""

    def config_reset_stats(self):
        """reset the stats returned by info"""

    def dbsize(self):
        """return the number of keys in the selected database"""

    def debug_object(self):
        """object key get debugging information about a key"""

    def debug_segfault(self):
        """make the server crash"""

    def info(self):
        """get information and statistics about the server"""

    def lastsave(self):
        """get the unix time stamp of the last successful save to disk"""

    def monitor(self):
        """listen for all requests received by the server in real time"""

    def save(self):
        """synchronously save the dataset to disk"""

    def shutdown(self):
        """synchronously save the dataset to disk and then shut down
        the server"""

    def slaveof(self, host, port):
        """make the server a slave of another instance, or promote it
        as master"""

    def slowlog(self, subcommand, argument=None):
        """manages the redis slow queries log"""

    def sync(self):
        """internal command used for replication"""


test_server = None


def setup_module(module):
    global test_server
    test_server = sh.redis_server(
        "--unixsocket", "/tmp/kv-test", "--port", "0", _bg=True
    )
    time.sleep(1)


def teardown_module(module):
    test_server.kill()
