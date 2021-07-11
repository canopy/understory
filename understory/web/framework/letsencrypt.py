"""A simple Let's Encrypt interface (a la acme-tiny)."""

import acme_tiny
import sh


def generate_cert(domain, cert_dir, challenge_dir):
    """Generate a TLS certificate signed by Let's Encrypt for given domain."""
    account_key = cert_dir / "account.key"
    if not account_key.exists():
        sh.openssl("genrsa", "4096", _out=str(account_key))
    private_key = cert_dir / "domain.key"
    if not private_key.exists():
        sh.openssl("genrsa", "4096", _out=str(private_key))
    csr = cert_dir / "domain.csr"
    if not csr.exists():
        sh.openssl(
            "req",
            "-new",
            "-sha256",
            "-key",
            private_key,
            "-subj",
            f"/CN={domain}",
            _out=str(csr),
        )
    with (cert_dir / "domain.crt").open("w") as fp:
        fp.write(acme_tiny.get_crt(account_key, csr, challenge_dir))
    csr.unlink()
