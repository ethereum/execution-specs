"""
Generate a JSON blockchain test from an existing JSON blockchain test by wrapping its pre-state
code in EOF wherever possible.

Example Usage:

1. Wrap tests

    ```console
    eofwrap <input_dir/file_path> <output_dir_path>
    ```
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, no_type_check

import click

from cli.evm_bytes import OpcodeWithOperands, process_evm_bytes
from ethereum_clis import CLINotFoundInPathError
from ethereum_clis.clis.evmone import EvmOneTransitionTool
from ethereum_test_base_types import Bytes, EthereumTestRootModel
from ethereum_test_base_types.conversions import to_hex
from ethereum_test_fixtures.blockchain import FixtureBlock, InvalidFixtureBlock
from ethereum_test_fixtures.file import Fixtures
from ethereum_test_forks.forks.forks import EOFv1
from ethereum_test_specs.blockchain import Block, BlockchainFixture, BlockchainTest
from ethereum_test_specs.debugging import print_traces
from ethereum_test_specs.eof import EOFParse
from ethereum_test_tools import Opcodes as Op
from ethereum_test_types import Transaction
from ethereum_test_types.block_types import Environment
from ethereum_test_types.eof.v1 import Container
from ethereum_test_vm.bytecode import Bytecode


@click.command()
@click.argument("input_path", type=click.Path(exists=True, dir_okay=True, file_okay=True))
@click.argument("output_dir", type=click.Path(dir_okay=True, file_okay=False))
@click.option("--traces", is_flag=True, type=bool)
def eof_wrap(input_path: str, output_dir: str, traces: bool):
    """
    Wrap JSON blockchain test file(s) found at `input_path` and
    outputs them to the `output_dir`.
    """
    eof_wrapper = EofWrapper()

    try:
        EvmOneTransitionTool()
    except CLINotFoundInPathError:
        print(f"Error: {EvmOneTransitionTool.default_binary} must be in the PATH.")
        sys.exit(1)
    except Exception as e:
        raise Exception(f"Unexpected exception: {e}") from e

    if os.path.isfile(input_path):
        file = os.path.basename(input_path)
        out_file = "eof_wrapped_" + file
        out_path = os.path.join(output_dir, out_file)

        eof_wrapper.wrap_file(input_path, out_path, traces)
    else:
        for subdir, _, files in os.walk(input_path):
            for file in files:
                rel_dir = Path(subdir).relative_to(input_path)
                out_file = "eof_wrapped_" + file
                out_path = os.path.join(output_dir, rel_dir, out_file)
                in_path = os.path.join(subdir, file)

                eof_wrapper.wrap_file(in_path, out_path, traces)

    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "metrics.json"), "w") as f:
        json.dump(eof_wrapper.metrics, f, indent=4)


class BlockchainFixtures(EthereumTestRootModel):
    """
    Class needed due to some of the `ethereum/tests` fixtures not having the
    `_info.fixture_format` field in the JSON files.
    """

    root: Dict[str, BlockchainFixture]


class EofWrapper:
    """EOF wrapping of blockchain tests with some simple metrics tracking."""

    # JSON files had at least one fixture generated successfully with EOF
    FILES_GENERATED = "files_generated"
    # JSON files skipped explicitly or didn't have a fixture with EOF
    FILES_SKIPPED = "files_skipped"
    # Test fixtures with at least one EOF code and generated successfully
    FIXTURES_GENERATED = "fixtures_generated"
    # Test fixtures with no code able to be EOF-wrapped
    FIXTURES_CANT_WRAP = "fixtures_cant_wrap"
    # Test fixtures with EOF code but test doesn't pass and generation fails
    FIXTURES_CANT_GENERATE = "fixtures_cant_generate"
    # Invalid blocks in fixtures skipped
    INVALID_BLOCKS_SKIPPED = "invalid_blocks_skipped"
    # State accounts with code wrapped into valid EOF
    ACCOUNTS_WRAPPED = "accounts_wrapped"
    # State accounts with code wrapped into valid unique EOF
    UNIQUE_ACCOUNTS_WRAPPED = "unique_accounts_wrapped"
    # State accounts wrapped but the code is not valid EOF
    ACCOUNTS_INVALID_EOF = "accounts_invalid_eof"
    # State accounts wrapped into valid EOF but in a fixture of a failing test
    ACCOUNTS_CANT_GENERATE = "accounts_cant_generate"
    # Breakdown of EOF validation errors summing up to `accounts_invalid_eof`
    VALIDATION_ERRORS = "validation_errors"
    # Breakdown of runtime test failures summing up to `fixtures_cant_generate`
    GENERATION_ERRORS = "generation_errors"

    def __init__(self):
        """Initialize the EofWrapper with metrics tracking and a unique EOF set."""
        self.metrics = {
            self.FILES_GENERATED: 0,
            self.FILES_SKIPPED: 0,
            self.FIXTURES_GENERATED: 0,
            self.FIXTURES_CANT_WRAP: 0,
            self.FIXTURES_CANT_GENERATE: 0,
            self.INVALID_BLOCKS_SKIPPED: 0,
            self.ACCOUNTS_WRAPPED: 0,
            self.UNIQUE_ACCOUNTS_WRAPPED: 0,
            self.ACCOUNTS_INVALID_EOF: 0,
            self.ACCOUNTS_CANT_GENERATE: 0,
            self.VALIDATION_ERRORS: {},
            self.GENERATION_ERRORS: {},
        }
        self.unique_eof = set()

    file_skip_list = [
        "Pyspecs",
        # EXTCODE* opcodes return different results for EOF targets and that is tested elsewhere
        "stExtCodeHash",
        # bigint syntax
        "ValueOverflowParis",
        "bc4895-withdrawals",
        # EOF opcodes at diff places - tests obsolete
        "opcD0DiffPlaces",
        "opcD1DiffPlaces",
        "opcD2DiffPlaces",
        "opcD3DiffPlaces",
        "opcE0DiffPlaces",
        "opcE1DiffPlaces",
        "opcE2DiffPlaces",
        "opcE3DiffPlaces",
        "opcE4DiffPlaces",
        "opcE5DiffPlaces",
        "opcE6DiffPlaces",
        "opcE7DiffPlaces",
        "opcE8DiffPlaces",
        "opcECDiffPlaces",
        "opcEEDiffPlaces",
        "opcF7DiffPlaces",
        "opcF8DiffPlaces",
        "opcF9DiffPlaces",
        "opcFBDiffPlaces",
        # stack overflow always (limit of `max_stack_height` is 1023!)
        "push0_fill_stack",
        "push0_stack_overflow",
        "blobbasefee_stack_overflow",
    ]

    def wrap_file(self, in_path: str, out_path: str, traces: bool):
        """
        Wrap code from a blockchain test JSON file from `in_path` into EOF containers,
        wherever possible. If not possible - skips and tracks that in metrics. Possible means
        at least one account's code can be wrapped in a valid EOF container and the assertions
        on post state are satisfied.
        """
        for skip in self.file_skip_list:
            if skip in in_path:
                self.metrics[self.FILES_SKIPPED] += 1
                return

        fixtures: BlockchainFixtures = BlockchainFixtures.model_validate_json(
            Path(in_path).read_text()
        )

        out_fixtures = Fixtures({})
        fixture: BlockchainFixture
        for fixture_id, fixture in fixtures.root.items():
            fixture_eof_codes = []
            wrapped_at_least_one_account = False

            if fixture.pre:
                for address, account in fixture.pre.root.items():
                    if account is None or account.code is None or len(account.code) == 0:
                        continue

                    try:
                        wrapped = wrap_code(account.code)
                    except ValueError as e:
                        self.metrics[self.ACCOUNTS_INVALID_EOF] += 1
                        _inc_counter(
                            self.metrics[self.VALIDATION_ERRORS], self._short_exception_msg(e)
                        )
                        continue

                    if self._validate_eof(wrapped):
                        account.code = Bytes(wrapped)
                        wrapped_at_least_one_account = True
                        self.metrics[self.ACCOUNTS_WRAPPED] += 1
                        fixture_eof_codes.append(to_hex(account.code))

                        # wrap the same account in post state the same way
                        if fixture.post_state and fixture.post_state.root[address]:
                            fixture.post_state.root[address].code = Bytes(wrapped)  # type: ignore
                    else:
                        self.metrics[self.ACCOUNTS_INVALID_EOF] += 1
            if not wrapped_at_least_one_account:
                self.metrics[self.FIXTURES_CANT_WRAP] += 1
                continue

            try:
                out_fixture = self._wrap_fixture(fixture, traces)
                out_fixtures[fixture_id] = out_fixture
                self.metrics[self.FIXTURES_GENERATED] += 1
                self.unique_eof.update(fixture_eof_codes)
                self.metrics[self.UNIQUE_ACCOUNTS_WRAPPED] = len(self.unique_eof)
            except Exception as e:
                _inc_counter(self.metrics[self.GENERATION_ERRORS], self._short_exception_msg(e))

                self.metrics[self.FIXTURES_CANT_GENERATE] += 1
                self.metrics[self.ACCOUNTS_CANT_GENERATE] += len(fixture_eof_codes)

                print(f"Exception {e} occurred during generation of {in_path}: {fixture_id}")

        if len(out_fixtures) == 0:
            self.metrics[self.FILES_SKIPPED] += 1
            return

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        out_fixtures.collect_into_file(Path(out_path))
        self.metrics[self.FILES_GENERATED] += 1

    def _short_exception_msg(self, e: Exception):
        threshold = 30
        short = str(e)
        if len(short) > threshold:
            short = short[:threshold] + "..."
        return short

    def _wrap_fixture(self, fixture: BlockchainFixture, traces: bool):
        env = Environment(
            difficulty=fixture.genesis.difficulty,
            gas_limit=fixture.genesis.gas_limit,
            base_fee_per_gas=fixture.genesis.base_fee_per_gas,
            blob_gas_used=fixture.genesis.blob_gas_used,
            excess_blob_gas=fixture.genesis.excess_blob_gas,
            parent_beacon_block_root=fixture.genesis.parent_beacon_block_root,
        )

        pre = fixture.pre

        t8n = EvmOneTransitionTool(trace=traces)

        test = BlockchainTest(
            genesis_environment=env,
            pre=pre.root,
            post=fixture.post_state.root if fixture.post_state else {},
            blocks=[],
            tag="wrapped test",
        )

        for fixture_block in fixture.blocks:
            if isinstance(fixture_block, FixtureBlock):
                header = fixture_block.header
                block = Block(
                    ommers_hash=header.ommers_hash,
                    fee_recipient=header.fee_recipient,
                    difficulty=header.difficulty,
                    number=header.number,
                    gas_limit=header.gas_limit,
                    timestamp=header.timestamp,
                    extra_data=header.extra_data,
                    prev_randao=header.prev_randao,
                    nonce=header.nonce,
                    base_fee_per_gas=header.base_fee_per_gas,
                    withdrawals_root=header.withdrawals_root,
                    parent_beacon_block_root=header.parent_beacon_block_root,
                )
                assert not fixture_block.ommers
                assert not fixture_block.withdrawals

                for fixture_tx in fixture_block.txs:
                    fixture_tx_dump = fixture_tx.model_dump()
                    fixture_tx_dump.pop("ty")
                    fixture_tx_dump.pop("data")
                    tx = Transaction(
                        type=fixture_tx.ty,
                        input=fixture_tx.data,
                        **fixture_tx_dump,
                    )
                    block.txs.append(tx)

                test.blocks.append(block)
            elif isinstance(fixture_block, InvalidFixtureBlock):
                # Skip - invalid blocks are not supported. Reason: FixtureTransaction doesn't
                # support expected exception. But we can continue and test the remaining
                # blocks.
                self.metrics[self.INVALID_BLOCKS_SKIPPED] += 1
            else:
                raise TypeError("not a FixtureBlock")

        result = test.generate(
            t8n=t8n,
            fork=EOFv1,
            fixture_format=BlockchainFixture,
        )
        result.info["fixture-format"] = "blockchain_test"
        if traces:
            print_traces(t8n.get_traces())
        return result

    def _validate_eof(self, container: Container, metrics: bool = True) -> bool:
        eof_parse = EOFParse()

        result = eof_parse.run(input_value=to_hex(container))
        actual_message = result.stdout.strip()
        if "OK" not in actual_message:
            if metrics:
                _inc_counter(self.metrics[self.VALIDATION_ERRORS], actual_message)
            return False

        return True


# `no_type_check` required because OpcodeWithOperand.opcode can be `None` when formatting as a
# string, but here it can never be `None`.
@no_type_check
def wrap_code(account_code: Bytes) -> Container:
    """
    Wrap `account_code` into a simplest EOF container, applying some simple heuristics in
    order to obtain a valid code section termination.
    """
    assert len(account_code) > 0

    opcodes = process_evm_bytes(account_code)

    if not opcodes[-1].terminating:
        opcodes.append(OpcodeWithOperands(opcode=Op.STOP))

    while len(opcodes) > 1 and opcodes[-2].terminating and opcodes[-1].terminating:
        opcodes.pop()

    bytecode = Bytecode()

    for opcode in opcodes:
        bytecode += opcode.bytecode

    return Container.Code(bytecode)


def _inc_counter(d: dict, key: Any) -> None:
    if key in d:
        d[key] += 1
    else:
        d[key] = 1
