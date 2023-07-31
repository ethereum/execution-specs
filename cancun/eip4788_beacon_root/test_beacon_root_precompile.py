"""
abstract: Tests beacon block root for [EIP-4788: Beacon block root in the EVM](https://eips.ethereum.org/EIPS/eip-4788)

    Test the exposed beacon chain root in the EVM for [EIP-4788: Beacon block root in the EVM](https://eips.ethereum.org/EIPS/eip-4788)

note: Adding a new test

    Add a function that is named `test_<test_name>` and takes at least the following arguments:

    - blockchain_test or state_test
    - env
    - pre
    - blocks or tx
    - post
    - valid_call

    The following arguments *need* to be parametrized or the test will not be generated:

    -

    All other `pytest.fixtures` can be parametrized to generate new combinations and test
    cases.

"""  # noqa: E501

from typing import Dict

import pytest

from ethereum_test_tools import (
    Account,
    Block,
    BlockchainTestFiller,
    Environment,
    StateTestFiller,
    Transaction,
    to_address,
    to_hash_bytes,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .common import (
    BEACON_ROOT_PRECOMPILE_GAS,
    DEFAULT_BEACON_ROOT_HASH,
    HISTORICAL_ROOTS_MODULUS,
    REF_SPEC_4788_GIT_PATH,
    REF_SPEC_4788_VERSION,
    expected_storage,
    timestamp_index,
)

REFERENCE_SPEC_GIT_PATH = REF_SPEC_4788_GIT_PATH
REFERENCE_SPEC_VERSION = REF_SPEC_4788_VERSION


@pytest.mark.parametrize(
    "call_gas, valid_call",
    [
        (BEACON_ROOT_PRECOMPILE_GAS, True),
        (BEACON_ROOT_PRECOMPILE_GAS + 1, True),
        (BEACON_ROOT_PRECOMPILE_GAS - 1, False),
    ],
)
@pytest.mark.parametrize(
    "call_type",
    [
        Op.CALL,
        Op.DELEGATECALL,
        Op.CALLCODE,
        Op.STATICCALL,
    ],
)
@pytest.mark.valid_from("Cancun")
def test_beacon_root_precompile_calls(
    state_test: StateTestFiller,
    env: Environment,
    pre: Dict,
    tx: Transaction,
    post: Dict,
):
    """
    Tests the beacon root precompile call using various call contexts:
    - `CALL`
    - `DELEGATECALL`
    - `CALLCODE`
    - `STATICCALL`
    for different call gas amounts:
    - exact gas (valid call)
    - extra gas (valid call)
    - insufficient gas (invalid call)

    The expected result is that the precompile call will be executed if the gas amount is met
    and return the correct`parent_beacon_block_root`. Otherwise the call will be invalid, and not
    be executed. This is highlighted within storage by storing the return value of each call
    context.
    """
    state_test(
        env=env,
        pre=pre,
        txs=[tx],
        post=post,
    )


@pytest.mark.parametrize(
    "timestamp, valid_input",
    [
        (0x0C, True),  # twelve
        (2**32, True),  # arbitrary
        (2**64 - 2, True),  # near-max
        (2**64 - 1, True),  # max
        # TODO: Update t8n to un marshal > 64-bit int
        # Exception: failed to evaluate: ERROR(10): failed un marshaling stdin
        # (2**64, False),  # overflow
        # Exception: failed to evaluate: ERROR(10): failed un marshaling stdin
        # (2**64 + 1, False),  # overflow+1
    ],
)
@pytest.mark.valid_from("Cancun")
def test_beacon_root_precompile_timestamps(
    state_test: StateTestFiller,
    env: Environment,
    pre: Dict,
    tx: Transaction,
    post: Dict,
):
    """
    Tests the beacon root precompile call across for various valid and invalid timestamps.

    The expected result is that the precompile call will return the correct
    `parent_beacon_block_root` for a valid input timestamp and return the zero'd 32 bytes value
    for an invalid input timestamp.
    """
    state_test(
        env=env,
        pre=pre,
        txs=[tx],
        post=post,
    )


@pytest.mark.parametrize(
    "beacon_root, timestamp",
    [
        (12, 12),  # twelve
        (2**32, 2**32),  # arbitrary
        (2**64 - 2, 2**64 - 2),  # near-max
        (2**64 - 1, 2**64 - 1),  # max
    ],
    indirect=["beacon_root"],
)
@pytest.mark.valid_from("Cancun")
def test_beacon_root_equal_to_timestamp(
    state_test: StateTestFiller,
    env: Environment,
    pre: Dict,
    tx: Transaction,
    post: Dict,
):
    """
    Tests the beacon root precompile call where the beacon root is equal to the timestamp.

    The expected result is that the precompile call will return the `parent_beacon_block_root`,
    as all timestamps used are valid.
    """
    state_test(
        env=env,
        pre=pre,
        txs=[tx],
        post=post,
    )


@pytest.mark.parametrize(
    "call_gas, valid_call",
    [
        (BEACON_ROOT_PRECOMPILE_GAS, True),
        (BEACON_ROOT_PRECOMPILE_GAS + 1, True),
        (BEACON_ROOT_PRECOMPILE_GAS - 1, False),
    ],
)
@pytest.mark.parametrize(
    "timestamp",
    [
        12,  # twelve
        2**32,  # arbitrary
    ],
)
@pytest.mark.valid_from("Cancun")
def test_beacon_root_timestamp_collisions(
    blockchain_test: BlockchainTestFiller,
    env: Environment,
    pre: Dict,
    tx: Transaction,
    precompile_call_account: Account,
    timestamp: int,
    valid_call: bool,
):
    """
    Tests multiple beacon root precompile calls where the timestamp index is calculated to
    be equal for each call (i.e colliding). For each parameterized timestamp a list of
    colliding timestamps are calculated using factors of the `HISTORY_ROOTS_MODULUS`.

    The expected result is that precompile call will return an equal beacon_root
    for each timestamp used within the call, as the timestamp index used will be the same.

    Here we are predominantly testing that the `timestamp_index` and `root_index` are derived
    correctly in the evm.
    """
    post = {}
    blocks, colliding_timestamps = [], []
    timestamp_collisions = 5
    for i in range(timestamp_collisions):
        pre[to_address(0x100 + i)] = precompile_call_account
        colliding_timestamps.append(timestamp + i * HISTORICAL_ROOTS_MODULUS)

    # check timestamp_index function is working as expected
    timestamp_indexes = [timestamp_index(v) for v in colliding_timestamps]
    assert len(set(timestamp_indexes)) == 1, "timestamp_index function is not working"

    for i, timestamp in enumerate(colliding_timestamps):
        blocks.append(
            Block(
                txs=[
                    tx.with_fields(
                        nonce=i,
                        to=to_address(0x100 + i),
                        data=to_hash_bytes(timestamp),
                    )
                ],
                beacon_root=DEFAULT_BEACON_ROOT_HASH,
                timestamp=timestamp,
            )
        )
        post[to_address(0x100 + i)] = Account(
            storage=expected_storage(
                beacon_root=DEFAULT_BEACON_ROOT_HASH,
                timestamp=timestamp,
                valid_call=valid_call,
                valid_input=True,
            )
        )

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post=post,
    )
