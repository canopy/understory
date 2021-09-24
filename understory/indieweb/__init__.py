"""Mountable IndieWeb apps and helper functions."""

from understory import mm, web
from understory.apps import (indieauth_client, indieauth_server,
                             micropub_server, text_editor)
from understory.web import tx

from ..apps import cache, content, data, owner, search
from . import microsub, webmention, websub

__all__ = ["personal_site"]

about = web.application("About", prefix="about")
people = web.application("People", prefix="people")


def personal_site(name: str, host: str = None, port: int = None) -> web.Application:
    """Return a `web.applicaion` pre-configured for use as a personal website."""
    return web.application(
        name,
        db=True,
        host=host,
        port=port,
        mounts=(
            owner.app,
            search.app,
            cache.app,
            data.app,
            # TODO about,
            # TODO people,
            web.debug_app,
            indieauth_server.app,
            indieauth_client.app,
            websub.publisher.app,  # websub must come before micropub/microsub
            websub.subscriber.app,
            text_editor.app,
            micropub_server.app,
            microsub.server.app,
            microsub.client.app,
            webmention.app,
            content.app,  # has no prefix, must remain last
        ),
        wrappers=(
            owner.wrap,
            micropub_server.wrap,
            microsub.server.wrap,
            indieauth_server.wrap,
            indieauth_client.wrap,
            webmention.wrap,
            websub.publisher.wrap,
        ),
    )


@about.control(r"")
class About:
    """"""

    def get(self):
        return templates.about.index(tx.host.owner, tx.pub.get_posts())


@about.control(r"editor")
class AboutEditor:
    """"""

    def get(self):
        return templates.about.editor(tx.host.owner, tx.pub.get_posts())

    def post(self):
        if not tx.user.is_owner:
            raise web.Unauthorized("must be owner")
        try:
            self.set_name(web.form("name").name)
        except web.BadRequest:
            pass
        try:
            self.set_note(web.form("note").note)
        except web.BadRequest:
            pass
        try:
            self.set_github(web.form("github").github)
        except web.BadRequest:
            pass
        try:
            self.set_twitter(web.form("twitter").twitter)
        except web.BadRequest:
            pass
        try:
            self.set_skills(web.form("skills").skills)
        except web.BadRequest:
            pass
        return "saved"

    def set_name(self, name):
        card = tx.host.owner
        card.update(name=[name])
        tx.db.update("identities", card=card)

    def set_note(self, note):
        card = tx.host.owner
        card["note"] = [note]
        tx.db.update("identities", card=card)

    def set_github(self, name):
        card = tx.host.owner
        card["url"].append(f"https://github.com/{name}")
        tx.db.update("identities", card=card)

    def set_twitter(self, name):
        card = tx.host.owner
        card["url"].append(f"https://twitter.com/{name}")
        tx.db.update("identities", card=card)

    def set_skills(self, skills):
        resume = get_resume()
        if resume is None:
            resume = {}
        resume.update(skills=skills.split())
        tx.db.update("identities", resume=resume)


@people.control(r"")
class People:
    def get(self):
        return templates.people.index(
            indieauth.server.get_clients(), indieauth.client.get_users()
        )
