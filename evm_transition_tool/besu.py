"""
Hyperledger Besu Transition tool frontend.
"""

import json
import re
import subprocess
import textwrap
from pathlib import Path
from re import compile
from typing import Any, Dict, List, Optional, Tuple

import requests

from ethereum_test_forks import Fork

from .transition_tool import TransitionTool, dump_files_to_directory


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

        input_json = {
            "alloc": alloc,
            "txs": txs,
            "env": env,
        }
        state_json = {
            "fork": fork_name,
            "chainid": chain_id,
            "reward": reward,
        }

        post_data = {"state": state_json, "input": input_json}

        if debug_output_path:
            post_data_string = json.dumps(post_data, indent=4)
            additional_indent = " " * 16  # for pretty indentation in t8n.sh
            indented_post_data_string = "{\n" + "\n".join(
                additional_indent + line for line in post_data_string[1:].splitlines()
            )
            t8n_script = textwrap.dedent(
                f"""\
                #!/bin/bash
                curl http://localhost:3000/ -X POST -H "Content-Type: application/json" --data '
                {indented_post_data_string}'
                """
            )
            dump_files_to_directory(
                debug_output_path,
                {
                    "state.json": state_json,
                    "input/alloc.json": input_json["alloc"],
                    "input/env.json": input_json["env"],
                    "input/txs.json": input_json["txs"],
                    "t8n.sh+x": t8n_script,
                },
            )

        response = requests.post(self.server_url, json=post_data, timeout=5)
        response.raise_for_status()  # exception visible in pytest failure output
        output = response.json()

        if debug_output_path:
            dump_files_to_directory(
                debug_output_path,
                {
                    "response.txt": response.text,
                    "status_code.txt": response.status_code,
                    "time_elapsed_seconds.txt": response.elapsed.total_seconds(),
                },
            )

        if response.status_code != 200:
            raise Exception(
                f"t8n-server returned status code {response.status_code}, "
                f"response: {response.text}"
            )
        if not all([x in output for x in ["alloc", "result", "body"]]):
            raise Exception(
                "Malformed t8n output: missing 'alloc', 'result' or 'body', server response: "
                f"{response.text}"
            )

        if debug_output_path:
            dump_files_to_directory(
                debug_output_path,
                {
                    "output/alloc.json": output["alloc"],
                    "output/result.json": output["result"],
                    "output/txs.rlp": output["body"],
                },
            )

        return output["alloc"], output["result"]

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Returns True if the fork is supported by the tool
        """
        return fork.fork() in self.help_string
