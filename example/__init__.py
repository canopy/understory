import web

app = web.application(__name__)


@app.control("")
class Main:
    def get(self):
        return app.view.index()
