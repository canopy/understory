"""
Web tests.

- Micropub server

"""

from gevent import monkey

monkey.patch_all()

import functools
import pathlib
import textwrap

import pytest
import requests
from selenium import webdriver
from understory import indieweb, kv, sql, web  # type: ignore
from understory.web import tx
from webdriver_manager.firefox import GeckoDriverManager

characters = {"Alice": {}, "Bob": {}}  # XXX , "Carol": {}, "Dan": {}}
tests_dir = pathlib.Path(__file__).parent
docs_dir = tests_dir.parent / "docs"
scenes = []


def setup_module(module):
    """Clean up previous run."""
    pathlib.Path("test-alice.db").unlink(missing_ok=True)
    pathlib.Path("test-bob.db").unlink(missing_ok=True)
    for png in docs_dir.glob("*.png"):
        png.unlink()


def teardown_module(module):
    """Render documentation."""
    for name, details in characters.items():
        details["browser"].quit()
    toc = ""
    story = ""
    for index, (who, caption, description, slug) in enumerate(scenes):
        if caption:
            toc += f"<li><a href=#{slug}>{caption}</a></li>"
        story += f"<section id={slug}>"
        if caption:
            story += f"<h2>{caption}</h2>"
        if description:
            story += f"<p>{description}</p>"
        story += f"<div class=storyboard>"
        for character in sorted(characters.keys()):
            if character in who:
                url = (
                    f"https://media.githubusercontent.com/media/canopy/understory/"
                    f"main/docs/{index:03}_{character}_{slug}.png"
                )
                story += f"<a href={url}><img src={url}></a>"
            else:
                story += "<div class=filler></div>"
        story += f"</div></section>"
    now = web.utcnow()
    with (docs_dir / "index.html").open("w") as output_fp:
        with (tests_dir / "doc_root.html").open() as template_fp:
            output_fp.write(str(web.template(template_fp)(now, characters, toc, story)))


def shot(caption, description, *involved):
    slug = caption.replace(" ", "_").lower()
    for character in involved:
        path = docs_dir / f"{len(scenes):03}_{character}_{slug}.png"
        characters[character]["browser"].save_screenshot(str(path))
    scenes.append((involved, caption, description, slug))


def gen_app(name, port) -> web.Application:
    def wrap(handler, app):
        db = sql.db(f"test-{name.lower()}.db")
        db.define("sessions", **web.session_table_sql)
        web.add_job_tables(db)
        tx.host.db = db
        tx.host.cache = web.cache(db=db)
        tx.host.kv = kv.db(f"test-{name.lower()}", ":", {"jobs": "list"})
        yield

    return web.application(
        name,
        host=f"{name.lower()}.example",
        serve=port,
        mounts=(
            indieweb.indieauth.server,
            indieweb.indieauth.client,
            indieweb.indieauth.root,
            indieweb.micropub.server,
            indieweb.webmention.receiver,
            indieweb.content,
        ),
        wrappers=(
            wrap,
            web.resume_session,
            indieweb.indieauth.wrap_server,
            indieweb.indieauth.wrap_client,
            indieweb.micropub.wrap_server,
            indieweb.webmention.wrap_receiver,
        ),
    )


