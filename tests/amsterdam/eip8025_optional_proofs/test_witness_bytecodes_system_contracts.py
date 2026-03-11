"""Witness bytecode scenarios for system contracts."""

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    ExecutionWitnessCodesExpectation,
    Fork,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# System contracts called every block (addresses as ints).
SYSTEM_CONTRACT_ADDRS = [
    0x000F3DF6D732807EF1319FB7B8BB8522D0BEAC02,  # beacon roots
    0x00000961EF480EB55E80D19AD83579A64C007002,  # withdrawal request
    0x0000BBDDC7CE488642FB579F8B00F3A590007251,  # consolidation request
    0x0000F90827F1C53A10CB7A02335B175320002935,  # history storage
]


def test_witness_codes_empty_block_has_system_contracts(
    pre: Alloc,
    fork: Fork,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Verify an empty block contains only system contract bytecodes.

    System contracts are called every block via process_system_call,
    which calls get_code() on a tracked TransactionState. An empty
    block (no user transactions) should have exactly the four system
    contract bytecodes in executionWitness.codes and nothing else.
    """
    alloc = fork.pre_allocation_blockchain()

    system_codes = []
    for addr in SYSTEM_CONTRACT_ADDRS:
        code = alloc[addr]["code"]
        if isinstance(code, str):
            code = bytes.fromhex(code.removeprefix("0x"))
        system_codes.append(Bytes(code))

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=system_codes,
                        allow_unexpected=False,
                    )
                ),
            )
        ],
        post={},
    )
