"""
Transition tool abstract class.
"""

import json
import os
import shutil
import subprocess
import tempfile
import textwrap
from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from itertools import groupby
from pathlib import Path
from re import Pattern
from typing import Any, Dict, List, Optional, Type

from ethereum_test_forks import Fork

from .file_utils import dump_files_to_directory, write_json_file


class UnknownTransitionTool(Exception):
    """Exception raised if an unknown t8n is encountered"""

    pass


class TransitionToolNotFoundInPath(Exception):
    """Exception raised if the specified t8n tool is not found in the path"""

    def __init__(self, message="The transition tool was not found in the path", binary=None):
        if binary:
            message = f"{message} ({binary})"
        super().__init__(message)


class FixtureFormats(Enum):
    """
    Helper class to define fixture formats.
    """

    UNSET_TEST_FORMAT = "unset_test_format"
    STATE_TEST = "state_test"
    BLOCKCHAIN_TEST = "blockchain_test"
    BLOCKCHAIN_TEST_HIVE = "blockchain_test_hive"

    @classmethod
    def is_state_test(cls, format):  # noqa: D102
        return format == cls.STATE_TEST

    @classmethod
    def is_blockchain_test(cls, format):  # noqa: D102
        return format in (cls.BLOCKCHAIN_TEST, cls.BLOCKCHAIN_TEST_HIVE)

    @classmethod
    def is_hive_format(cls, format):  # noqa: D102
        return format == cls.BLOCKCHAIN_TEST_HIVE

    @classmethod
    def is_standard_format(cls, format):  # noqa: D102
        return format in (cls.STATE_TEST, cls.BLOCKCHAIN_TEST)

    @classmethod
    def is_verifiable(cls, format):  # noqa: D102
        return format in (cls.STATE_TEST, cls.BLOCKCHAIN_TEST)

    @classmethod
    def get_format_description(cls, format):
        """
        Returns a description of the fixture format.

        Used to add a description to the generated pytest marks.
        """
        if format == cls.UNSET_TEST_FORMAT:
            return "Unknown fixture format; it has not been set."
        elif format == cls.STATE_TEST:
            return "Tests that generate a state test fixture."
        elif format == cls.BLOCKCHAIN_TEST:
            return "Tests that generate a blockchain test fixture."
        elif format == cls.BLOCKCHAIN_TEST_HIVE:
            return "Tests that generate a blockchain test fixture in hive format."
        raise Exception(f"Unknown fixture format: {format}.")

    @property
    def output_base_dir_name(self) -> Path:
        """
        Returns the name of the subdirectory where this type of fixture should be dumped to.
        """
        return Path(self.value.replace("test", "tests"))

    @property
    def output_file_extension(self) -> str:
        """
        Returns the file extension for this type of fixture.

        By default, fixtures are dumped as JSON files.
        """
        return ".json"


