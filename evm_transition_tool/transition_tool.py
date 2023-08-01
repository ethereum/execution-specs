"""
Transition tool abstract class.
"""

import os
import shutil
from abc import abstractmethod
from itertools import groupby
from json import dump
from pathlib import Path
from re import Pattern
from typing import Any, Dict, List, Optional, Tuple, Type

from ethereum_test_forks import Fork


class UnknownTransitionTool(Exception):
    """Exception raised if an unknown t8n is encountered"""

    pass


class TransitionToolNotFoundInPath(Exception):
    """Exception raised if the specified t8n tool is not found in the path"""

    def __init__(self, message="The transition tool was not found in the path", binary=None):
        if binary:
            message = f"{message} ({binary})"
        super().__init__(message)


def dump_files_to_directory(output_path: str, files: Dict[str, Any]) -> None:
    """
    Dump the files to the given directory.
    """
    os.makedirs(output_path, exist_ok=True)
    for file_name, file_contents in files.items():
        file_path = os.path.join(output_path, file_name)
        with open(file_path, "w") as f:
            dump(file_contents, f, ensure_ascii=True, indent=4)


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
                with os.popen(f"{binary} {version_flag}") as f:
                    binary_output = f.read()
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

    @abstractmethod
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

    def calc_state_root(self, *, alloc: Any, fork: Fork, debug_output_path: str = "") -> bytes:
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

        if fork.header_excess_blob_gas_required(0, 0):
            env["currentExcessBlobGas"] = "0"

        if fork.header_beacon_root_required(0, 0):
            env[
                "beaconRoot"
            ] = "0x0000000000000000000000000000000000000000000000000000000000000000"

        _, result = self.evaluate(
            alloc=alloc,
            txs=[],
            env=env,
            fork_name=fork.fork(block_number=0, timestamp=0),
            debug_output_path=debug_output_path,
        )
        state_root = result.get("stateRoot")
        if state_root is None or not isinstance(state_root, str):
            raise Exception("Unable to calculate state root")
        return bytes.fromhex(state_root[2:])

    def calc_withdrawals_root(
        self, *, withdrawals: Any, fork: Fork, debug_output_path: str = ""
    ) -> bytes:
        """
        Calculate the state root for the given `alloc`.
        """
        if isinstance(withdrawals, list) and len(withdrawals) == 0:
            # Optimize returning the empty root immediately
            return bytes.fromhex(
                "56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
            )

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

        if fork.header_excess_blob_gas_required(0, 0):
            env["currentExcessBlobGas"] = "0"

        if fork.header_beacon_root_required(0, 0):
            env[
                "beaconRoot"
            ] = "0x0000000000000000000000000000000000000000000000000000000000000000"

        _, result = self.evaluate(
            alloc={},
            txs=[],
            env=env,
            fork_name=fork.fork(block_number=0, timestamp=0),
            debug_output_path=debug_output_path,
        )
        withdrawals_root = result.get("withdrawalsRoot")
        if withdrawals_root is None:
            raise Exception(
                "Unable to calculate withdrawals root: no value returned from transition tool"
            )
        if not isinstance(withdrawals_root, str):
            raise Exception(
                "Unable to calculate withdrawals root: "
                + "incorrect type returned from transition tool: "
                + f"{withdrawals_root}"
            )
        return bytes.fromhex(withdrawals_root[2:])
