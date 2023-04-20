"""
Python wrapper for the `evm t8n` tool.
"""

import json
import os
import subprocess
import tempfile
from abc import abstractmethod
from pathlib import Path
from shutil import which
from typing import Any, Dict, List, Optional, Tuple

from ethereum_test_forks import Fork


class TransitionTool:
    """
    Transition tool frontend.
    """

    traces: List[List[List[Dict]]] | None = None

    @abstractmethod
    def evaluate(
        self,
        alloc: Any,
        txs: Any,
        env: Any,
        fork: Fork,
        chain_id: int = 1,
        reward: int = 0,
        eips: Optional[List[int]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
        """
        Simulate a state transition with specified parameters
        """
        pass

    @abstractmethod
    def version(self) -> str:
        """
        Return name and version of tool used to state transition
        """
        pass

    @abstractmethod
    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Returns True if the fork is supported by the tool
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

    def calc_state_root(self, alloc: Any, fork: Fork) -> str:
        """
        Calculate the state root for the given `alloc`.
        """
        env: Dict[str, Any] = {
            "currentCoinbase": "0x0000000000000000000000000000000000000000",
            "currentDifficulty": "0x0",
            "currentGasLimit": "0x0",
            "currentNumber": "0",
            "currentTimestamp": "0",
        }

        if fork.header_base_fee_required(0, 0):
            env["currentBaseFee"] = "7"

        if fork.header_prev_randao_required(0, 0):
            env["currentRandom"] = "0"

        if fork.header_withdrawals_required(0, 0):
            env["withdrawals"] = []

        (_, result, _) = self.evaluate(alloc, [], env, fork)
        state_root = result.get("stateRoot")
        if state_root is None or not isinstance(state_root, str):
            raise Exception("Unable to calculate state root")
        return state_root

    def calc_withdrawals_root(self, withdrawals: Any, fork: Fork) -> str:
        """
        Calculate the state root for the given `alloc`.
        """
        if type(withdrawals) is list and len(withdrawals) == 0:
            # Optimize returning the empty root immediately
            return "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"  # noqa: E501

        env: Dict[str, Any] = {
            "currentCoinbase": "0x0000000000000000000000000000000000000000",
            "currentDifficulty": "0x0",
            "currentGasLimit": "0x0",
            "currentNumber": "0",
            "currentTimestamp": "0",
            "withdrawals": withdrawals,
        }

        if fork.header_base_fee_required(0, 0):
            env["currentBaseFee"] = "7"

        if fork.header_prev_randao_required(0, 0):
            env["currentRandom"] = "0"

        if fork.header_excess_data_gas_required(0, 0):
            env["currentExcessDataGas"] = "0"

        (_, result, _) = self.evaluate({}, [], env, fork)
        withdrawals_root = result.get("withdrawalsRoot")
        if withdrawals_root is None:
            raise Exception(
                "Unable to calculate withdrawals root: "
                + "no value returned from transition tool"
            )
        if type(withdrawals_root) is not str:
            raise Exception(
                "Unable to calculate withdrawals root: "
                + "incorrect type returned from transition tool: "
                + f"{withdrawals_root}"
            )
        return withdrawals_root


class EvmTransitionTool(TransitionTool):
    """
    Go-ethereum `evm` Transition tool frontend.
    """

    binary: Path
    cached_version: Optional[str] = None
    trace: bool

    def __init__(
        self,
        binary: Optional[Path] = None,
        trace: bool = False,
    ):
        if binary is None:
            which_path = which("evm")
            if which_path is not None:
                binary = Path(which_path)
        if binary is None or not binary.exists():
            raise Exception(
                """`evm` binary executable is not accessible, please refer to
                https://github.com/ethereum/go-ethereum on how to compile and
                install the full suite of utilities including the `evm` tool"""
            )
        self.binary = binary
        self.trace = trace

    def evaluate(
        self,
        alloc: Any,
        txs: Any,
        env: Any,
        fork: Fork,
        chain_id: int = 1,
        reward: int = 0,
        eips: Optional[List[int]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
        """
        Executes `evm t8n` with the specified arguments.
        """
        fork_name = fork.name()
        if eips is not None:
            fork_name = "+".join([fork_name] + [str(eip) for eip in eips])

        temp_dir = tempfile.TemporaryDirectory()

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

        if result.returncode != 0:
            raise Exception("failed to evaluate: " + result.stderr.decode())

        output = json.loads(result.stdout)

        if "alloc" not in output or "result" not in output:
            raise Exception("malformed result")

        with open(os.path.join(temp_dir.name, "txs.rlp"), "r") as txs_rlp_file:
            txs_rlp = txs_rlp_file.read().strip('"')

        if self.trace:
            receipts: List[Any] = output["result"]["receipts"]
            traces: List[List[Dict]] = []
            for i, r in enumerate(receipts):
                h = r["transactionHash"]
                trace_file_name = f"trace-{i}-{h}.jsonl"
                with open(
                    os.path.join(temp_dir.name, trace_file_name), "r"
                ) as trace_file:
                    tx_traces: List[Dict] = []
                    for trace_line in trace_file.readlines():
                        tx_traces.append(json.loads(trace_line))
                    traces.append(tx_traces)
            self.append_traces(traces)

        temp_dir.cleanup()

        return (output["alloc"], output["result"], txs_rlp)

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
                raise Exception(
                    "failed to evaluate: " + result.stderr.decode()
                )

            self.cached_version = result.stdout.decode().strip()

        return self.cached_version

    def is_fork_supported(self, _: Fork) -> bool:
        """
        Returns True if the fork is supported by the tool
        """
        return True