class TransitionTool:
    """
    Transition tool abstract base class which should be inherited by all transition tool
    implementations.
    """

    traces: List[List[List[Dict]]] | None = None

    registered_tools: List[Type["TransitionTool"]] = []
    default_tool: Optional[Type["TransitionTool"]] = None
    default_binary: Path
    detect_binary_pattern: Pattern
    version_flag: str = "-v"
    t8n_subcommand: Optional[str] = None
    statetest_subcommand: Optional[str] = None
    blocktest_subcommand: Optional[str] = None
    cached_version: Optional[str] = None
    t8n_use_stream: bool = True

    # Abstract methods that each tool must implement

    @abstractmethod
    def __init__(
        self,
        *,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """
        Abstract initialization method that all subclasses must implement.
        """
        if binary is None:
            binary = self.default_binary
        else:
            # improve behavior of which by resolving the path: ~/relative paths don't work
            resolved_path = Path(os.path.expanduser(binary)).resolve()
            if resolved_path.exists():
                binary = resolved_path
        binary = shutil.which(binary)  # type: ignore
        if not binary:
            raise TransitionToolNotFoundInPath(binary=binary)
        self.binary = Path(binary)
        self.trace = trace

    def __init_subclass__(cls):
        """
        Registers all subclasses of TransitionTool as possible tools.
        """
        TransitionTool.register_tool(cls)

    @classmethod
    def register_tool(cls, tool_subclass: Type["TransitionTool"]):
        """
        Registers a given subclass as tool option.
        """
        cls.registered_tools.append(tool_subclass)

    @classmethod
    def set_default_tool(cls, tool_subclass: Type["TransitionTool"]):
        """
        Registers the default tool subclass.
        """
        cls.default_tool = tool_subclass

    @classmethod
    def from_binary_path(cls, *, binary_path: Optional[Path], **kwargs) -> "TransitionTool":
        """
        Instantiates the appropriate TransitionTool subclass derived from the
        tool's binary path.
        """
        assert cls.default_tool is not None, "default transition tool was never set"

        if binary_path is None:
            return cls.default_tool(binary=binary_path, **kwargs)

        resolved_path = Path(os.path.expanduser(binary_path)).resolve()
        if resolved_path.exists():
            binary_path = resolved_path
        binary = shutil.which(binary_path)  # type: ignore

        if not binary:
            raise TransitionToolNotFoundInPath(binary=binary)

        binary = Path(binary)

        # Group the tools by version flag, so we only have to call the tool once for all the
        # classes that share the same version flag
        for version_flag, subclasses in groupby(
            cls.registered_tools, key=lambda x: x.version_flag
        ):
            try:
                result = subprocess.run(
                    [binary, version_flag], stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                if result.returncode != 0:
                    raise Exception(f"Non-zero return code: {result.returncode}")

                if result.stderr:
                    raise Exception(f"Tool wrote to stderr: {result.stderr.decode()}")

                binary_output = ""
                if result.stdout:
                    binary_output = result.stdout.decode().strip()
            except Exception:
                # If the tool doesn't support the version flag,
                # we'll get an non-zero exit code.
                continue
            for subclass in subclasses:
                if subclass.detect_binary(binary_output):
                    return subclass(binary=binary, **kwargs)

        raise UnknownTransitionTool(f"Unknown transition tool binary: {binary_path}")

    @classmethod
    def detect_binary(cls, binary_output: str) -> bool:
        """
        Returns True if the binary matches the tool
        """
        assert cls.detect_binary_pattern is not None

        return cls.detect_binary_pattern.match(binary_output) is not None

    def version(self) -> str:
        """
        Return name and version of tool used to state transition
        """
        if self.cached_version is None:
            result = subprocess.run(
                [str(self.binary), self.version_flag],
                stdout=subprocess.PIPE,
            )

            if result.returncode != 0:
                raise Exception("failed to evaluate: " + result.stderr.decode())

            self.cached_version = result.stdout.decode().strip()

        return self.cached_version

    @abstractmethod
    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Returns True if the fork is supported by the tool
        """
        pass

    def shutdown(self):
        """
        Perform any cleanup tasks related to the tested tool.
        """
        pass

    def reset_traces(self):
        """
        Resets the internal trace storage for a new test to begin
        """
        self.traces = None

    def append_traces(self, new_traces: List[List[Dict]]):
        """
        Appends a list of traces of a state transition to the current list
        """
        if self.traces is None:
            self.traces = []
        self.traces.append(new_traces)

    def get_traces(self) -> List[List[List[Dict]]] | None:
        """
        Returns the accumulated traces
        """
        return self.traces

    def collect_traces(
        self,
        receipts: List[Any],
        temp_dir: tempfile.TemporaryDirectory,
        debug_output_path: str = "",
    ) -> None:
        """
        Collect the traces from the t8n tool output and store them in the traces list.
        """
        traces: List[List[Dict]] = []
        for i, r in enumerate(receipts):
            trace_file_name = f"trace-{i}-{r['transactionHash']}.jsonl"
            if debug_output_path:
                shutil.copy(
                    os.path.join(temp_dir.name, trace_file_name),
                    os.path.join(debug_output_path, trace_file_name),
                )
            with open(os.path.join(temp_dir.name, trace_file_name), "r") as trace_file:
                tx_traces: List[Dict] = []
                for trace_line in trace_file.readlines():
                    tx_traces.append(json.loads(trace_line))
                traces.append(tx_traces)
        self.append_traces(traces)

    @dataclass
    class TransitionToolData:
        """
        Transition tool files and data to pass between methods
        """

        alloc: Any
        txs: Any
        env: Any
        fork_name: str
        chain_id: int = field(default=1)
        reward: int = field(default=0)

    def _evaluate_filesystem(
        self,
        *,
        t8n_data: TransitionToolData,
        debug_output_path: str = "",
    ) -> Dict[str, Any]:
        """
        Executes a transition tool using the filesystem for its inputs and outputs.
        """
        temp_dir = tempfile.TemporaryDirectory()
        os.mkdir(os.path.join(temp_dir.name, "input"))
        os.mkdir(os.path.join(temp_dir.name, "output"))

        input_contents = {
            "alloc": t8n_data.alloc,
            "env": t8n_data.env,
            "txs": t8n_data.txs,
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
            t8n_data.fork_name,
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
            str(t8n_data.reward),
            "--state.chainid",
            str(t8n_data.chain_id),
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
                rm -rf {debug_output_path}/t8n.sh.out  # hard-coded to avoid surprises
                mkdir -p {debug_output_path}/t8n.sh.out/output
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

        return output_contents

    def _evaluate_stream(
        self,
        *,
        t8n_data: TransitionToolData,
        debug_output_path: str = "",
    ) -> Dict[str, Any]:
        """
        Executes a transition tool using stdin and stdout for its inputs and outputs.
        """
        temp_dir = tempfile.TemporaryDirectory()
        args = self.construct_args_stream(t8n_data, temp_dir)

        stdin = {
            "alloc": t8n_data.alloc,
            "txs": t8n_data.txs,
            "env": t8n_data.env,
        }

        result = subprocess.run(
            args,
            input=str.encode(json.dumps(stdin)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.dump_debug_stream(debug_output_path, temp_dir, stdin, args, result)

        if result.returncode != 0:
            raise Exception("failed to evaluate: " + result.stderr.decode())

        output = json.loads(result.stdout)

        if not all([x in output for x in ["alloc", "result", "body"]]):
            raise Exception("Malformed t8n output: missing 'alloc', 'result' or 'body'.")

        if debug_output_path:
            dump_files_to_directory(
                debug_output_path,
                {
                    "output/alloc.json": output["alloc"],
                    "output/result.json": output["result"],
                    "output/txs.rlp": output["body"],
                },
            )

        if self.trace:
            self.collect_traces(output["result"]["receipts"], temp_dir, debug_output_path)
            temp_dir.cleanup()

        return output

    def construct_args_stream(
        self, t8n_data: TransitionToolData, temp_dir: tempfile.TemporaryDirectory
    ) -> List[str]:
        """
        Construct arguments for t8n interaction via streams
        """
        command: list[str] = [str(self.binary)]
        if self.t8n_subcommand:
            command.append(self.t8n_subcommand)

        args = command + [
            "--input.alloc=stdin",
            "--input.txs=stdin",
            "--input.env=stdin",
            "--output.result=stdout",
            "--output.alloc=stdout",
            "--output.body=stdout",
            f"--state.fork={t8n_data.fork_name}",
            f"--state.chainid={t8n_data.chain_id}",
            f"--state.reward={t8n_data.reward}",
        ]

        if self.trace:
            args.append("--trace")
            args.append(f"--output.basedir={temp_dir.name}")
        return args

    def dump_debug_stream(
        self,
        debug_output_path: str,
        temp_dir: tempfile.TemporaryDirectory,
        stdin: Dict[str, Any],
        args: List[str],
        result: subprocess.CompletedProcess,
    ):
        """
        Export debug files if requested when interacting with t8n via streams
        """
        if not debug_output_path:
            return

        t8n_call = " ".join(args)
        t8n_output_base_dir = os.path.join(debug_output_path, "t8n.sh.out")
        if self.trace:
            t8n_call = t8n_call.replace(temp_dir.name, t8n_output_base_dir)
        t8n_script = textwrap.dedent(
            f"""\
            #!/bin/bash
            rm -rf {debug_output_path}/t8n.sh.out  # hard-coded to avoid surprises
            mkdir {debug_output_path}/t8n.sh.out  # unused if tracing is not enabled
            {t8n_call} < {debug_output_path}/stdin.txt
            """
        )
        dump_files_to_directory(
            debug_output_path,
            {
                "args.py": args,
                "input/alloc.json": stdin["alloc"],
                "input/env.json": stdin["env"],
                "input/txs.json": stdin["txs"],
                "returncode.txt": result.returncode,
                "stdin.txt": stdin,
                "stdout.txt": result.stdout.decode(),
                "stderr.txt": result.stderr.decode(),
                "t8n.sh+x": t8n_script,
            },
        )

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
    ) -> Dict[str, Any]:
        """
        Executes the relevant evaluate method as required by the `t8n` tool.

        If a client's `t8n` tool varies from the default behavior, this method
        can be overridden.
        """
        if eips is not None:
            fork_name = "+".join([fork_name] + [str(eip) for eip in eips])
        if int(env["currentNumber"], 0) == 0:
            reward = -1
        t8n_data = TransitionTool.TransitionToolData(
            alloc=alloc, txs=txs, env=env, fork_name=fork_name, chain_id=chain_id, reward=reward
        )

        if self.t8n_use_stream:
            return self._evaluate_stream(t8n_data=t8n_data, debug_output_path=debug_output_path)
        else:
            return self._evaluate_filesystem(
                t8n_data=t8n_data,
                debug_output_path=debug_output_path,
            )

    def verify_fixture(
        self, fixture_format: FixtureFormats, fixture_path: Path, debug_output_path: Optional[Path]
    ):
        """
        Executes `evm [state|block]test` to verify the fixture at `fixture_path`.

        Currently only implemented by geth's evm.
        """
        raise Exception(
            "The `verify_fixture()` function is not supported by this tool. Use geth's evm tool."
        )
