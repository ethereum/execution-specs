"""
abstract: Tests beacon block root for [EIP-4788: Beacon block root in the EVM](https://eips.ethereum.org/EIPS/eip-4788)
    Test the exposed beacon chain root in the EVM for [EIP-4788: Beacon block root in the EVM](https://eips.ethereum.org/EIPS/eip-4788)

note: Adding a new test
    Add a function that is named `test_<test_name>` and takes at least the following arguments:

    - state_test
    - env
    - pre
    - tx
    - post
    - valid_call

    All other `pytest.fixtures` can be parametrized to generate new combinations and test
    cases.

"""  # noqa: E501

from itertools import count
from typing import Dict, Iterator, List

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Address,
    Block,
    BlockchainTestFiller,
    Hash,
    Storage,
    TestAddress,
    Transaction,
    Withdrawal,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .spec import Spec, ref_spec_4788

REFERENCE_SPEC_GIT_PATH = ref_spec_4788.git_path
REFERENCE_SPEC_VERSION = ref_spec_4788.version


@pytest.mark.parametrize(
    "call_gas, valid_call",
    [
        pytest.param(Spec.BEACON_ROOTS_CALL_GAS, True),
        pytest.param(int(Spec.BEACON_ROOTS_CALL_GAS / 100), False),
    ],
)
@pytest.mark.parametrize(
    "call_type,call_value,valid_input",
    [
        (Op.CALL, 1, True),
        (Op.CALL, 0, True),
        (Op.CALLCODE, 0, False),
        (Op.DELEGATECALL, 0, False),
        (Op.STATICCALL, 0, True),
    ],
)
@pytest.mark.valid_from("Cancun")
def test_beacon_root_contract_calls(
    blockchain_test: BlockchainTestFiller,
    beacon_root: bytes,
    timestamp: int,
    pre: Dict,
    tx: Transaction,
    post: Dict,
):
    """
    Tests the beacon root contract call using various call contexts:
    - `CALL`
    - `DELEGATECALL`
    - `CALLCODE`
    - `STATICCALL`
    for different call gas amounts:
    - exact gas (valid call)
    - extra gas (valid call)
    - insufficient gas (invalid call)

    The expected result is that the contract call will be executed if the gas amount is met
    and return the correct`parent_beacon_block_root`. Otherwise the call will be invalid, and not
    be executed. This is highlighted within storage by storing the return value of each call
    context.
    """
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], parent_beacon_block_root=beacon_root, timestamp=timestamp)],
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
@pytest.mark.parametrize("auto_access_list", [False, True])
@pytest.mark.parametrize(
    "system_address_balance",
    [
        pytest.param(0, id="empty_system_address"),
        pytest.param(1, id="one_wei_system_address"),
        pytest.param(int(1e18), id="one_eth_system_address"),
    ],
)
@pytest.mark.valid_from("Cancun")
def test_beacon_root_contract_timestamps(
    blockchain_test: BlockchainTestFiller,
    beacon_root: bytes,
    timestamp: int,
    pre: Dict,
    tx: Transaction,
    post: Dict,
):
    """
    Tests the beacon root contract call across for various valid and invalid timestamps.

    The expected result is that the contract call will return the correct
    `parent_beacon_block_root` for a valid input timestamp and return the zero'd 32 bytes value
    for an invalid input timestamp.
    """
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], parent_beacon_block_root=beacon_root, timestamp=timestamp)],
        post=post,
    )


@pytest.mark.parametrize(
    "tx_data",
    [
        pytest.param(bytes(), id="empty_calldata"),
        pytest.param(int.to_bytes(12, length=1, byteorder="big"), id="one_byte"),
        pytest.param(int.to_bytes(12, length=31, byteorder="big"), id="31_bytes"),
        pytest.param(int.to_bytes(12, length=33, byteorder="big"), id="33_bytes"),
        pytest.param(int.to_bytes(12, length=1024, byteorder="big"), id="1024_bytes"),
    ],
)
@pytest.mark.parametrize("valid_call,valid_input", [(False, False)])
@pytest.mark.parametrize("timestamp", [12])
@pytest.mark.valid_from("Cancun")
def test_calldata_lengths(
    blockchain_test: BlockchainTestFiller,
    beacon_root: bytes,
    timestamp: int,
    pre: Dict,
    tx: Transaction,
    post: Dict,
):
    """
    Tests the beacon root contract call using multiple invalid input lengths.
    """
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], parent_beacon_block_root=beacon_root, timestamp=timestamp)],
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
@pytest.mark.parametrize("auto_access_list", [False, True])
@pytest.mark.valid_from("Cancun")
def test_beacon_root_equal_to_timestamp(
    blockchain_test: BlockchainTestFiller,
    beacon_root: bytes,
    timestamp: int,
    pre: Dict,
    tx: Transaction,
    post: Dict,
):
    """
    Tests the beacon root contract call where the beacon root is equal to the timestamp.

    The expected result is that the contract call will return the `parent_beacon_block_root`,
    as all timestamps used are valid.
    """
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], parent_beacon_block_root=beacon_root, timestamp=timestamp)],
        post=post,
    )


@pytest.mark.parametrize("auto_access_list", [False, True])
@pytest.mark.parametrize("call_beacon_root_contract", [True])
@pytest.mark.with_all_tx_types
@pytest.mark.valid_from("Cancun")
def test_tx_to_beacon_root_contract(
    blockchain_test: BlockchainTestFiller,
    beacon_root: bytes,
    timestamp: int,
    pre: Dict,
    tx: Transaction,
    post: Dict,
):
    """
    Tests the beacon root contract using a transaction with different types and data lengths.
    """
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], parent_beacon_block_root=beacon_root, timestamp=timestamp)],
        post=post,
    )


