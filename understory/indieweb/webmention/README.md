# Webmention Receiver Endpoint & Sending Client

## Use

    $ web serve webmention

A webmention endpoint server will start at port `8010` and received mentions
will be stored in the SQLite database `web-Webmention.db`.

You should put that server behind Caddy or Nginx.

You may then query the webmentions multiple ways:

### Command Line Interface

    $ mentions from friendsdomain.com
    {
        'content': 'yo',
        'mention-of': 'yourdomain.com/posts/2021/035/3'
    }

### Python Local Client

    # TODO >>> receiver = web.indie.webmention.LocalClient()
    # TODO >>> receiver.from_domain("friendsdomain.com")[0]
    # TODO {
    # TODO     'content': 'yo',
    # TODO     'mention-of': 'yourdomain.com/posts/2021/035/3'
    # TODO }

### Python Remote API

    # TODO >>> web.get("http://0.0.0.0:8010/?source=friendsdomain.com").json
    # TODO {
    # TODO     'type': 'feed',
    # TODO     'name': 'Webmentions',
    # TODO     'children': [
    # TODO         {
    # TODO             'content': 'yo',
    # TODO             'mention-of': 'yourdomain.com/posts/2021/035/3'
    # TODO         }
    # TODO }

### SQLite via Python ORM

    # TODO >>> db = web.db("web-Webmention.db")
    # TODO >>> db.select("mentions", where="source LIKE ?",
    # TODO ...           vals=["friendsdomain.com%"])[0]["mention"]
    # TODO {
    # TODO     'content': 'yo',
    # TODO     'mention-of': 'yourdomain.com/posts/2021/035/3'
    # TODO }
