# Understory
Social web framework

## Create a web app

You should use `Poetry`.

```shell
poetry init
poetry add understory
```

Create the following file structure:

```
example
├── __init__.py
├── static
│   └── screen.css
└── templates
    ├── __init__.py
    └── index.html
```

**example/\_\_init\_\_.py**

```python
import web
from understory import indieauth

app = web.application(__name__, mounts=[indieauth.client.app])


@app.control("")
class Landing:
    def get(self):
        return app.view.index(web.tx.user)
```

**example/static/screen.css**

```css
p.greeting { color: #f00; font-size: 5em; }
```

**example/templates/\_\_init\_\_.py**

```python
import random

from understory.indieauth import web_sign_in

__all__ = ["random", "web_sign_in_form"]
```

**example/templates/index.html**

```html
$def with (user, greeting)

$if user.session:
    $ greeting = random.choice(["hello", "hi", "howdy"])
    <p class=greeting>$greeting $user.name ($user.url)</p>
$else:
    $:web_sign_in_form()
```

### Serve it locally

```shell
poetry run web serve example
```

The server will automatically reload on changes to the source code.

### Host it in the cloud

```shell
poetry run web host example
```

## URL parsing

Defaults to safe-mode and raises DangerousURL eagerly. Up-to-date public
suffix and HSTS support.

    >>> url = skutterbug.uri("example.cnpy.gdn/foo/bar?id=38")
    >>> url.host
    'example.cnpy.gdn'
    >>> url.suffix
    'cnpy.gdn'
    >>> url.is_hsts()
    True

## Cache

uses SQLite

    >>> cache = skutterbug.cache()
    >>> cache["indieweb.org/note"].entry["summary"]
    'A note is a post that is typically short unstructured* plain text, written & posted quickly, that has its own permalink page.'
    >>> cache["indieweb.org/note"].entry["summary"]  # served from cache
    'A note is a post that is typically short unstructured* plain text, written & posted quickly, that has its own permalink page.'

### Microformat parsing

Parse `mf2` from `HTML`. Analyze vocabularies for stability/interoperability.

## Browser

uses Firefox via Selenium

    >>> # browser = skutterbug.Firefox()
    >>> # browser.go("en.wikipedia.org/wiki/Pasta")
    >>> # browser.shot("wikipedia-pasta.png")
