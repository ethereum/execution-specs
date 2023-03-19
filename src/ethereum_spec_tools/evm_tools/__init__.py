"""
Defines EVM tools for use in the Ethereum specification.
"""

import argparse

from .t8n import T8N

# TODO: Add verbose description
DESCRIPTION = """
This is the EVM tool for execution specs.
You can use this to run the following tools:
    1. t8n: A stateless state transition utility.
"""

parser = argparse.ArgumentParser(
    description=DESCRIPTION,
    formatter_class=argparse.RawDescriptionHelpFormatter,
)


# Add options to the t8n tool
subparsers = parser.add_subparsers(dest="subparser_name")

t8n_parser = subparsers.add_parser("t8n", help="This is the t8n tool.")
t8n_parser.add_argument(
    "--input.alloc", dest="input_alloc", type=str, default="alloc.json"
)
t8n_parser.add_argument(
    "--input.env", dest="input_env", type=str, default="env.json"
)
t8n_parser.add_argument(
    "--input.txs", dest="input_txs", type=str, default="txs.json"
)
t8n_parser.add_argument(
    "--output.alloc", dest="output_alloc", type=str, default="alloc.json"
)
t8n_parser.add_argument("--output.basedir", dest="output_basedir", type=str)
t8n_parser.add_argument("--output.body", dest="output_body", type=str)
t8n_parser.add_argument(
    "--output.result", dest="output_result", type=str, default="result.json"
)
t8n_parser.add_argument(
    "--state.chainid", dest="state_chainid", type=int, default=1
)
# TODO: Check if transition forks can be supported
# Also check for Fork+EIP combinations. (E.g. Homestead+EIP-150)
t8n_parser.add_argument(
    "--state.fork", dest="state_fork", type=str, default="Frontier"
)
t8n_parser.add_argument(
    "--state.reward", dest="state_reward", type=int, default=0
)
# TODO: Add support for the following trace options
t8n_parser.add_argument(
    "--trace.memory", dest="trace_memory", type=bool, default=False
)
t8n_parser.add_argument(
    "--trace.nomemory", dest="trace_nomemory", type=bool, default=True
)
t8n_parser.add_argument(
    "--trace.noreturndata", dest="trace_noreturndata", type=bool, default=True
)
t8n_parser.add_argument(
    "--trace.nostack ", dest="trace_nostack ", type=bool, default=False
)
t8n_parser.add_argument(
    "--trace.returndata", dest="trace_returndata", type=bool, default=False
)


def main() -> int:
    """Run the tools based on the given options."""
    options = parser.parse_args()
    if options.subparser_name == "t8n":
        t8n_tool = T8N(options)
        return t8n_tool.run()
    else:
        # TODO: Add support for b11r tool
        parser.print_help()
        return 0
