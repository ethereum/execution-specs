"""
Python wrapper for the `evm t8n` tool.
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Tuple


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
        ]
        stdin = {
            "alloc": alloc,
            "txs": txs,
            "env": env,
        }
        result = subprocess.run(
            args, input=str.encode(json.dumps(stdin)), stdout=subprocess.PIPE
        )

        if result.returncode != 0:
            raise Exception("Failed to evaluate: " + str(result.stderr))

        output = json.loads(result.stdout)

        if "alloc" not in output or "result" not in output:
            Exception("Malformed result")

        return (output["alloc"], output["result"])
