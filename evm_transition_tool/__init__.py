"""
Python wrapper for the `evm t8n` tool.
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Optional, Tuple


class TransitionTool:
    """
    Transition tool frontend.
    """

    binary: Path = Path("evm")

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

        result = subprocess.run(
            args,
            input=str.encode(json.dumps(stdin)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if result.returncode != 0:
            raise Exception("failed to evaluate")

        output = json.loads(result.stdout)

        if "alloc" not in output or "result" not in output:
            Exception("malformed result")

        return (output["alloc"], output["result"])

    def calc_state_root(self, env: Any, alloc: Any, fork: str) -> str:
        """
        Calculate the state root for the given `alloc`.
        """
        env = {
            "currentCoinbase": "0x0000000000000000000000000000000000000000",
            "currentDifficulty": "0x0",
            "currentGasLimit": "0x0",
            "currentNumber": "0",
            "currentTimestamp": "0",
            "currentBaseFee": hex(env.base_fee)
            if env.base_fee is not None
            else None,
        }

        (_, result) = self.evaluate(alloc, [], env, fork)
        return result.get("stateRoot")


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


def map_fork(fork: str) -> Optional[str]:
    """
    Map known fork to t8n fork identifier.
    """
    return fork_map.get(fork, fork)
