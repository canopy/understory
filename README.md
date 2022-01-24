# understory

Social web framework

## Use

### A simple website

    pip install understory

Create a directory for your website (eg. `mysite/`) and place the following in
the package's `__init__.py` (eg. `mysite/__init__.py`):

```python
from understory import web

app = web.application(__name__)

@app.route("")
class Landing:
    def get(self):
        return "peaches"
```

    web serve mysite
