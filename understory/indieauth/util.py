"""Utility functions."""

import base64
import hashlib


def generate_challenge(verifier):
    """Compute a `challenge` from given `verifier`."""
    raw_hash = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(raw_hash).decode().rstrip("=")
