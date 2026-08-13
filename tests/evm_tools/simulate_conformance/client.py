"""
Run go-ethereum out of the hive image and talk JSON-RPC to it.

The client is the one thing here that cannot be derived, so it is kept
at arm's length: a container started from an image the repository does
not build, initialized from [`genesis_json`], torn down afterwards, and
reached over HTTP. Nothing about the comparison depends on which client
it is — [`SimulateClient`] is a two-method interface any JSON-RPC
endpoint satisfies.

[`genesis_json`]: ref:tests.evm_tools.simulate_conformance.genesis.genesis_json
"""

import json
import subprocess
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from typing import Any, Dict, Iterator, List, Optional

from .genesis import genesis_json

GO_ETHEREUM_IMAGE = "hive/clients/go-ethereum:latest"
"""The image hive builds. Not published, so it has to be built locally."""

GETH_BINARY = "/usr/local/bin/geth"
CONTAINER_NAME = "eels-simulate-conformance"
HOST_PORT = 18545
STARTUP_TIMEOUT_SECONDS = 60


class ClientUnavailableError(Exception):
    """Docker or the client image is not present."""


class SimulateClient:
    """A JSON-RPC endpoint that answers `eth_simulateV1`."""

    def __init__(self, url: str) -> None:
        self.url = url

    def request(self, method: str, params: List[Any]) -> Dict[str, Any]:
        """
        Send one JSON-RPC request and return the whole envelope.

        The envelope rather than the result, because half of what is
        being compared is which error a bad request produces.
        """
        body = json.dumps(
            {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        ).encode()
        request = urllib.request.Request(
            self.url,
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            parsed = json.loads(response.read())
        assert isinstance(parsed, dict)
        return parsed

    def simulate(
        self, payload: Dict[str, Any], reference: str = "latest"
    ) -> Dict[str, Any]:
        """Send one `eth_simulateV1` request."""
        return self.request("eth_simulateV1", [payload, reference])

    def alive(self) -> bool:
        """Return whether the endpoint answers at all."""
        try:
            self.request("eth_chainId", [])
        except (urllib.error.URLError, OSError, json.JSONDecodeError):
            return False
        return True


def _docker(*arguments: str, check: bool = True) -> str:
    """Run a docker command and return its output."""
    result = subprocess.run(
        ["docker", *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise ClientUnavailableError(
            f"docker {' '.join(arguments)} failed: {result.stderr.strip()}"
        )
    return result.stdout


def client_image_available() -> bool:
    """Return whether the hive go-ethereum image is built locally."""
    try:
        listing = _docker(
            "images", "--format", "{{.Repository}}:{{.Tag}}", check=True
        )
    except (ClientUnavailableError, FileNotFoundError):
        return False
    return GO_ETHEREUM_IMAGE in listing.split()


def client_version() -> str:
    """Return the version string of the image that will be run."""
    output = _docker(
        "run",
        "--rm",
        "--entrypoint",
        GETH_BINARY,
        GO_ETHEREUM_IMAGE,
        "version",
    )
    fields = {}
    for line in output.splitlines():
        if ":" in line:
            name, _, value = line.partition(":")
            fields[name.strip()] = value.strip()
    return f"{fields.get('Version', '?')} ({fields.get('Git Commit', '?')})"


@contextmanager
def running_client(
    port: int = HOST_PORT, keep_data: Optional[Path] = None
) -> Iterator[SimulateClient]:
    """
    Start go-ethereum on the harness genesis and yield a client for it.

    The node never produces a block: post-merge it waits for a consensus
    layer that is not coming, and it does not need to, because
    `eth_simulateV1` is answered against the head and the head is
    genesis.
    """
    if not client_image_available():
        raise ClientUnavailableError(
            f"{GO_ETHEREUM_IMAGE} is not present; build it with hive first"
        )

    directory = mkdtemp(prefix="eels-simulate-")
    try:
        workspace = Path(keep_data) if keep_data else Path(directory)
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "genesis.json").write_text(
            json.dumps(genesis_json(), indent=2)
        )

        _docker("rm", "-f", CONTAINER_NAME, check=False)
        _docker(
            "run",
            "--rm",
            "-v",
            f"{workspace}:/harness",
            "--entrypoint",
            GETH_BINARY,
            GO_ETHEREUM_IMAGE,
            "init",
            "--datadir",
            "/harness/data",
            "/harness/genesis.json",
        )
        _docker(
            "run",
            "-d",
            "--name",
            CONTAINER_NAME,
            "-p",
            f"{port}:8545",
            "-v",
            f"{workspace}:/harness",
            "--entrypoint",
            GETH_BINARY,
            GO_ETHEREUM_IMAGE,
            "--datadir",
            "/harness/data",
            "--networkid",
            "1",
            "--http",
            "--http.addr",
            "0.0.0.0",
            "--http.api",
            "eth,web3,net,debug",
            "--http.vhosts",
            "*",
            "--nodiscover",
            "--maxpeers",
            "0",
            "--syncmode",
            "full",
        )
        client = SimulateClient(f"http://127.0.0.1:{port}")
        try:
            deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
            while not client.alive():
                if time.monotonic() > deadline:
                    logs = _docker("logs", CONTAINER_NAME, check=False)
                    raise ClientUnavailableError(
                        f"client did not come up:\n{logs[-2000:]}"
                    )
                time.sleep(0.5)
            yield client
        finally:
            _docker("rm", "-f", CONTAINER_NAME, check=False)
    finally:
        # The client writes its data directory as root, so it has to be
        # removed from inside a container to be removed at all.
        _docker(
            "run",
            "--rm",
            "-v",
            f"{directory}:/harness",
            "--entrypoint",
            "rm",
            GO_ETHEREUM_IMAGE,
            "-rf",
            "/harness/data",
            check=False,
        )
        rmtree(directory, ignore_errors=True)
