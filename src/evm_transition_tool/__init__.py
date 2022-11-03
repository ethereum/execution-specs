"""
Python wrapper for the `evm t8n` tool.
"""

import json
import subprocess
from abc import abstractmethod
from pathlib import Path
from shutil import which
from typing import Any, Optional, Tuple


class TransitionTool:
    """
    Transition tool frontend.
    """

    @abstractmethod
    def evaluate(
        self,
        alloc: Any,
        txs: Any,
        env: Any,
        fork: str,
        chain_id: int = 1,
        reward: int = 0,
        txsPath: Optional[str] = None,
    ) -> Tuple[Any, Any]:
        pass

    @abstractmethod
    def calc_state_root(self, env: Any, alloc: Any, fork: str) -> str:
        pass

    @abstractmethod
    def version(self) -> str:
        pass


class EvmTransitionTool(TransitionTool):
    """
    Go-ethereum `evm` Transition tool frontend.
    """

    binary: Path
    cached_version: Optional[str] = None

    def __init__(self, binary: Optional[Path] = None):
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

    def evaluate(
        self,
        alloc: Any,
        txs: Any,
        env: Any,
        fork: str,
        chain_id: int = 1,
        reward: int = 0,
        txsPath: Optional[str] = None,
    ) -> Tuple[Any, Any]:
        """
        Executes `evm t8n` with the specified arguments.
        """
        args = [
            str(self.binary),
            "t8n",
            "--input.alloc=stdin",
            "--input.txs=stdin",
            "--input.env=stdin",
            "--output.result=stdout",
            "--output.alloc=stdout",
            f"--state.fork={fork}",
            f"--state.chainid={chain_id}",
            f"--state.reward={reward}",
        ]

        if txsPath is not None:
            args.append(f"--output.body={txsPath}")

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
            Exception("malformed result")

        return (output["alloc"], output["result"])

    def calc_state_root(self, env: Any, alloc: Any, fork: str) -> str:
        """
        Calculate the state root for the given `alloc`.
        """
        base_fee = env.base_fee
        env = {
            "currentCoinbase": "0x0000000000000000000000000000000000000000",
            "currentDifficulty": "0x0",
            "currentGasLimit": "0x0",
            "currentNumber": "0",
            "currentTimestamp": "0",
        }
        if base_fee is not None:
            env["currentBaseFee"] = str(base_fee)
        elif base_fee_required(fork):
            env["currentBaseFee"] = "7"

        (_, result) = self.evaluate(alloc, [], env, fork)
        return result.get("stateRoot")

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


fork_map = {
    "frontier": "Frontier",
    "homestead": "Homestead",
    "dao": None,
    "tangerine whistle": "EIP150",
    "spurious dragon": "EIP158",
    "byzantium": "Byzantium",
    "constantinople": "Constantinople",
    "petersburg": "ConstantinopleFix",
    "istanbul": "Istanbul",
    "muir glacier": None,
    "berlin": "Berlin",
    "london": "London",
    "arrow glacier": "ArrowGlacier",
}

fork_list = list(fork_map.keys())


def base_fee_required(fork: str) -> bool:
    """
    Return true if the fork requires baseFee in the block.
    """
    return fork_list.index(fork.lower()) >= fork_list.index("london")


def map_fork(fork: str) -> Optional[str]:
    """
    Map known fork to t8n fork identifier.
    """
    return fork_map.get(fork, fork)
