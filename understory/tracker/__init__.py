"""
Personal tracker for your personal website.

Track your physical movement: GPS locations and trip circuits (eg. Overland)

Track your web movement: webpage visits (eg. Liana)

"""

from understory import web

app = web.application(
    __name__,
    prefix="tracker",
    args={"start": r".*"},
    model={
        "locations": {"location": "JSON"},
        "trips": {"start": "DATETIME", "distance": "TEXT", "location": "JSON"},
        "web": {"location": "JSON"},
    },
)


@app.wrap
def connect_model(handler, main_app):
    """Connect the model to this transaction's database."""
    web.tx.tracker = app.model(web.tx.db)
    yield


@app.control(r"")
class Tracker:
    """"""

    def get(self):
        """"""
        if not web.tx.user.session:
            raise web.NotFound("nothing to see here.")
        return app.view.physical(
            web.tx.tracker.get_locations(), web.tx.tracker.get_trip_locations()
        )


@app.control(r"physical")
class Physical:
    """"""

    # @app.scope("fitness")
    # @web.scope("mj.com", "ace.com")
    def get(self):
        """"""
        return app.view.physical(
            web.tx.tracker.get_locations(), web.tx.tracker.get_trips()
        )

    def post(self):
        """"""
        for location in web.tx.request.body["locations"]:
            web.tx.tracker.add_location(location)
        if trip := web.tx.request.body.get("trip"):
            web.tx.tracker.add_trip_location(trip)
        return {"result": "ok"}


@app.control(r"physical/trips/{start}")
class Trip:
    """"""

    def get(self):
        """"""
        if not web.tx.user.session:
            raise NotFound("nothing to see here.")
        return app.view.trip(web.tx.tracker.get_trip(self.start))


@app.control(r"web")
class Web:
    """"""

    def get(self):
        """"""
        if not web.tx.user.session:
            raise NotFound("nothing to see here.")
        return app.view.web(web.tx.tracker.get_web_locations())

    def post(self):
        """"""
        web.tx.tracker.add_web_location(web.tx.request.body["location"])
        print("hello")
        return {"result": "ok"}


@app.model.control
def add_location(db, location):
    db.insert("locations", location=location)


@app.model.control
def get_locations(db):
    return db.select("locations")


@app.model.control
def add_trip_location(db, location):
    db.insert(
        "trips",
        start=location["start"],
        distance=location["distance"],
        location=location,
    )


@app.model.control
def get_trips(db):
    return db.select("trips", group="start")


@app.model.control
def get_trip(db, start):
    return db.select(
        "trips",
        where="start = ?",
        vals=[str(start).replace("+00:00", "Z")],
        order="distance ASC",
    )


@app.model.control
def add_web_location(db, location):
    db.insert("web", location=location)


@app.model.control
def get_web_locations(db):
    return db.select("web")
