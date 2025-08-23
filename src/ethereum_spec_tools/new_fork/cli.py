"""
Command-line interface to `ForkBuilder`.
"""

from argparse import ArgumentParser
from pathlib import Path
from typing import Sequence

from ethereum_types.numeric import U64, Uint

from ethereum.fork_criteria import ByBlockNumber, ByTimestamp, Unscheduled

from ..forks import Hardfork
from .builder import ForkBuilder, SetConstant


def _make_parser() -> ArgumentParser:
    forks = Hardfork.discover()
    fork_short_names = [f.short_name for f in forks]

    parser = ArgumentParser(
        # TODO: Description / help text
    )

    parser.add_argument(
        "--template-fork",
        "--from_fork",
        dest="template_fork",
        type=str,
        choices=fork_short_names,
        metavar="NAME",
        help="short name of the fork to use as a template",
        default=fork_short_names[-1],
    )

    parser.add_argument(
        "--new-fork",
        "--to_fork",
        dest="new_fork",
        type=str,
        required=True,
        metavar="NAME",
        help="short name (Python-friendly) of the new fork",
    )

    parser.add_argument(
        "--output",
        "-o",
        dest="output",
        type=Path,
        metavar="PATH",
        help="directory in which to place the generated fork",
    )

    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="overwrite the destination if it already exists",
        default=False,
    )

    fork_criteria = parser.add_mutually_exclusive_group()

    fork_criteria.add_argument(
        "--unscheduled",
        action="store_const",
        const=Unscheduled(),
        dest="fork_criteria",
        help="mark the new fork as unscheduled",
    )

    fork_criteria.add_argument(
        "--at-timestamp",
        type=lambda x: ByTimestamp(int(x)),
        dest="fork_criteria",
        help="mark the new fork as beginning at the given time",
    )

    fork_criteria.add_argument(
        "--at-block",
        type=lambda x: ByBlockNumber(int(x)),
        dest="fork_criteria",
        help="mark the new fork as beginning at the given block number",
    )

    blob_parameters = parser.add_argument_group()

    blob_parameters.add_argument(
        "--target-blob-gas-per-block",
        type=lambda x: U64(int(x)),
        dest="target_blob_gas_per_block",
        default=None,
        help="Set `TARGET_BLOB_GAS_PER_BLOCK` in the generated fork",
    )

    blob_parameters.add_argument(
        "--gas-per-blob",
        type=lambda x: U64(int(x)),
        dest="gas_per_blob",
        default=None,
        help="Set `GAS_PER_BLOB` in the generated fork",
    )

    blob_parameters.add_argument(
        "--min-blob-gasprice",
        type=lambda x: Uint(int(x)),
        dest="min_blob_gasprice",
        default=None,
        help="Set `MIN_BLOB_GASPRICE` in the generated fork",
    )

    blob_parameters.add_argument(
        "--blob-base-fee-update-fraction",
        type=lambda x: Uint(int(x)),
        dest="blob_base_fee_update_fraction",
        default=None,
        help="Set `BLOB_BASE_FEE_UPDATE_FRACTION` in the generated fork",
    )

    blob_parameters.add_argument(
        "--max-blob-gas-per-block",
        type=lambda x: U64(int(x)),
        dest="max_blob_gas_per_block",
        default=None,
        help="Set `MAX_BLOB_GAS_PER_BLOCK` in the generated fork",
    )

    blob_parameters.add_argument(
        "--blob-schedule-target",
        type=lambda x: U64(int(x)),
        dest="blob_schedule_target",
        default=None,
        help="Set `BLOB_SCHEDULE_TARGET` in the generated fork",
    )

    return parser


def main(args: Sequence[str] | None = None) -> None:
    """
    Command-line entry point into `ForkBuilder`.
    """
    parser = _make_parser()
    options = parser.parse_args(args)

    if options.template_fork == "spurious_dragon":
        raise NotImplementedError(
            "An instance of 'Spurious Dragon' in a comment will get "
            "incorrectly replaced; use another fork as the template."
        )

    builder = ForkBuilder(options.template_fork, options.new_fork)

    if options.output is not None:
        assert isinstance(options.output, Path)
        builder.output = options.output

    builder.force = options.force

    if options.fork_criteria is not None:
        builder.fork_criteria = options.fork_criteria

    if options.target_blob_gas_per_block is not None:
        builder.modifiers.append(
            SetConstant(
                "vm.gas.TARGET_BLOB_GAS_PER_BLOCK",
                repr(options.target_blob_gas_per_block),
            )
        )

    if options.gas_per_blob is not None:
        builder.modifiers.append(
            SetConstant(
                "vm.gas.GAS_PER_BLOB",
                repr(options.gas_per_blob),
            )
        )

    if options.min_blob_gasprice is not None:
        builder.modifiers.append(
            SetConstant(
                "vm.gas.MIN_BLOB_GASPRICE",
                repr(options.min_blob_gasprice),
            )
        )

    if options.blob_base_fee_update_fraction is not None:
        builder.modifiers.append(
            SetConstant(
                "vm.gas.BLOB_BASE_FEE_UPDATE_FRACTION",
                repr(options.blob_base_fee_update_fraction),
            )
        )

    if options.max_blob_gas_per_block is not None:
        builder.modifiers.append(
            SetConstant(
                "fork.MAX_BLOB_GAS_PER_BLOCK",
                repr(options.max_blob_gas_per_block),
            )
        )

    if options.blob_schedule_target is not None:
        builder.modifiers.append(
            SetConstant(
                "vm.gas.BLOB_SCHEDULE_TARGET",
                repr(options.blob_schedule_target),
            )
        )

    builder.build()


if __name__ == "__main__":
    main()