class TestIndieAuthDocs:
    """Test the IndieAuth suite with selenium."""

    @pytest.fixture(scope="class")
    def alice(self):
        """Serve Alice's site and yield her browser."""
        alice_app = gen_app("Alice", 9910)
        browser = webdriver.Firefox(executable_path=GeckoDriverManager().install())
        browser.set_window_size(800, 600)
        characters["Alice"]["browser"] = browser
        browser.test_entry = functools.partial(
            self._test_entry, "alice.example:9910", browser
        )
        yield browser

    @pytest.fixture(scope="class")
    def bob(self):
        """Serve Bob's site and yield his browser."""
        alice_app = gen_app("Bob", 9911)
        browser = webdriver.Firefox(executable_path=GeckoDriverManager().install())
        browser.set_window_size(800, 600)
        characters["Bob"]["browser"] = browser
        yield browser

    def _test_entry(self, character, browser, entry):
        """Create an entry, fetch permalink and return parsed mf2json."""
        response = requests.post(
            f"http://{character}/pub", {"type": ["h-entry"], "properties": entry}
        )
        resource = browser.get(response.headers["Location"])
        return resource.mf2json["items"][0]["properties"]

    def test_claim(self, alice, bob):
        alice.get("http://alice.example:9910")
        alice_name = alice.find_element_by_name("name")
        alice_name.send_keys("Alice")
        bob.get("http://bob.example:9911")
        bob_name = bob.find_element_by_name("name")
        bob_name.send_keys("Bob")
        shot(
            "Claim your domain",
            "Visit your app's address in a browser to claim it.",
            "Alice",
            "Bob",
        )

        alice_name.submit()
        bob_name.submit()
        shot(
            "Write down your passphrase",
            "Save this somewhere not on your computer.",
            "Alice",
            "Bob",
        )

        alice.get("http://alice.example:9910")
        bob.get("http://bob.example:9911")
        shot("Check your homepage", "You're live!", "Alice", "Bob")

    def test_sign_in_to_each_other(self, alice, bob):
        alice.get(
            "http://bob.example:9911/auth/visitors/sign-in?me=http://alice.example:9910"
        )
        bob.get(
            "http://alice.example:9910/auth/visitors/sign-in?me=http://bob.example:9911"
        )
        shot(
            "Sign in to each other's site",
            """When you use IndieAuth to sign in to a friend's website you're going to
            a) confirm that your website is who it says it is and
            b) provide your friend with a secret token for later use.""",
            "Alice",
            "Bob",
        )
        alice.find_element_by_css_selector("button[value=signin]").click()
        bob.find_element_by_css_selector("button[value=signin]").click()
        shot("Signed in", "Once signed in you will see private posts.", "Alice", "Bob")

    def test_micropub_endpoint(self, alice, bob):
        alice.get("http://alice.example:9910/pub")
        bob.get("http://bob.example:9911/pub")
        shot(
            "Go to your content pub for access to posts",
            "All of your content stored in one place, accessible via Micropub.",
            "Alice",
            "Bob",
        )

    def test_webmention_receiver(self, alice, bob):
        alice.get("http://alice.example:9910/mentions")
        bob.get("http://bob.example:9911/mentions")
        shot(
            "Check your received mentions",
            "Mentions from other websites appear here.",
            "Alice",
            "Bob",
        )

    def test_generate_personal_access_token(self, alice, bob):
        alice.get("http://alice.example:9910/auth")
        shot(
            "Generate a personal access token",
            """Manually acquire a token to use from eg. a command line program.""",
            "Alice",
        )
        alice.find_element_by_css_selector("button").click()
        shot("", "", "Alice")

    # def test_create_simple_note(self, alice, bob):
    #     request = {"content": "test content"}
    #     desired = {
    #         "content": [{"html": "<p>test content </p>", "value": "test content"}]
    #     }
    #     parsed = alice.test_entry(request)
    #     assert desired["content"] == parsed["content"]


# class TestIndieAuth:
#     """Test the IndieAuth suite."""
#
#     @pytest.fixture(scope="class")
#     def alice(self):
#         """Serve Alice's site and yield her browser."""
#         alice_app = gen_app("Alice", 9900)
#         yield web.browser()
#
#     @pytest.fixture(scope="class")
#     def bob(self):
#         """Serve Bob's site and yield his browser."""
#         bob_app = gen_app("Bob", 9901)
#         yield web.browser()
#
#     def test_claim(self, alice, bob):
#         """
#         Alice and Bob claim their URLs.
#
#         """
#         response = alice.post(
#             "http://alice.example:9900/auth/claim", data={"name": "Alice"}
#         )
#         assert response.status == 200
#         assert len(response.dom.select("pre")[0].text.split()) == 7  # passphrase length
#         bob.post("http://bob.example:9901/auth/claim", data={"name": "Bob"})
#
#     def test_profile(self, alice, bob):
#         """
#         Alice visits her homepage and verifies her basic information.
#
#         Bob does the same.
#
#         """
#         response = alice.get("http://alice.example:9900")
#         assert response.status == 200
#         assert response.card["name"][0] == "Alice"
#         assert response.card["url"][0] == "http://alice.example:9900"
#         assert bob.get("http://alice.example:9900").status == 200
#
#     def test_profile_update(self, alice, bob):
#         """
#         Alice updates her name and verifies the change.
#
#         """
#         response = alice.post(
#             "http://alice.example:9900/auth/identity", data={"name": "Alice Anderson"}
#         )
#         assert response.status == 200
#         response = alice.get("http://alice.example:9900")
#         assert response.status == 200
#         assert response.card["name"][0] == "Alice Anderson"
#         assert response.card["url"][0] == "http://alice.example:9900"
#
#     def test_friendly_signin(self, alice, bob):
#         """
#         Alice signs in to Bob's site.
#
#         """
#         # response = alice.get(
#         #     "http://bob.example:9901/auth/visitors/sign-in",
#         #     params={"me": "http://alice.example:9900"},
#         # )


