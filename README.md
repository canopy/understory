# understory

Social web framework

## Use

### Get on

Linux |
Windows |
Mac

### Make a simple website

    pip install understory

Create a directory for your website (eg. `mysite/`) and place the following in
the package's `__init__.py` (eg. `mysite/__init__.py`):

```python
from understory import web

app = web.application(__name__)

@app.control("")
class Landing:
    def get(self):
        return "peaches"
```

    web serve mysite

## Develop

```shell
git clone https://github.com/canopy/canopy.git && cd canopy
poetry install
WEBCTX=dev poetry run web serve canopy:app --port 9000
# hack
poetry run build_understory  # optional
```
