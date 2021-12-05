"""Passphrase functionality."""

import hmac
import json
import pathlib
import secrets

import Crypto.Random

try:
    import scrypt
except OSError:
    pass

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
    scrypt_hash = scrypt.hash(passphrase, salt)
    return salt, scrypt_hash, passphrase_words


def verify_passphrase(salt, scrypt_hash, passphrase):
    """
    Verify passphrase.

    `passphrase` should be concatenation of generated words, without spaces

    """
    return hmac.compare_digest(scrypt.hash(passphrase, salt), scrypt_hash)
