"""
Transition tool abstract class.
"""

import json
import os
import shutil
import subprocess
import tempfile
import textwrap
import time
from abc import abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Type

from requests import Response
from requests.exceptions import ConnectionError
from requests_unixsocket import Session  # type: ignore

from ethereum_test_exceptions import ExceptionMapper
from ethereum_test_fixtures import FixtureFormat, FixtureVerifier
from ethereum_test_forks import Fork
from ethereum_test_types import Alloc, Environment, Transaction

from .ethereum_cli import EthereumCLI
from .file_utils import dump_files_to_directory, write_json_file
from .types import TransactionReceipt, TransitionToolInput, TransitionToolOutput

model_dump_config: Mapping = {"by_alias": True, "exclude_none": True}


class TransitionTool(EthereumCLI, FixtureVerifier):
    """
    Transition tool abstract base class which should be inherited by all transition tool
    implementations.
    """

    traces: List[List[List[Dict]]] | None = None

    registered_tools: List[Type["TransitionTool"]] = []
    default_tool: Optional[Type["TransitionTool"]] = None

    t8n_subcommand: Optional[str] = None
    statetest_subcommand: Optional[str] = None
    blocktest_subcommand: Optional[str] = None
    cached_version: Optional[str] = None
    t8n_use_stream: bool = False

    t8n_use_server: bool = False
    server_url: str
    process: Optional[subprocess.Popen] = None

    @abstractmethod
    def __init__(
        self,
        *,
        exception_mapper: ExceptionMapper,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        """
        Abstract initialization method that all subclasses must implement.
        """
        self.exception_mapper = exception_mapper
        super().__init__(binary=binary)
        self.trace = trace

    def __init_subclass__(cls):
        """
        Registers all subclasses of TransitionTool as possible tools.
        """
        TransitionTool.register_tool(cls)

    @abstractmethod
    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Returns True if the fork is supported by the tool
        """
        pass

    def start_server(self):
        """
        Starts the t8n-server process, extracts the port, and leaves it running for future re-use.
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
        receipts: List[TransactionReceipt],
        temp_dir: tempfile.TemporaryDirectory,
        debug_output_path: str = "",
    ) -> None:
        """
        Collect the traces from the t8n tool output and store them in the traces list.
        """
        traces: List[List[Dict]] = []
        for i, r in enumerate(receipts):
            trace_file_name = f"trace-{i}-{r.transaction_hash}.jsonl"
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

        alloc: Alloc
        txs: List[Transaction]
        env: Environment
        fork_name: str
        chain_id: int = field(default=1)
        reward: int = field(default=0)

        def to_input(self) -> TransitionToolInput:
            """
            Convert the data to a TransactionToolInput object
            """
            return TransitionToolInput(
                alloc=self.alloc,
                txs=self.txs,
                env=self.env,
            )

    def _evaluate_filesystem(
        self,
        *,
        t8n_data: TransitionToolData,
        debug_output_path: str = "",
    ) -> TransitionToolOutput:
        """
        Executes a transition tool using the filesystem for its inputs and outputs.
        """
        temp_dir = tempfile.TemporaryDirectory()
        os.mkdir(os.path.join(temp_dir.name, "input"))
        os.mkdir(os.path.join(temp_dir.name, "output"))

        input_contents = t8n_data.to_input().model_dump(mode="json", **model_dump_config)

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
        output = TransitionToolOutput(**output_contents)
        if self.trace:
            self.collect_traces(output.result.receipts, temp_dir, debug_output_path)

        temp_dir.cleanup()

        return output

    def _server_post(self, data: Dict[str, Any], retries: int = 10) -> Response:
        """
        Send a POST request to the t8n-server and return the response.
        """
        post_delay = 0.1
        while True:
            try:
                response = Session().post(self.server_url, json=data, timeout=20)
                break
            except ConnectionError as e:
                retries -= 1
                if retries == 0:
                    raise e
                time.sleep(post_delay)
                post_delay *= 2
        response.raise_for_status()
        if response.status_code != 200:
            raise Exception(
                f"t8n-server returned status code {response.status_code}, "
                f"response: {response.text}"
            )
        return response

    def _evaluate_server(
        self,
        *,
        t8n_data: TransitionToolData,
        debug_output_path: str = "",
    ) -> TransitionToolOutput:
        """
        Executes the transition tool sending inputs and outputs via a server.
        """
        input_contents = t8n_data.to_input()
        input_json = input_contents.model_dump(mode="json", **model_dump_config)
        post_data = {
            "state": {
                "fork": t8n_data.fork_name,
                "chainid": t8n_data.chain_id,
                "reward": t8n_data.reward,
            },
            "input": input_json,
        }

        if debug_output_path:
            request_info = (
                f"Server URL: {self.server_url}\n\n"
                f"Request Data:\n{json.dumps(post_data, indent=2)}\n"
            )
            dump_files_to_directory(
                debug_output_path,
                {
                    "input/alloc.json": input_contents.alloc,
                    "input/env.json": input_contents.env,
                    "input/txs.json": [
                        tx.model_dump(mode="json", **model_dump_config)
                        for tx in input_contents.txs
                    ],
                    "request_info.txt": request_info,
                },
            )

        response = self._server_post(post_data)
        output: TransitionToolOutput = TransitionToolOutput.model_validate(response.json())

        if debug_output_path:
            response_info = (
                f"Status Code: {response.status_code}\n\n"
                f"Headers:\n{json.dumps(dict(response.headers), indent=2)}\n\n"
                f"Content:\n{response.text}\n"
            )
            dump_files_to_directory(
                debug_output_path,
                {
                    "output/alloc.json": output.alloc,
                    "output/result.json": output.result,
                    "output/txs.rlp": str(output.body),
                    "response_info.txt": response_info,
                },
            )

        return output

    def _evaluate_stream(
        self,
        *,
        t8n_data: TransitionToolData,
        debug_output_path: str = "",
    ) -> TransitionToolOutput:
        """
        Executes a transition tool using stdin and stdout for its inputs and outputs.
        """
        temp_dir = tempfile.TemporaryDirectory()
        args = self.construct_args_stream(t8n_data, temp_dir)

        stdin = t8n_data.to_input()

        result = subprocess.run(
            args,
            input=stdin.model_dump_json(**model_dump_config).encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.dump_debug_stream(debug_output_path, temp_dir, stdin, args, result)

        if result.returncode != 0:
            raise Exception("failed to evaluate: " + result.stderr.decode())

        output: TransitionToolOutput = TransitionToolOutput.model_validate_json(result.stdout)

        if debug_output_path:
            dump_files_to_directory(
                debug_output_path,
                {
                    "output/alloc.json": output.alloc,
                    "output/result.json": output.result,
                    "output/txs.rlp": str(output.body),
                },
            )

        if self.trace:
            self.collect_traces(output.result.receipts, temp_dir, debug_output_path)
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
        stdin: TransitionToolInput,
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
                "input/alloc.json": stdin.alloc,
                "input/env.json": stdin.env,
                "input/txs.json": [
                    tx.model_dump(mode="json", **model_dump_config) for tx in stdin.txs
                ],
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
        alloc: Alloc,
        txs: List[Transaction],
        env: Environment,
        fork: Fork,
        chain_id: int = 1,
        reward: int = 0,
        eips: Optional[List[int]] = None,
        debug_output_path: str = "",
    ) -> TransitionToolOutput:
        """
        Executes the relevant evaluate method as required by the `t8n` tool.

        If a client's `t8n` tool varies from the default behavior, this method
        can be overridden.
        """
        fork_name = fork.transition_tool_name(
            block_number=env.number,
            timestamp=env.timestamp,
        )
        if eips is not None:
            fork_name = "+".join([fork_name] + [str(eip) for eip in eips])
        if env.number == 0:
            reward = -1
        t8n_data = self.TransitionToolData(
            alloc=alloc,
            txs=txs,
            env=env,
            fork_name=fork_name,
            chain_id=chain_id,
            reward=reward,
        )

        if self.t8n_use_server:
            if not self.process:
                self.start_server()
            return self._evaluate_server(t8n_data=t8n_data, debug_output_path=debug_output_path)

        if self.t8n_use_stream:
            return self._evaluate_stream(t8n_data=t8n_data, debug_output_path=debug_output_path)

        return self._evaluate_filesystem(
            t8n_data=t8n_data,
            debug_output_path=debug_output_path,
        )

    def verify_fixture(
        self,
        fixture_format: FixtureFormat,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ):
        """
        Executes `evm [state|block]test` to verify the fixture at `fixture_path`.

        Currently only implemented by geth's evm.
        """
        raise NotImplementedError(
            "The `verify_fixture()` function is not supported by this tool. Use geth's evm tool."
        )
