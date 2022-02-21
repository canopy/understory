## web
Tools for metamodern web development

```python
import web
```

## Applications

```python
app = web.application(
    __name__,
    prefix="events",
    model={"attendees": {"event_id": "INTEGER", "name": "TEXT"}}
)
```

### Models

### Views

#### Templating

Full Python inside string templates.

```pycon
>>> str(web.template("$def with (name)\n$name")("Alice"))
'Alice'
```

##### Markdown

Strict syntax subset (there should be one and only one way).

Supports picoformats: @person, @@org, #tag, %license

```pycon
>>> str(web.mkdn("*lorem* ipsum."))
'<p><em>lorem</em> ipsum. </p>'
```

### Controllers

```python
@app.control("{event_id}/attendees")
class EventAttendees:
    def get(self):
        return app.view.attendees(app.model.get_attendees(self.event_id))

@app.model.control
def get_attendees(db, event_id):
    return db.select("attendees", where="event_id = ?", vals=[event_id])
```

## Mounting

import events

app = web.application(__name__, mounts=[events.app])
