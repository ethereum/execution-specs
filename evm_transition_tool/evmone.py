"""
Evmone Transition tool frontend.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path
from re import compile
from typing import Any, Dict, List, Optional, Tuple

from ethereum_test_forks import Fork

from .transition_tool import TransitionTool


def write_json_file(data: Dict[str, Any], file_path: str) -> None:
    """
    Write a JSON file to the given path.
    """
    with open(file_path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class EvmOneTransitionTool(TransitionTool):
    """
    Evmone `evmone-t8n` Transition tool frontend wrapper class.
    """

    default_binary = Path("evmone-t8n")
    detect_binary_pattern = compile(r"^evmone-t8n\b")

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
        if self.trace:
            raise Exception("`evmone-t8n` does not support tracing.")

    def evaluate(
        self,
        alloc: Any,
        txs: Any,
        env: Any,
        fork: Fork,
        chain_id: int = 1,
        reward: int = 0,
        eips: Optional[List[int]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Executes `evmone-t8n` with the specified arguments.
        """
        fork_name = fork.name()
        if eips is not None:
            fork_name = "+".join([fork_name] + [str(eip) for eip in eips])

        temp_dir = tempfile.TemporaryDirectory()

        input_contents = {
            "alloc": alloc,
            "env": env,
            "txs": txs,
        }
        input_paths = {
            k: os.path.join(temp_dir.name, f"input_{k}.json") for k in input_contents.keys()
        }
        for key, val in input_contents.items():
            file_path = os.path.join(temp_dir.name, f"input_{key}.json")
            write_json_file(val, file_path)

        # Construct args for evmone-t8n binary
        args = [
            str(self.binary),
            "--state.fork",
            fork_name,
            "--input.alloc",
            input_paths["alloc"],
            "--input.env",
            input_paths["env"],
            "--input.txs",
            input_paths["txs"],
            "--output.basedir",
            temp_dir.name,
            "--output.result",
            "output_result.json",
            "--output.alloc",
            "output_alloc.json",
            "--output.body",
            "txs.rlp",
            "--state.reward",
            str(reward),
            "--state.chainid",
            str(chain_id),
        ]
        result = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if result.returncode != 0:
            raise Exception("failed to evaluate: " + result.stderr.decode())

        output_paths = {
            "alloc": os.path.join(temp_dir.name, "output_alloc.json"),
            "result": os.path.join(temp_dir.name, "output_result.json"),
        }

        output_contents = {}
        for key, file_path in output_paths.items():
            with open(file_path, "r+") as file:
                contents = json.load(file)
                file.seek(0)
                json.dump(contents, file, ensure_ascii=False, indent=4)
                file.truncate()
                output_contents[key] = contents

        temp_dir.cleanup()

        return output_contents["alloc"], output_contents["result"]

    def version(self) -> str:
        """
        Gets `evmone-t8n` binary version.
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
        Currently, evmone-t8n provides no way to determine supported forks.
        """
        return True
