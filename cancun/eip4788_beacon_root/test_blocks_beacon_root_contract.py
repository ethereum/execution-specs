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
from typing import Dict, Iterator, List

import pytest

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

from .spec import Spec, ref_spec_4788

REFERENCE_SPEC_GIT_PATH = ref_spec_4788.git_path
REFERENCE_SPEC_VERSION = ref_spec_4788.version


@pytest.mark.parametrize(
    "timestamps",
    [
        pytest.param(
            count(
                start=Spec.HISTORY_BUFFER_LENGTH - 5,
                step=1,
            ),
            id="buffer_wraparound",
        ),
        pytest.param(
            count(
                start=12,
                step=Spec.HISTORY_BUFFER_LENGTH,
            ),
            id="buffer_wraparound_overwrite",
        ),
        pytest.param(
            count(
                start=2**32,
                step=Spec.HISTORY_BUFFER_LENGTH,
            ),
            id="buffer_wraparound_overwrite_high_timestamp",
        ),
        pytest.param(
            count(
                start=5,
                step=Spec.HISTORY_BUFFER_LENGTH - 1,
            ),
            id="buffer_wraparound_no_overwrite",
        ),
        pytest.param(
            count(
                start=Spec.HISTORY_BUFFER_LENGTH - 3,
                step=Spec.HISTORY_BUFFER_LENGTH + 1,
            ),
            id="buffer_wraparound_no_overwrite_2",
        ),
    ],
)
@pytest.mark.parametrize("block_count", [10])  # All tests use 10 blocks
@pytest.mark.valid_from("Cancun")
def test_multi_block_beacon_root_timestamp_calls(
    blockchain_test: BlockchainTestFiller,
    timestamps: Iterator[int],
    beacon_roots: Iterator[bytes],
    block_count: int,
    tx: Transaction,
    call_gas: int,
    call_value: int,
):
    """
    Tests multiple blocks where each block writes a timestamp to storage and contains one
    transaction that calls the beacon root contract multiple times.

    The blocks might overwrite the historical roots buffer, or not, depending on the `timestamps`,
    and whether they increment in multiples of `Spec.HISTORY_BUFFER_LENGTH` or not.

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
    }
    post = {}

    timestamps_storage: Dict[int, int] = {}
    roots_storage: Dict[int, bytes] = {}

    all_timestamps: List[int] = []

    for timestamp, beacon_root, i in zip(timestamps, beacon_roots, range(block_count)):
        timestamp_index = timestamp % Spec.HISTORY_BUFFER_LENGTH
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
                and timestamps_storage[t % Spec.HISTORY_BUFFER_LENGTH] == t
            )
            current_call_account_code += Op.SSTORE(
                current_call_account_expected_storage.store_next(0x01 if call_valid else 0x00),
                Op.CALL(
                    call_gas,
                    Spec.BEACON_ROOTS_ADDRESS,
                    call_value,
                    0x00,
                    0x20,
                    0x20,
                    0x20,
                ),
            )

            current_call_account_code += Op.SSTORE(
                current_call_account_expected_storage.store_next(
                    roots_storage[t % Spec.HISTORY_BUFFER_LENGTH] if call_valid else 0x00
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
                        address=Spec.BEACON_ROOTS_ADDRESS,
                        amount=1,
                        index=next(withdraw_index),
                        validator=0,
                    ),
                    Withdrawal(
                        address=Spec.SYSTEM_ADDRESS,
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
def test_beacon_root_transition(
    blockchain_test: BlockchainTestFiller,
    timestamps: Iterator[int],
    beacon_roots: Iterator[bytes],
    block_count: int,
    tx: Transaction,
    call_gas: int,
    call_value: int,
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
    }
    post = {}

    timestamps_storage: Dict[int, int] = {}
    roots_storage: Dict[int, bytes] = {}

    all_timestamps: List[int] = []
    timestamps_in_beacon_root_contract: List[int] = []

    for timestamp, beacon_root, i in zip(timestamps, beacon_roots, range(block_count)):
        timestamp_index = timestamp % Spec.HISTORY_BUFFER_LENGTH

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
                and timestamps_storage[t % Spec.HISTORY_BUFFER_LENGTH] == t
            )
            current_call_account_code += Op.SSTORE(
                current_call_account_expected_storage.store_next(0x01 if call_valid else 0x00),
                Op.CALL(
                    call_gas,
                    Spec.BEACON_ROOTS_ADDRESS,
                    call_value,
                    0x00,
                    0x20,
                    0x20,
                    0x20,
                ),
            )

            current_call_account_code += Op.SSTORE(
                current_call_account_expected_storage.store_next(
                    roots_storage[t % Spec.HISTORY_BUFFER_LENGTH] if call_valid else 0x00
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
                        address=Spec.BEACON_ROOTS_ADDRESS,
                        amount=1,
                        index=next(withdraw_index),
                        validator=0,
                    ),
                    Withdrawal(
                        address=Spec.SYSTEM_ADDRESS,
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


@pytest.mark.parametrize("timestamp", [15_000])
@pytest.mark.valid_at_transition_to("Cancun")
def test_no_beacon_root_contract_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
    beacon_roots: Iterator[bytes],
    tx: Transaction,
    timestamp: int,
    caller_address: str,
    fork: Fork,
):
    """
    Tests the fork transition to cancun in the case where the beacon root pre-deploy was not
    deployed in time for the fork.
    """
    assert fork.header_beacon_root_required(1, timestamp)
    blocks: List[Block] = [
        Block(
            txs=[tx],
            beacon_root=next(beacon_roots),
            timestamp=timestamp,
            withdrawals=[
                # Also withdraw to the beacon root contract and the system address
                Withdrawal(
                    address=Spec.BEACON_ROOTS_ADDRESS,
                    amount=1,
                    index=0,
                    validator=0,
                ),
                Withdrawal(
                    address=Spec.SYSTEM_ADDRESS,
                    amount=1,
                    index=1,
                    validator=1,
                ),
            ],
        )
    ]
    pre[Spec.BEACON_ROOTS_ADDRESS] = Account(
        code=b"",  # Remove the code that is automatically allocated on Cancun fork
        nonce=0,
        balance=0,
    )
    post = {
        Spec.BEACON_ROOTS_ADDRESS: Account(
            storage={
                timestamp % Spec.HISTORY_BUFFER_LENGTH: 0,
                (timestamp % Spec.HISTORY_BUFFER_LENGTH) + Spec.HISTORY_BUFFER_LENGTH: 0,
            },
            code=b"",
            nonce=0,
            balance=int(1e9),
        ),
        caller_address: Account(
            storage={
                0: 1
            },  # Successful call because the contract is not there, but nothing else is stored
        ),
    }
    blockchain_test(
        pre=pre,
        blocks=blocks,
        post=post,
    )


@pytest.mark.parametrize(
    "timestamp",
    [
        pytest.param(15_000, id="deploy_on_shanghai"),
        pytest.param(30_000, id="deploy_on_cancun"),
    ],
)
@pytest.mark.valid_at_transition_to("Cancun")
def test_beacon_root_contract_deploy(
    blockchain_test: BlockchainTestFiller,
    pre: Dict,
    beacon_root: bytes,
    tx: Transaction,
    timestamp: int,
    post: Dict,
    fork: Fork,
):
    """
    Tests the fork transition to cancun deploying the contract during Shanghai and verifying the
    code deployed and its functionality after Cancun.
    """
    assert fork.header_beacon_root_required(1, timestamp)
    tx_gas_limit = 0x3D090
    tx_gas_price = 0xE8D4A51000
    deployer_required_balance = tx_gas_limit * tx_gas_price
    deploy_tx = Transaction(
        ty=0,
        nonce=0,
        to=None,
        gas_limit=tx_gas_limit,
        gas_price=tx_gas_price,
        value=0,
        data=bytes.fromhex(
            "60618060095f395ff33373fffffffffffffffffffffffffffffffffffffffe14604d576020361460"
            "24575f5ffd5b5f35801560495762001fff810690815414603c575f5ffd5b62001fff01545f526020"
            "5ff35b5f5ffd5b62001fff42064281555f359062001fff015500"
        ),
        v=0x1B,
        r=0x539,
        s=0x1B9B6EB1F0,
        protected=False,
    ).with_signature_and_sender()
    deployer_address = deploy_tx.sender
    assert deployer_address is not None
    assert deployer_address == int.to_bytes(Spec.BEACON_ROOTS_DEPLOYER_ADDRESS, 20, "big")
    blocks: List[Block] = []

    beacon_root_contract_storage: Dict = {}
    for i, current_timestamp in enumerate(range(timestamp // 2, timestamp + 1, timestamp // 2)):
        if i == 0:
            blocks.append(
                Block(  # Deployment block
                    txs=[deploy_tx],
                    beacon_root=beacon_root
                    if fork.header_beacon_root_required(1, current_timestamp)
                    else None,
                    timestamp=timestamp // 2,
                    withdrawals=[
                        # Also withdraw to the beacon root contract and the system address
                        Withdrawal(
                            address=Spec.BEACON_ROOTS_ADDRESS,
                            amount=1,
                            index=0,
                            validator=0,
                        ),
                        Withdrawal(
                            address=Spec.SYSTEM_ADDRESS,
                            amount=1,
                            index=1,
                            validator=1,
                        ),
                    ],
                )
            )
            beacon_root_contract_storage[current_timestamp % Spec.HISTORY_BUFFER_LENGTH] = 0
            beacon_root_contract_storage[
                (current_timestamp % Spec.HISTORY_BUFFER_LENGTH) + Spec.HISTORY_BUFFER_LENGTH
            ] = 0
        elif i == 1:
            blocks.append(
                Block(  # Contract already deployed
                    txs=[tx],
                    beacon_root=beacon_root,
                    timestamp=timestamp,
                    withdrawals=[
                        # Also withdraw to the beacon root contract and the system address
                        Withdrawal(
                            address=Spec.BEACON_ROOTS_ADDRESS,
                            amount=1,
                            index=2,
                            validator=0,
                        ),
                        Withdrawal(
                            address=Spec.SYSTEM_ADDRESS,
                            amount=1,
                            index=3,
                            validator=1,
                        ),
                    ],
                ),
            )
            beacon_root_contract_storage[
                current_timestamp % Spec.HISTORY_BUFFER_LENGTH
            ] = current_timestamp
            beacon_root_contract_storage[
                (current_timestamp % Spec.HISTORY_BUFFER_LENGTH) + Spec.HISTORY_BUFFER_LENGTH
            ] = beacon_root
        else:
            assert False, "This test should only have two blocks"

    expected_code = fork.pre_allocation(1, timestamp)[Spec.BEACON_ROOTS_ADDRESS]["code"]
    pre[Spec.BEACON_ROOTS_ADDRESS] = Account(
        code=b"",  # Remove the code that is automatically allocated on Cancun fork
        nonce=0,
        balance=0,
    )
    pre[deployer_address] = Account(
        balance=deployer_required_balance,
    )

    post[Spec.BEACON_ROOTS_ADDRESS] = Account(
        storage=beacon_root_contract_storage,
        code=expected_code,
        nonce=1,
        balance=int(2e9),
    )
    post[Spec.SYSTEM_ADDRESS] = Account(
        storage={},
        code=b"",
        nonce=0,
        balance=int(2e9),
    )
    post[deployer_address] = Account(
        balance=175916000000000000,  # It doesn't consume all the balance :(
        nonce=1,
    )
    blockchain_test(
        pre=pre,
        blocks=blocks,
        post=post,
    )
