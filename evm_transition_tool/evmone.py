"""
Evmone Transition tool interface.
"""
import json
import os
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path
from re import compile
from typing import Any, Dict, List, Optional, Tuple

from ethereum_test_forks import Fork

from .transition_tool import TransitionTool, dump_files_to_directory


def write_json_file(data: Dict[str, Any], file_path: str) -> None:
    """
    Write a JSON file to the given path.
    """
    with open(file_path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class EvmOneTransitionTool(TransitionTool):
    """
    Evmone `evmone-t8n` Transition tool interface wrapper class.
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
        Executes `evmone-t8n` with the specified arguments.
        """
        if eips is not None:
            fork_name = "+".join([fork_name] + [str(eip) for eip in eips])

        temp_dir = tempfile.TemporaryDirectory()
        os.mkdir(os.path.join(temp_dir.name, "input"))
        os.mkdir(os.path.join(temp_dir.name, "output"))

        input_contents = {
            "alloc": alloc,
            "env": env,
            "txs": txs,
        }

        input_paths = {
            k: os.path.join(temp_dir.name, "input", f"{k}.json") for k in input_contents.keys()
        }
        for key, file_path in input_paths.items():
            write_json_file(input_contents[key], file_path)

        output_paths = {
            output: os.path.join("output", f"{output}.json") for output in ["alloc", "result"]
        }
        output_paths["body"] = os.path.join("output", "txs.rlp")

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
            output_paths["result"],
            "--output.alloc",
            output_paths["alloc"],
            "--output.body",
            output_paths["body"],
            "--state.reward",
            str(reward),
            "--state.chainid",
            str(chain_id),
        ]

        if self.trace:
            args.append("--trace")

        result = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if debug_output_path:
            if os.path.exists(debug_output_path):
                shutil.rmtree(debug_output_path)
            shutil.copytree(temp_dir.name, debug_output_path)
            t8n_output_base_dir = os.path.join(debug_output_path, "t8n.sh.out")
            t8n_call = " ".join(args)
            for file_path in input_paths.values():  # update input paths
                t8n_call = t8n_call.replace(
                    os.path.dirname(file_path), os.path.join(debug_output_path, "input")
                )
            t8n_call = t8n_call.replace(  # use a new output path for basedir and outputs
                temp_dir.name,
                t8n_output_base_dir,
            )
            t8n_script = textwrap.dedent(
                f"""\
                #!/bin/bash
                output_directory={os.path.join(t8n_output_base_dir, "output")}
                rm -rf $output_directory
                mkdir -p $output_directory
                {t8n_call}
                """
            )
            dump_files_to_directory(
                debug_output_path,
                {
                    "args.py": args,
                    "returncode.txt": result.returncode,
                    "stdout.txt": result.stdout.decode(),
                    "stderr.txt": result.stderr.decode(),
                    "t8n.sh+x": t8n_script,
                },
            )

        if result.returncode != 0:
            raise Exception("failed to evaluate: " + result.stderr.decode())

        for key, file_path in output_paths.items():
            output_paths[key] = os.path.join(temp_dir.name, file_path)

        output_contents = {}
        for key, file_path in output_paths.items():
            if "txs.rlp" in file_path:
                continue
            with open(file_path, "r+") as file:
                output_contents[key] = json.load(file)

        if self.trace:
            self.collect_traces(output_contents["result"]["receipts"], temp_dir, debug_output_path)

        temp_dir.cleanup()

        return output_contents["alloc"], output_contents["result"]

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Returns True if the fork is supported by the tool.
        Currently, evmone-t8n provides no way to determine supported forks.
        """
        return True
