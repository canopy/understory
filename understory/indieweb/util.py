def discover_post_type(properties):
    """Return the discovered post type."""
    if "photo" in properties:
        post_type = "photo"
    elif "bookmark-of" in properties:
        post_type = "bookmark"
    elif "like-of" in properties:
        post_type = "like"
    elif "follow-of" in properties:
        post_type = "follow"
    elif "identification-of" in properties:
        post_type = "identification"
    elif "rsvp" in properties:
        post_type = "rsvp"
    elif "in-reply-to" in properties:
        post_type = "reply"
    elif "weight" in properties:
        post_type = "weight"
    elif "name" in properties:
        post_type = "article"
    else:
        post_type = "note"
    return post_type
