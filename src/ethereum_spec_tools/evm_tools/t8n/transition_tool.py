from ethereum_clis import TransitionTool
from ethereum_clis.clis.execution_specs import ExecutionSpecsExceptionMapper
from ethereum_clis.transition_tool import model_dump_config
import ethereum
import tempfile

from . import T8N
from .. import create_parser
from io import StringIO, TextIOWrapper
import json
from ethereum_clis.types import TransitionToolOutput
from ethereum_clis.file_utils import dump_files_to_directory

class ExecutionSpecsWrapper(TransitionTool):
    t8n_use_eels: bool = True
    detect_binary_pattern = ""

    def __init__(
            self,
            *,
            trace: bool = False,
        ):
        """Initialize the EELS Transition Tool interface."""
        super().__init__(
            exception_mapper=ExecutionSpecsExceptionMapper(), trace=trace
        )

    def version(self):
        return ethereum.__version__

    def _evaluate_custom_t8n(self, t8n_data, debug_output_path):
        request_data = t8n_data.get_request_data()
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

        if t8n_data.state_test:
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

