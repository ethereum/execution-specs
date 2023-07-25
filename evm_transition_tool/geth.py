"""
Go-ethereum Transition tool interface.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from re import compile
from typing import Any, Dict, List, Optional, Tuple

from ethereum_test_forks import Fork

from .transition_tool import TransitionTool, dump_files_to_directory


class GethTransitionTool(TransitionTool):
    """
    Go-ethereum `evm` Transition tool interface wrapper class.
    """

    default_binary = Path("evm")
    detect_binary_pattern = compile(r"^evm version\b")

    binary: Path
    cached_version: Optional[str] = None
    trace: bool

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

    def evaluate(
        self,
        *,
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
        if eips is not None:
            fork_name = "+".join([fork_name] + [str(eip) for eip in eips])

        temp_dir = tempfile.TemporaryDirectory()

        if int(env["currentNumber"], 0) == 0:
            reward = -1
        args = [
            str(self.binary),
            "t8n",
            "--input.alloc=stdin",
            "--input.txs=stdin",
            "--input.env=stdin",
            "--output.result=stdout",
            "--output.alloc=stdout",
            "--output.body=txs.rlp",
            f"--output.basedir={temp_dir.name}",
            f"--state.fork={fork_name}",
            f"--state.chainid={chain_id}",
            f"--state.reward={reward}",
        ]

        if self.trace:
            args.append("--trace")

        stdin = {
            "alloc": alloc,
            "txs": txs,
            "env": env,
        }

        encoded_input = str.encode(json.dumps(stdin))
        result = subprocess.run(
            args,
            input=encoded_input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if debug_output_path:
            dump_files_to_directory(
                debug_output_path,
                stdin
                | {
                    "args": args,
                    "stdout": result.stdout.decode(),
                    "stderr": result.stderr.decode(),
                    "returncode": result.returncode,
                },
            )

        if result.returncode != 0:
            raise Exception("failed to evaluate: " + result.stderr.decode())

        output = json.loads(result.stdout)

        if "alloc" not in output or "result" not in output:
            raise Exception("malformed result")

        if self.trace:
            receipts: List[Any] = output["result"]["receipts"]
            traces: List[List[Dict]] = []
            for i, r in enumerate(receipts):
                h = r["transactionHash"]
                trace_file_name = f"trace-{i}-{h}.jsonl"
                with open(os.path.join(temp_dir.name, trace_file_name), "r") as trace_file:
                    tx_traces: List[Dict] = []
                    for trace_line in trace_file.readlines():
                        tx_traces.append(json.loads(trace_line))
                    traces.append(tx_traces)
            self.append_traces(traces)

        temp_dir.cleanup()

        if debug_output_path:
            dump_files_to_directory(
                debug_output_path,
                {
                    "output_alloc": output["alloc"],
                    "output_result": output["result"],
                },
            )

        return output["alloc"], output["result"]

    def version(self) -> str:
        """
        Gets `evm` binary version.
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
        Returns True if the fork is supported by the tool.

        If the fork is a transition fork, we want to check the fork it transitions to.
        """
        return fork.fork() in self.help_string
