"""
Implementation of the EELS T8N for execution-spec-tests.
"""

import json
import tempfile
from io import StringIO
from typing import Any, Dict, Optional

from ethereum_clis.clis.execution_specs import ExecutionSpecsExceptionMapper
from ethereum_clis.file_utils import dump_files_to_directory
from ethereum_clis.transition_tool import TransitionTool, model_dump_config
from ethereum_clis.types import TransitionToolOutput
from ethereum_test_forks import Fork

import ethereum

from .. import create_parser
from ..utils import get_supported_forks
from . import T8N


class EELST8N(TransitionTool):
    """Implementation of the EELS T8N for execution-spec-tests."""

    def __init__(
        self,
        *,
        trace: bool = False,
    ):
        """Initialize the EELS Transition Tool interface."""
        self.exception_mapper = ExecutionSpecsExceptionMapper()
        self.trace = trace
        self._info_metadata: Optional[Dict[str, Any]] = {}

    def version(self) -> str:
        """Version of the t8n tool."""
        return ethereum.__version__

    def is_fork_supported(self, fork: Fork) -> bool:
        """Return True if the fork is supported by the tool."""
        return fork.transition_tool_name() in get_supported_forks()

    def evaluate(
        self,
        *,
        transition_tool_data: TransitionTool.TransitionToolData,
        debug_output_path: str = "",
        slow_request: bool = False,  # noqa: U100, F841
    ) -> TransitionToolOutput:
        """
        Evaluate using the EELS T8N entry point.
        """
        request_data = transition_tool_data.get_request_data()
        request_data_json = request_data.model_dump(mode="json", **model_dump_config)

        t8n_args = [
            "t8n",
            "--input.alloc=stdin",
            "--input.env=stdin",
            "--input.txs=stdin",
            "--output.result=stdout",
            "--output.body=stdout",
            "--output.alloc=stdout",
            f"--state.fork={request_data_json['state']['fork']}",
            f"--state.chainid={request_data_json['state']['chainid']}",
            f"--state.reward={request_data_json['state']['reward']}",
        ]

        if transition_tool_data.state_test:
            t8n_args.append("--state-test")

        temp_dir = tempfile.TemporaryDirectory()
        if self.trace:
            t8n_args.extend(
                [
                    "--trace",
                    "--trace.memory",
                    "--trace.returndata",
                    f"--output.basedir={temp_dir.name}",
                ]
            )

        parser = create_parser()
        t8n_options = parser.parse_args(t8n_args)

        out_stream = StringIO()

        in_stream = StringIO(json.dumps(request_data_json["input"]))

        t8n = T8N(t8n_options, out_stream, in_stream)
        t8n.run()

        output_dict = json.loads(out_stream.getvalue())
        output: TransitionToolOutput = TransitionToolOutput.model_validate(
            output_dict, context={"exception_mapper": self.exception_mapper}
        )

        if debug_output_path:
            dump_files_to_directory(
                debug_output_path,
                {
                    "input/alloc.json": request_data.input.alloc,
                    "input/env.json": request_data.input.env,
                    "input/txs.json": [
                        tx.model_dump(mode="json", **model_dump_config)
                        for tx in request_data.input.txs
                    ],
                },
            )

            dump_files_to_directory(
                debug_output_path,
                {
                    "output/alloc.json": output.alloc,
                    "output/result.json": output.result,
                },
            )

        if self.trace:
            self.collect_traces(output.result.receipts, temp_dir, debug_output_path)
        temp_dir.cleanup()

        return output
