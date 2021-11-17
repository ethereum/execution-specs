"""
Python wrapper for the `evm t8n` tool.
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Tuple

from ethereum.crypto import Hash32


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
            "--state.fork=London",
        ]
        stdin = {
            "alloc": alloc,
            "txs": txs,
            "env": env,
        }
        print(str(json.dumps(stdin)))
        result = subprocess.run(
            args, input=str.encode(json.dumps(stdin)), stdout=subprocess.PIPE
        )

        if result.returncode != 0:
            raise Exception("Failed to evaluate: " + str(result.stderr))

        output = json.loads(result.stdout)

        if "alloc" not in output or "result" not in output:
            Exception("Malformed result")

        return (output["alloc"], output["result"])

    def calc_state_root(self, alloc: Any) -> Hash32:
        """
        Calculate the state root for the given `alloc`.
        """
        env = {
            "currentCoinbase": "0x0000000000000000000000000000000000000000",
            "currentDifficulty": "0x00",
            "currentGasLimit": "0x00",
            "currentNumber": "0",
            "currentTimestamp": "0",
        }
        (_, result) = self.evaluate(alloc, [], env)
        return result.get("stateRoot")
