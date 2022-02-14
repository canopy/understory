# understory

Social web scaffolding

## Spawn a personal website in one-click

Linux | Windows | Mac

## Use the library to build a website

```shell
    pip install understory
```

### Create the following files

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
from understory import web, indieauth

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
    $ greeting = random.choice(("hello", "hi", "howdy"))
    <p class=greeting>$greeting $user.name ($user.url)</p>
$else:
    $:web_sign_in_form()
```

### Develop

```shell
    web serve example
```

### Publish

```shell
    web host create example
```
