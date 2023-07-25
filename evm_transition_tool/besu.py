"""
Hyperledger Besu Transition tool frontend.
"""

import re
import subprocess
from pathlib import Path
from re import compile
from typing import Any, Dict, List, Optional, Tuple

import requests

from ethereum_test_forks import Fork

from .transition_tool import TransitionTool


class BesuTransitionTool(TransitionTool):
    """
    Besu EvmTool Transition tool frontend wrapper class.
    """

    default_binary = Path("evm")
    detect_binary_pattern = compile(r"^Hyperledger Besu evm .*$")

    binary: Path
    cached_version: Optional[str] = None
    trace: bool
    process: Optional[subprocess.Popen] = None
    server_url: str

    def __init__(
        self,
        *,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        super().__init__(binary=binary, trace=trace)
        args = [str(self.binary), "t8n", "--help"]
        try:
            result = subprocess.run(args, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise Exception("evm process unexpectedly returned a non-zero status code: " f"{e}.")
        except Exception as e:
            raise Exception(f"Unexpected exception calling evm tool: {e}.")
        self.help_string = result.stdout

    def start_server(self):
        """
        Starts the t8n-server process, extracts the port, and leaves it running for future re-use.
        """
        self.process = subprocess.Popen(
            args=[
                str(self.binary),
                "t8n-server",
                "--port=0",  # OS assigned server port
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        while True:
            line = str(self.process.stdout.readline())

            if not line or "Failed to start transition server" in line:
                raise Exception("Failed starting Besu subprocess\n" + line)
            if "Transition server listening on" in line:
                port = re.search("Transition server listening on ([0-9]+)", line).group(1)
                self.server_url = f"http://localhost:{port}/"
                break

    def shutdown(self):
        """
        Stops the t8n-server process if it was started
        """
        if self.process:
            self.process.kill()

    def evaluate(
        self,
        alloc: Any,
        txs: Any,
        env: Any,
        fork_name: str,
        chain_id: int = 1,
        reward: int = 0,
        eips: Optional[List[int]] = None,
        debug_output_path: str = "",
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Executes `evm t8n` with the specified arguments.
        """
        if not self.process:
            self.start_server()

        if eips is not None:
            fork_name = "+".join([fork_name] + [str(eip) for eip in eips])

        if self.trace:
            raise Exception("Besu `t8n-server` does not support tracing.")

        response = requests.post(
            self.server_url,
            json={
                "state": {
                    "fork": fork_name,
                    "chainid": chain_id,
                    "reward": reward,
                },
                "input": {
                    "alloc": alloc,
                    "txs": txs,
                    "env": env,
                },
            },
            timeout=5,
        )
        response.raise_for_status()  # exception visible in pytest failure output
        output = response.json()

        return output["alloc"], output["result"]

    def version(self) -> str:
        """
        Gets EVMTool binary version.
        """
        if self.cached_version is None:
            result = subprocess.run(
                [str(self.binary), "-v"],
                stdout=subprocess.PIPE,
            )

            if result.returncode != 0:
                raise Exception("failed to evaluate: " + result.stderr.decode())

            self.cached_version = result.stdout.decode().strip()

        return self.cached_version

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Returns True if the fork is supported by the tool
        """
        return fork.fork() in self.help_string