# class TestMicropub:
#
#     """Test the Micropub server."""
#     @pytest.fixture
#     def browser(self, scope="class"):
#         """Return a browser backed by an app with a mounted Micropub server."""
#         app = web.application("MicropubTest")
#         browser = web.browser(apps={"mp": app})
#
#         app.mount(web.micropub.server)
#         app.mount(web.indieauth.server)
#         app.mount(web.indieauth.root)
#         app.mount(web.micropub.content)
#
#         app.wrap(web.micropub.wrap_server, "post")
#         app.wrap(web.indieauth.wrap_server, "post")
#
#         @app.wrap
#         def wrap(handler, app):
#             db = sql.db("test.db")
#             db.define("sessions", **web.session_table_sql)
#             web.add_job_tables(db)
#             tx.host.db = db
#             tx.host.cache = web.cache(db=db)
#             tx.host.kv = kv.db("test", ":", {"jobs": "list"})
#             yield
#
#         response = browser.post("mp/auth/claim", {"name": "Testy McTestface"})
#         # TODO check primary author has been created (sqlite db)
#         assert response.status == "200 OK"
#         browser.get("mp")  # TODO check link header
#         browser.test_entry = functools.partial(self._test_entry, browser)
#         return browser
#
#     def _test_entry(self, browser, entry):
#         """Create an entry, fetch permalink and return parsed mf2json."""
#         # pathlib.Path("server.html").unlink(missing_ok=True)
#         # pathlib.Path("entry.html").unlink(missing_ok=True)
#         response = browser.post("mp/pub", {"type": ["h-entry"], "properties": entry})
#         # with open("server.html", "w") as fp:
#         #     fp.write(str(response.text))
#         resource = browser.get(f"mp{response.headers['Location']}")
#         # with open("entry.html", "w") as fp:
#         #     fp.write(str(resource.text))
#         return resource.mf2json["items"][0]["properties"]
#
#     def test_mount(self, browser):
#         """Mount the application in a browser."""
#         # fails when `browser` fixture fails
#
#     # CREATE & READ
#
#     def test_create_simple_note(self, browser):
#         """Create a simple note."""
#         request = {"content": "test content"}
#         desired = {
#             "content": [{"html": "<p>test content </p>", "value": "test content"}]
#         }
#         parsed = browser.test_entry(request)
#         assert desired["content"] == parsed["content"]
#
#     def test_create_simple_article(self, browser):
#         """Create a simple article."""
#         request = {"name": "Test Title", "content": "test content"}
#         desired = {
#             "name": ["Test Title"],
#             "content": [{"html": "<p>test content </p>", "value": "test content"}],
#         }
#         actual = browser.test_entry(request)
#         assert actual["name"] == desired["name"]
#         assert actual["content"] == desired["content"]
#
#     def test_create_personal_weight(self, browser):
#         """Create a simple note of personal weight."""
#         request = {
#             "summary": "Weighed 57.3 kg",
#             "weight": {
#                 "type": ["h-measure"],
#                 "properties": {"num": "57.3", "unit": "kg"},
#             },
#         }
#         desired = {
#             "summary": ["Weighed 57.3 kg"],
#             "weight": [
#                 {
#                     "type": ["h-measure"],
#                     "properties": {"num": ["57.3"], "unit": ["kg"]},
#                     "value": "57.3 kg",
#                 }
#             ],
#         }
#         actual = browser.test_entry(request)
#         assert actual["summary"] == desired["summary"]
#         assert actual["weight"] == desired["weight"]
#
#     # UPDATE
#
#     # DELETE
#
#     # UNDELETE
#
#     # QUERYING
#
#     def test_query_config(self, browser):
#         """Query for configuration."""
#         config = browser.get("mp/pub", {"q": "config"})
#         assert str(config.headers["Content-Type"]) == "application/json"
#         assert config.text == {
#             "q": ["category", "contact", "source", "syndicate-to"],
#             "media-endpoint": "https://mp/pub/media",
#             "syndicate-to": [],
#             "visibility": ["public", "unlisted", "private"],
#         }
#
#     def test_query_for_single_source(self, browser):
#         """Query for a single source."""
#         request = {"type": ["h-entry"], "properties": {"content": "test content"}}
#         response = browser.post("mp/pub", request)
#         permalink = f"{response.headers['Location']}"
#         source = browser.get("mp/pub", {"q": "source", "url": permalink})
#         assert source.text["resource"]["content"][0] == request["properties"]["content"]
#
#     # SYNDICATION
