"""Digital Ocean client."""

import json
import os
import pathlib
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

# XXX sh.ssh_copy_id("-f", "-i", "key", "-o", "IdentityFile=sshkeyfile",
# XXX                "root@server.name")


class TokenError(Exception):
    """Bad token."""


class DomainExistsError(Exception):
    """Domain already exists."""


def get_key(do):
    """Return a SSH key, registering it with DigitalOcean if necessary."""
    key_path = pathlib.Path("gaea_key.pub")
    try:
        with key_path.open() as fp:
            key_data = fp.read().strip()
    except FileNotFoundError:
        subprocess.run(
            [
                "ssh-keygen",
                "-o",
                "-a",
                "100",
                "-t",
                "ed25519",
                "-N",
                "",
                "-f",
                str(key_path)[:-4],
            ]
        )
        with key_path.open() as fp:
            key_data = fp.read().strip()
        key = do.add_key("gaea", key_data)
    else:
        for key in do.get_keys()["ssh_keys"]:
            if key["public_key"] == key_data:
                break
        else:
            key = do.add_key("gaea", key_data)
    return key


def get_ssh(user, ip_address, output_handler=None):
    """Return a function for executing commands over SSH."""

    def ssh(*command, env=None, stdin=None):
        combined_env = os.environ.copy()
        if env:
            combined_env.update(env)
        kwargs = {
            "env": combined_env,
            "stderr": subprocess.STDOUT,
            "stdout": subprocess.PIPE,
        }
        if stdin:
            kwargs["stdin"] = subprocess.PIPE
        # env=combined_env,
        # stdin=subprocess.PIPE,
        # stderr=subprocess.STDOUT,
        # stdout=subprocess.PIPE,
        with subprocess.Popen(
            [
                "ssh",
                "-i",
                "gaea_key",
                "-tt",  # FIXME necessary?
                "-o",
                "IdentitiesOnly=yes",
                "-o",
                "StrictHostKeyChecking no",
                f"{user}@{ip_address}",
                *command,
            ],
            **kwargs,
        ) as process:
            # TODO make explicit stdout/stderr
            if stdin:
                try:
                    for line in process.communicate(
                        input=stdin.encode("utf-8"), timeout=3
                    )[0].decode("utf-8"):
                        if output_handler:
                            output_handler(line)
                        else:
                            print(line)
                except subprocess.TimeoutExpired:
                    process.kill()
                    stdout, stderr = process.communicate()
                    print(f"stdout: {stdout}")
                    print(f"stderr: {stderr}")
            else:
                for line in process.stdout:
                    if output_handler:
                        output_handler(line.decode("utf-8"))
                    else:
                        print(line.decode("utf-8"))
        return process

    tries = 20
    while tries:
        if tries == 18:
            print("..waiting for server to come alive..", end="")
            # TODO use log here if possible
        result = ssh("true").returncode
        if result == 255:
            print(".", end="", flush=True)
        elif result == 0:
            break
        time.sleep(2)
        tries -= 1
    else:
        print(" couldn't connect!")
        # TODO raise an error here instead..
    print()
    return ssh


def scp(from_path, to_path):
    """Return a function for sending/retrieving a file over SCP."""
    with subprocess.Popen(
        [
            "scp",
            "-i",
            "gaea_key",
            "-o",
            "IdentitiesOnly=yes",
            "-o",
            "StrictHostKeyChecking no",
            from_path,
            to_path,
        ],
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
    ) as process:
        for line in process.stdout:
            print(line.decode("utf-8"))
    return process


def wait(do, droplet_id):
    """Wait for a droplet to come alive."""
    while do.get_droplet_actions(droplet_id)[0]["status"] == "in-progress":
        time.sleep(1)


class Client:
    """Interface the DigitalOcean service."""

    endpoint = "https://api.digitalocean.com/v2/"

    def __init__(self, key, debug=False):
        self.key = str(key)
        self.debug = debug

    def get_keys(self):
        return self._get("account/keys")

    def add_key(self, name, key_data):
        data = {"name": name, "public_key": key_data}
        return self._post("account/keys", **data)["ssh_key"]

    def get_domains(self):
        return self._get("domains")

    def create_domain(self, domain, address):
        data = {"name": domain, "ip_address": address}
        try:
            response = self._post("domains", **data)
        except urllib.error.HTTPError as err:
            if err.code == 422:
                raise DomainExistsError()
        return response

    def create_domain_record(self, domain, subdomain, record_data, record_type="A"):
        data = {"name": subdomain, "data": record_data, "type": record_type}
        return self._post(f"domains/{domain}/records", **data)

    def get_domain_records(self, domain):
        return self._get(f"domains/{domain}/records")["domain_records"]

    def update_domain_record(self, domain, record, **kwargs):
        return self._put(f"domains/{domain}/records/{record}", **kwargs)[
            "domain_record"
        ]

    def get_droplets(self):
        return self._get("droplets")

    def get_droplet(self, droplet_id):
        return self._get(f"droplets/{droplet_id}")["droplet"]

    def create_droplet(
        self,
        name,
        region="sfo2",
        size="s-1vcpu-1gb",
        image="debian-10-x64",
        ssh_keys=None,
        tags=None,
    ):
        data = {
            "name": name,
            "region": region,
            "size": size,
            "image": image,
            "ssh_keys": ssh_keys,
            "tags": tags,
        }
        return self._post("droplets", **data)["droplet"]

    def delete_droplet(self, droplet_id):
        return self._delete(f"droplets/{droplet_id}")

    def get_droplet_actions(self, droplet_id):
        return self._get(f"droplets/{droplet_id}/actions")["actions"]

    def shutdown_droplet(self, droplet_id):
        data = {"type": "shutdown"}
        return self._post(f"droplets/{droplet_id}/actions", **data)["action"]

    def get_snapshots_of_droplets(self):
        return self._get("snapshots", resource_type="droplet")

    def get_droplet_snapshots(self, droplet_id):
        return self._get(f"droplets/{droplet_id}/snapshots")["snapshots"]

    def take_snapshot(self, droplet_id, name):
        data = {"type": "snapshot", "name": name}
        return self._post(f"droplets/{droplet_id}/actions", **data)["action"]

    def get_images(self):
        return self._get("images", per_page=200)

    def _get(self, path, **args):
        return self._request("get", path, data=args)

    def _post(self, path, **args):
        return self._request("post", path, data=args)

    def _put(self, path, **args):
        return self._request("put", path, data=args)

    def _delete(self, path, **args):
        return self._request("delete", path, data=args)

    def _request(self, method, path, data=None):
        """Send an API request."""
        url = self.endpoint + path
        args = {
            "method": method.upper(),
            "headers": {"Authorization": "Bearer " + self.key},
        }
        if method in ("post", "put", "delete"):
            args["headers"].update({"Content-Type": "application/json"})
        if data:
            if method == "get":
                url += "?" + urllib.parse.urlencode(data)
            else:
                args["data"] = json.dumps(data).encode()
        req = urllib.request.Request(url, **args)
        try:
            response = urllib.request.urlopen(req)
        except urllib.error.HTTPError as err:
            error = json.loads(err.read().decode())
            if error["id"] == "Unauthorized":
                raise TokenError()
            else:
                print(error)
        if method == "delete":
            response = True if response.status == 204 else False
        else:
            response = json.loads(response.read())
        if self.debug:
            print(">>", method, path)
            print(">>", response)
        return response
