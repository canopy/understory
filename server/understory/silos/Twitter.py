"""Bridge to Twitter."""

import time

from understory import web

URLS = {"user": "https://twitter.com/(?P<user>.+)"}


def login(browser, handle, passphrase):
    """Log in."""
    browser.go("https://twitter.com/login")
    time.sleep(2)
    username = browser.select_first("input[type=text]")
    username.send_keys(handle)
    password = browser.select_first("input[type=password]")
    password.send_keys(passphrase)
    password.submit()
    time.sleep(3)


def get_tweet(browser, tweet_url):
    """Get a tweet and its interactions."""
    browser.go(tweet_url)
    time.sleep(2)
    urls = []
    for article in browser.select("article"):
        links = []
        for link in article.find_elements_by_css_selector("a"):
            suffixes = ("/retweets", "/retweets/with_comments", "/likes")
            if (
                link.get_property("target") == "_blank"
                or link.text.startswith("@")
                or link.get_property("href").endswith(suffixes)
            ):
                continue
            links.append(link)
        url = links[{3: 2, 4: 2, 5: 3}[len(links)]].get_property("href")
        urls.append(url)
    post = {"url": tweet_url}
    if urls[0] == tweet_url:  # a note
        article_index = 0
        child_index = 0
        post["comment"] = urls[1:]
    elif urls[1] == tweet_url:  # a reply
        post["in-reply-to"] = urls[0]
        post["comment"] = urls[2:]
        article_index = 1
        child_index = 1
    js = f"""return document.querySelectorAll("article")[{article_index}]
             .querySelector("div[data-testid=tweet] + div")
             .childNodes[{child_index}].childNodes[0].childNodes[0]
             .innerHTML"""
    doc = web.Document(browser.execute_script(js)).doc
    children = doc.getchildren()
    if children:
        parts = []
        for child in children:
            grandchildren = child.getchildren()
            if child.tag == "a":
                url = child.attrib["title"]
                part = f'<a href="{url}">{url}</a>'
            elif grandchildren:
                grandchild_text = grandchildren[0].text_content()
                if grandchild_text.startswith("@"):  # @-mention
                    part = (
                        f'<a class=h-card href="https://twitter.com/'
                        f'{grandchild_text}">{grandchild_text}</a>'
                    )
                else:  # emoji
                    part = grandchildren[0].attrib["aria-label"]
            else:
                part = child.text_content().replace("\n", "<br>")
            parts.append(part)
        content = "".join(parts)
    else:
        content = doc.text_content()
    post["content"] = content
    return post


def publish_tweet(browser, tweet, source_url=None, in_reply_to=None):
    """Publish a tweet and return its url."""
    if in_reply_to:
        start_url = in_reply_to
        button = "Reply"
        y_offset = 320
        article_index = 1
    else:
        start_url = "https://twitter.com/home"
        button = "Tweet"
        y_offset = 220
        article_index = 0
    browser.go(start_url)
    time.sleep(2)
    browser.select_first(f"*[aria-label={button}]").click()
    time.sleep(2)
    padding = web.browsers.index(browser) * 1024
    body = tweet
    if source_url:
        body += f" \u2014 {source_url}"
    sh.xdotool("mousemove", padding + 330, y_offset, "click", 1, "type", body)
    browser.select_first("*[data-testid=tweetButton]").click()
    time.sleep(2)
    js = f"""return document.querySelectorAll("article")[{article_index}]
             .querySelectorAll("div[data-testid=tweet] a")[2].href"""
    return browser.execute_script(js)
