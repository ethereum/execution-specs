"""
abstract: Tests beacon block root for [EIP-4788: Beacon block root in the EVM](https://eips.ethereum.org/EIPS/eip-4788)

    Test the exposed beacon chain root in the EVM for [EIP-4788: Beacon block root in the EVM](https://eips.ethereum.org/EIPS/eip-4788) using multi-block tests

note: Adding a new test

    Add a function that is named `test_<test_name>` and takes at least the following arguments:

    - blockchain_test
    - env
    - pre
    - blocks
    - post
    - valid_call

    The following arguments *need* to be parametrized or the test will not be generated:

    -

    All other `pytest.fixtures` can be parametrized to generate new combinations and test
    cases.

"""  # noqa: E501

from itertools import count
from typing import Dict, Iterable, List

import pytest
from ethereum.crypto.hash import keccak256

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Block,
    BlockchainTestFiller,
    Storage,
    TestAddress,
    Transaction,
    Withdrawal,
    to_address,
    to_hash_bytes,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .common import (
    BEACON_ROOT_CONTRACT_ADDRESS,
    HISTORICAL_ROOTS_MODULUS,
    REF_SPEC_4788_GIT_PATH,
    REF_SPEC_4788_VERSION,
    SYSTEM_ADDRESS,
)

REFERENCE_SPEC_GIT_PATH = REF_SPEC_4788_GIT_PATH
REFERENCE_SPEC_VERSION = REF_SPEC_4788_VERSION


@pytest.fixture
def beacon_roots() -> Iterable[bytes]:
    """
    By default, return an iterator that returns the keccak of an internal counter.
    """

    class BeaconRoots:
        def __init__(self) -> None:
            self._counter = count(1)

        def __iter__(self) -> "BeaconRoots":
            return self

        def __next__(self) -> bytes:
            return keccak256(int.to_bytes(next(self._counter), length=8, byteorder="big"))

    return BeaconRoots()


@pytest.mark.parametrize(
    "timestamps",
    [
        pytest.param(
            count(
                start=HISTORICAL_ROOTS_MODULUS - 5,
                step=1,
            ),
            id="buffer_wraparound",
        ),
        pytest.param(
            count(
                start=12,
                step=HISTORICAL_ROOTS_MODULUS,
            ),
            id="buffer_wraparound_overwrite",
        ),
        pytest.param(
            count(
                start=2**32,
                step=HISTORICAL_ROOTS_MODULUS,
            ),
            id="buffer_wraparound_overwrite_high_timestamp",
        ),
        pytest.param(
            count(
                start=5,
                step=HISTORICAL_ROOTS_MODULUS - 1,
            ),
            id="buffer_wraparound_no_overwrite",
        ),
        pytest.param(
            count(
                start=HISTORICAL_ROOTS_MODULUS - 3,
                step=HISTORICAL_ROOTS_MODULUS + 1,
            ),
            id="buffer_wraparound_no_overwrite_2",
        ),
    ],
)
@pytest.mark.parametrize("block_count", [10])  # All tests use 10 blocks
@pytest.mark.valid_from("Cancun")
def test_multi_block_beacon_root_timestamp_calls(
    blockchain_test: BlockchainTestFiller,
    timestamps: Iterable[int],
    beacon_roots: Iterable[bytes],
    block_count: int,
    tx: Transaction,
    call_gas: int,
    call_value: int,
    system_address_balance: int,
):
    """
    Tests multiple blocks where each block writes a timestamp to storage and contains one
    transaction that calls the beacon root contract multiple times.

    The blocks might overwrite the historical roots buffer, or not, depending on the `timestamps`,
    and whether they increment in multiples of `HISTORICAL_ROOTS_MODULUS` or not.

    By default, the beacon roots are the keccak of the block number.

    Each transaction checks the current timestamp and also all previous timestamps, and verifies
    that the beacon root is correct for all of them if the timestamp is supposed to be in the
    buffer, which might have been overwritten by a later block.
    """
    blocks: List[Block] = []
    pre = {
        TestAddress: Account(
            nonce=0,
            balance=0x10**10,
        ),
        SYSTEM_ADDRESS: Account(
            nonce=0,
            balance=system_address_balance,
        ),
    }
    post = {}

    timestamps_storage: Dict[int, int] = {}
    roots_storage: Dict[int, bytes] = {}

    all_timestamps: List[int] = []

    for timestamp, beacon_root, i in zip(timestamps, beacon_roots, range(block_count)):
        timestamp_index = timestamp % HISTORICAL_ROOTS_MODULUS
        timestamps_storage[timestamp_index] = timestamp
        roots_storage[timestamp_index] = beacon_root

        all_timestamps.append(timestamp)

        withdraw_index = count(0)

        current_call_account_code = bytes()
        current_call_account_expected_storage = Storage()
        current_call_account_address = to_address(0x100 + i)

        # We are going to call the beacon roots contract once for every timestamp of the current
        # and all previous blocks, and check that the returned beacon root is still correct only
        # if it was not overwritten.
        for t in all_timestamps:
            current_call_account_code += Op.MSTORE(0, t)
            call_valid = (
                timestamp_index in timestamps_storage
                and timestamps_storage[t % HISTORICAL_ROOTS_MODULUS] == t
            )
            current_call_account_code += Op.SSTORE(
                current_call_account_expected_storage.store_next(0x01 if call_valid else 0x00),
                Op.CALL(
                    call_gas,
                    BEACON_ROOT_CONTRACT_ADDRESS,
                    call_value,
                    0x00,
                    0x20,
                    0x20,
                    0x20,
                ),
            )

            current_call_account_code += Op.SSTORE(
                current_call_account_expected_storage.store_next(
                    roots_storage[t % HISTORICAL_ROOTS_MODULUS] if call_valid else 0x00
                ),
                Op.MLOAD(0x20),
            )

        pre[current_call_account_address] = Account(
            code=current_call_account_code,
        )
        post[current_call_account_address] = Account(
            storage=current_call_account_expected_storage,
        )
        blocks.append(
            Block(
                txs=[
                    tx.with_fields(
                        nonce=i,
                        to=to_address(0x100 + i),
                        data=to_hash_bytes(timestamp),
                    )
                ],
                beacon_root=beacon_root,
                timestamp=timestamp,
                withdrawals=[
                    # Also withdraw to the beacon root contract and the system address
                    Withdrawal(
                        address=BEACON_ROOT_CONTRACT_ADDRESS,
                        amount=1,
                        index=next(withdraw_index),
                        validator=0,
                    ),
                    Withdrawal(
                        address=SYSTEM_ADDRESS,
                        amount=1,
                        index=next(withdraw_index),
                        validator=1,
                    ),
                ],
            )
        )

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post=post,
    )


