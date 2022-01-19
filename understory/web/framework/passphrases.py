"""Passphrase functionality."""

import hashlib
import hmac
import json
import pathlib
import secrets

import Crypto.Random

__all__ = ["generate_passphrase", "verify_passphrase"]


random = secrets.SystemRandom()


def generate_passphrase():
    """
    Generate a new randomly-generated wordlist passphrase.

    `passphrase_words` is a list of generated words.

    EFF's large wordlist [1] for passphrase generation.

    [1]: https://www.eff.org/files/2016/07/18/eff_large_wordlist.txt

    """
    with (pathlib.Path(__file__).parent / "passphrases.json").open() as fp:
        wordlist = json.load(fp)
    passphrase_words = list()
    while len(passphrase_words) < 7:
        passphrase_words.append(random.choice(wordlist))
    passphrase = "".join(passphrase_words)
    salt = Crypto.Random.get_random_bytes(64)
    return (
        salt,
        hashlib.scrypt(
            passphrase.encode("utf-8"), salt=salt, n=2048, r=8, p=1, dklen=32
        ),
        passphrase_words,
    )


def verify_passphrase(salt, scrypt_hash, passphrase):
    """
    Verify passphrase.

    `passphrase` should be concatenation of generated words, without spaces

    """
    return hmac.compare_digest(
        hashlib.scrypt(
            passphrase.encode("utf-8"), salt=salt, n=2048, r=8, p=1, dklen=32
        ),
        scrypt_hash,
    )
