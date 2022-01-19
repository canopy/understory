"""Domain registrars and hosting providers."""

import lxml.etree
import requests

hosts = []


class TokenError(Exception):
    """Bad auth token."""


class DigitalOcean:
    ...


hosts = [DigitalOcean]


class Dynadot:
    """Interface the Dynadot service."""

    endpoint = "https://api.dynadot.com/api3.xml"

    def __init__(self, token=None):
        """Return a Dynadot client."""
        self.key = token

    def list_domains(self):
        """List currently registered domains."""
        response = self._request("list_domain")
        domains = []
        for domain in response.cssselect("DomainInfo"):
            name = domain.cssselect("Name")[0].text
            expiration = domain.cssselect("Expiration")[0].text
            domains.append((name, expiration))
        return domains

    def create_record(self, domain, record, subdomain=""):
        """Set DNS record for given domain."""
        # TODO set low ttl
        command = "set_dns2"
        record_type = "a"
        if subdomain:
            return self._request(
                command,
                domain=domain,
                main_record_type0=record_type,
                main_record0=record,
                subdomain0=subdomain,
                sub_record_type0=record_type,
                sub_record0=record,
            )
        return self._request(
            command, domain=domain, main_record_type0=record_type, main_record0=record
        )

    def search(self, *domains):
        """Search for available of domains."""
        domain_params = {
            "domain{}".format(n): domain for n, domain in enumerate(domains)
        }
        response = self._request(show_price="1", **domain_params)
        results = {}
        for result in response:
            # if len(result[0]) == 5:
            # data = {"price": result[0][4].text}
            # results[result[0][1].text] = data
            available = False if result[0].find("Available").text == "no" else True
            price = result[0].find("Price")
            if price is None:
                price = 0
            else:
                if " in USD" in price.text:
                    price = float(price.text.partition(" ")[0])
                else:
                    price = "?"
            results[result[0].find("DomainName").text] = (available, price)
        return results

    def register(self, domain, duration=1):
        """Register domain."""
        return self._request("register", domain=domain, duration=duration)

    def account_info(self):
        """Return account information."""
        return self._request("account_info")[1][0]

    def _request(self, command, **payload):
        """Send an API request."""
        payload.update(command=command, key=self.key)
        response = requests.get(self.endpoint, params=payload)
        message = lxml.etree.fromstring(response.text)
        try:
            if message.cssselect("ResponseCode")[0].text == "-1":
                print(response.text)
                raise TokenError()
        except IndexError:
            pass
        return message


class NameCom:
    """Interface the Name.com service."""

    endpoint = "https://api.name.com"

    def __init__(self, username=None, token=None):
        """Return a Name.com client."""
        self.username = username
        self.token = token

    def list_domains(self):
        """List currently registered domains."""
        return [
            (domain["domainName"], domain["expireDate"])
            for domain in self._request("get", "domains")["domains"]
        ]

    def create_record(self, domain, record, subdomain=""):
        """
        Set DNS record for given domain.

        https://www.name.com/api-docs/DNS#CreateRecord

        """
        return self._request(
            "post",
            f"domains/{domain}/records",
            host=subdomain,
            type="A",
            answer=record,
            ttl="300",
        )

    def _request(self, method, command, **payload):
        """Send an API request."""
        post_body = {}
        if payload:
            post_body = {"json": payload}
        response = getattr(requests, method)(
            f"{self.endpoint}/v4/{command}",
            auth=(self.username, self.token),
            headers={"Content-Type": "application/json"},
            **post_body,
        )
        return response.json()


registrars = [Dynadot, NameCom]