@pytest.mark.parametrize(
    "timestamps",
    [pytest.param(count(start=1000, step=1000), id="fork_transition")],
)
@pytest.mark.parametrize("block_count", [20])
@pytest.mark.valid_at_transition_to("Cancun")
def test_beacon_root_transition_test(
    blockchain_test: BlockchainTestFiller,
    timestamps: Iterable[int],
    beacon_roots: Iterable[bytes],
    block_count: int,
    tx: Transaction,
    call_gas: int,
    call_value: int,
    system_address_balance: int,
    fork: Fork,
):
    """
    Tests the fork transition to cancun and verifies that blocks with timestamp lower than the
    transition timestamp do not contain beacon roots in the pre-deployed contract.
    """
    blocks: List[Block] = []
    pre = {
        TestAddress: Account(
            nonce=0,
            balance=0x10**10,
        ),
        SYSTEM_ADDRESS: Account(
            nonce=0,
            balance=system_address_balance,
        ),
    }
    post = {}

    timestamps_storage: Dict[int, int] = {}
    roots_storage: Dict[int, bytes] = {}

    all_timestamps: List[int] = []
    timestamps_in_beacon_root_contract: List[int] = []

    for timestamp, beacon_root, i in zip(timestamps, beacon_roots, range(block_count)):
        timestamp_index = timestamp % HISTORICAL_ROOTS_MODULUS

        transitioned = fork.header_beacon_root_required(i, timestamp)
        if transitioned:
            # We've transitioned, the current timestamp must contain a value in the contract
            timestamps_in_beacon_root_contract.append(timestamp)
            timestamps_storage[timestamp_index] = timestamp
            roots_storage[timestamp_index] = beacon_root

        all_timestamps.append(timestamp)

        withdraw_index = count(0)

        current_call_account_code = bytes()
        current_call_account_expected_storage = Storage()
        current_call_account_address = to_address(0x100 + i)

        # We are going to call the beacon roots contract once for every timestamp of the current
        # and all previous blocks, and check that the returned beacon root is correct only
        # if it was after the transition timestamp.
        for t in all_timestamps:
            current_call_account_code += Op.MSTORE(0, t)
            call_valid = (
                t in timestamps_in_beacon_root_contract
                and timestamp_index in timestamps_storage
                and timestamps_storage[t % HISTORICAL_ROOTS_MODULUS] == t
            )
            current_call_account_code += Op.SSTORE(
                current_call_account_expected_storage.store_next(0x01 if call_valid else 0x00),
                Op.CALL(
                    call_gas,
                    BEACON_ROOT_CONTRACT_ADDRESS,
                    call_value,
                    0x00,
                    0x20,
                    0x20,
                    0x20,
                ),
            )

            current_call_account_code += Op.SSTORE(
                current_call_account_expected_storage.store_next(
                    roots_storage[t % HISTORICAL_ROOTS_MODULUS] if call_valid else 0x00
                ),
                Op.MLOAD(0x20),
            )

        pre[current_call_account_address] = Account(
            code=current_call_account_code,
        )
        post[current_call_account_address] = Account(
            storage=current_call_account_expected_storage,
        )
        blocks.append(
            Block(
                txs=[
                    tx.with_fields(
                        nonce=i,
                        to=to_address(0x100 + i),
                        data=to_hash_bytes(timestamp),
                    )
                ],
                beacon_root=beacon_root if transitioned else None,
                timestamp=timestamp,
                withdrawals=[
                    # Also withdraw to the beacon root contract and the system address
                    Withdrawal(
                        address=BEACON_ROOT_CONTRACT_ADDRESS,
                        amount=1,
                        index=next(withdraw_index),
                        validator=0,
                    ),
                    Withdrawal(
                        address=SYSTEM_ADDRESS,
                        amount=1,
                        index=next(withdraw_index),
                        validator=1,
                    ),
                ],
            )
        )

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post=post,
    )
