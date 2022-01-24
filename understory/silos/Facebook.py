"""Bridge to Facebook."""

import time

URLS = {"user": "https://facebook.com/(?P<user>.+)"}


def login(browser, handle, passphrase):
    """Log in."""
    browser.go("https://facebook.com/login")
    time.sleep(2)
    username = browser.select_first("input#user")
    username.send_keys(handle)
    password = browser.select_first("input#pass")
    password.send_keys(passphrase)
    password.submit()
    time.sleep(3)


def update_website_address(browser, url):
    """Update personal website address."""
    browser.go("https://www.facebook.com/me/about_contact_and_basic_info")
    # TODO make the update