@pytest.mark.parametrize(
    "tx_data",
    [
        pytest.param(int.to_bytes(0, length=32, byteorder="big"), id="zero_calldata"),
    ],
)
@pytest.mark.parametrize("valid_call,valid_input", [(False, False)])
@pytest.mark.parametrize("timestamp", [12])
@pytest.mark.valid_from("Cancun")
def test_invalid_beacon_root_calldata_value(
    blockchain_test: BlockchainTestFiller,
    beacon_root: bytes,
    timestamp: int,
    pre: Dict,
    tx: Transaction,
    post: Dict,
):
    """
    Tests the beacon root contract call using invalid input values:
    - zero calldata.

    Contract should revert.
    """
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], parent_beacon_block_root=beacon_root, timestamp=timestamp)],
        post=post,
    )


@pytest.mark.parametrize("timestamp", [12])
@pytest.mark.valid_from("Cancun")
def test_beacon_root_selfdestruct(
    blockchain_test: BlockchainTestFiller,
    beacon_root: bytes,
    timestamp: int,
    pre: Dict,
    tx: Transaction,
    post: Dict,
):
    """
    Tests that self destructing the beacon root address transfers actors balance correctly.
    """
    # self destruct actor
    pre[Address(0x1337)] = Account(
        code=Op.SELFDESTRUCT(Spec.BEACON_ROOTS_ADDRESS),
        balance=0xBA1,
    )
    # self destruct caller
    pre[Address(0xCC)] = Account(
        code=Op.CALL(100000, Address(0x1337), 0, 0, 0, 0, 0)
        + Op.SSTORE(0, Op.BALANCE(Spec.BEACON_ROOTS_ADDRESS)),
    )
    post = {
        Address(0xCC): Account(
            storage=Storage({0: 0xBA1}),
        )
    }
    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[Transaction(nonce=0, to=Address(0xCC), gas_limit=100000, gas_price=10)])
        ],
        post=post,
    )


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
        current_call_account_address = Address(0x100 + i)

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
                    tx.copy(
                        nonce=i,
                        to=Address(0x100 + i),
                        data=Hash(timestamp),
                    )
                ],
                parent_beacon_block_root=beacon_root,
                timestamp=timestamp,
                withdrawals=[
                    # Also withdraw to the beacon root contract and the system address
                    Withdrawal(
                        address=Spec.BEACON_ROOTS_ADDRESS,
                        amount=1,
                        index=next(withdraw_index),
                        validator_index=0,
                    ),
                    Withdrawal(
                        address=Spec.SYSTEM_ADDRESS,
                        amount=1,
                        index=next(withdraw_index),
                        validator_index=1,
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
        current_call_account_address = Address(0x100 + i)

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
                    tx.copy(
                        nonce=i,
                        to=Address(0x100 + i),
                        data=Hash(timestamp),
                    )
                ],
                parent_beacon_block_root=beacon_root if transitioned else None,
                timestamp=timestamp,
                withdrawals=[
                    # Also withdraw to the beacon root contract and the system address
                    Withdrawal(
                        address=Spec.BEACON_ROOTS_ADDRESS,
                        amount=1,
                        index=next(withdraw_index),
                        validator_index=0,
                    ),
                    Withdrawal(
                        address=Spec.SYSTEM_ADDRESS,
                        amount=1,
                        index=next(withdraw_index),
                        validator_index=1,
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
    caller_address: Address,
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
            parent_beacon_block_root=next(beacon_roots),
            timestamp=timestamp,
            withdrawals=[
                # Also withdraw to the beacon root contract and the system address
                Withdrawal(
                    address=Spec.BEACON_ROOTS_ADDRESS,
                    amount=1,
                    index=0,
                    validator_index=0,
                ),
                Withdrawal(
                    address=Spec.SYSTEM_ADDRESS,
                    amount=1,
                    index=1,
                    validator_index=1,
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
    assert Address(deployer_address) == Spec.BEACON_ROOTS_DEPLOYER_ADDRESS
    blocks: List[Block] = []

    beacon_root_contract_storage: Dict = {}
    for i, current_timestamp in enumerate(range(timestamp // 2, timestamp + 1, timestamp // 2)):
        if i == 0:
            blocks.append(
                Block(  # Deployment block
                    txs=[deploy_tx],
                    parent_beacon_block_root=(
                        beacon_root
                        if fork.header_beacon_root_required(1, current_timestamp)
                        else None
                    ),
                    timestamp=timestamp // 2,
                    withdrawals=[
                        # Also withdraw to the beacon root contract and the system address
                        Withdrawal(
                            address=Spec.BEACON_ROOTS_ADDRESS,
                            amount=1,
                            index=0,
                            validator_index=0,
                        ),
                        Withdrawal(
                            address=Spec.SYSTEM_ADDRESS,
                            amount=1,
                            index=1,
                            validator_index=1,
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
                    parent_beacon_block_root=beacon_root,
                    timestamp=timestamp,
                    withdrawals=[
                        # Also withdraw to the beacon root contract and the system address
                        Withdrawal(
                            address=Spec.BEACON_ROOTS_ADDRESS,
                            amount=1,
                            index=2,
                            validator_index=0,
                        ),
                        Withdrawal(
                            address=Spec.SYSTEM_ADDRESS,
                            amount=1,
                            index=3,
                            validator_index=1,
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

    expected_code = fork.pre_allocation_blockchain()[Spec.BEACON_ROOTS_ADDRESS]["code"]
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
