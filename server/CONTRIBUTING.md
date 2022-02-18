## Contributing Guide

```shell
git clone https://github.com/canopy/canopy.git && cd canopy
poetry install
WEBCTX=dev poetry run web serve canopy:app --port 9000
# hack
poetry run build_understory  # optional
```
