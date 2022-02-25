import web
from example import app


def test_example():
    response = app.get("")
    assert response.status == "200 OK"  # TODO web.OK
    assert response.dom.select("p")[0].text == "foo"
