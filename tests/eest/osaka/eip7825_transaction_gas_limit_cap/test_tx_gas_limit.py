"""
abstract: Tests [EIP-7825 Transaction Gas Limit Cap](https://eips.ethereum.org/EIPS/eip-7825)
    Test cases for [EIP-7825 Transaction Gas Limit Cap](https://eips.ethereum.org/EIPS/eip-7825)].
"""

from typing import List

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    AccessList,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Environment,
    Hash,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
    add_kzg_version,
)
from ethereum_test_tools.utility.pytest import ParameterSet
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .spec import Spec, ref_spec_7825

# Update reference spec constants
REFERENCE_SPEC_GIT_PATH = ref_spec_7825.git_path
REFERENCE_SPEC_VERSION = ref_spec_7825.version


def tx_gas_limit_cap_tests(fork: Fork) -> List[ParameterSet]:
    """
    Return a list of tests for transaction gas limit cap parametrized for each different
    fork.
    """
    fork_tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    if fork_tx_gas_limit_cap is None:
        # Use a default value for forks that don't have a transaction gas limit cap
        return [
            pytest.param(Spec.tx_gas_limit_cap + 1, None, id="tx_gas_limit_cap_none"),
        ]

    return [
        pytest.param(
            fork_tx_gas_limit_cap + 1,
            TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM,
            id="tx_gas_limit_cap_exceeds_maximum",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(fork_tx_gas_limit_cap, None, id="tx_gas_limit_cap_none"),
    ]


@pytest.mark.parametrize_by_fork("tx_gas_limit,error", tx_gas_limit_cap_tests)
@pytest.mark.with_all_tx_types
@pytest.mark.valid_from("Prague")
def test_transaction_gas_limit_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_gas_limit: int,
    error: TransactionException | None,
    tx_type: int,
):
    """Test the transaction gas limit cap behavior for all transaction types."""
    env = Environment()

    sender = pre.fund_eoa()
    storage = Storage()
    contract_address = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), 1) + Op.STOP,
    )

    tx_kwargs = {
        "ty": tx_type,
        "to": contract_address,
        "gas_limit": tx_gas_limit,
        "data": b"",
        "value": 0,
        "sender": sender,
        "error": error,
    }

    # Add extra required fields based on transaction type
    if tx_type >= 1:
        # Type 1: EIP-2930 Access List Transaction
        tx_kwargs["access_list"] = [
            {
                "address": contract_address,
                "storage_keys": [0],
            }
        ]
    if tx_type == 3:
        # Type 3: EIP-4844 Blob Transaction
        tx_kwargs["max_fee_per_blob_gas"] = fork.min_base_fee_per_blob_gas()
        tx_kwargs["blob_versioned_hashes"] = add_kzg_version([0], Spec.blob_commitment_version_kzg)
    elif tx_type == 4:
        # Type 4: EIP-7702 Set Code Transaction
        signer = pre.fund_eoa(amount=0)
        tx_kwargs["authorization_list"] = [
            AuthorizationTuple(
                signer=signer,
                address=Address(0),
                nonce=0,
            )
        ]

    tx = Transaction(**tx_kwargs)
    post = {contract_address: Account(storage=storage if error is None else {})}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.CALL),
        pytest.param(Op.DELEGATECALL),
        pytest.param(Op.CALLCODE),
        pytest.param(Op.STATICCALL),
    ],
)
@pytest.mark.valid_from("Osaka")
def test_tx_gas_limit_cap_subcall_context(
    state_test: StateTestFiller, pre: Alloc, opcode: Op, fork: Fork, env: Environment
):
    """Test the transaction gas limit cap behavior for subcall context."""
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    assert tx_gas_limit_cap is not None, "Fork does not have a transaction gas limit cap"

    caller_address = pre.deploy_contract(
        code=Op.SSTORE(
            0,
            opcode(
                gas=tx_gas_limit_cap + 1,
                address=pre.deploy_contract(code=Op.MSTORE(0, Op.GAS) + Op.RETURN(0, 0x20)),
                ret_offset=0,
                ret_size=0,
            ),
        )
    )

    # Passing tx limit cap as the gas parameter to *CALL operations
    # All tests should pass and the *CALL operations should succeed
    # Gas forwarded = min(remaining gas, specified gas parameter)

    tx = Transaction(
        to=caller_address,
        sender=pre.fund_eoa(),
        gas_limit=tx_gas_limit_cap,
    )

    post = {
        caller_address: Account(storage={"0x00": 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "exceed_block_gas_limit",
    [
        pytest.param(True, marks=pytest.mark.exception_test),
        pytest.param(False),
    ],
)
@pytest.mark.valid_from("Osaka")
def test_tx_gas_larger_than_block_gas_limit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    env: Environment,
    fork: Fork,
    exceed_block_gas_limit: bool,
):
    """Test multiple transactions with total gas larger than the block gas limit."""
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    assert tx_gas_limit_cap is not None, "Fork does not have a transaction gas limit cap"

    tx_count = env.gas_limit // tx_gas_limit_cap

    gas_spender_contract = pre.deploy_contract(code=Op.INVALID)
    block = Block(
        txs=[
            Transaction(
                to=gas_spender_contract,
                sender=pre.fund_eoa(),
                gas_limit=tx_gas_limit_cap,
                error=TransactionException.GAS_ALLOWANCE_EXCEEDED if i >= tx_count else None,
            )
            for i in range(tx_count + int(exceed_block_gas_limit))
        ],
        exception=TransactionException.GAS_ALLOWANCE_EXCEEDED if exceed_block_gas_limit else None,
    )

    blockchain_test(env=env, pre=pre, post={}, blocks=[block])


@pytest.fixture
def total_cost_floor_per_token(fork: Fork):
    """Total cost floor per token."""
    gas_costs = fork.gas_costs()
    return gas_costs.G_TX_DATA_FLOOR_TOKEN_COST


@pytest.mark.parametrize(
    "exceed_tx_gas_limit,correct_intrinsic_cost_in_transaction_gas_limit",
    [
        pytest.param(True, False, marks=pytest.mark.exception_test),
        pytest.param(True, True, marks=pytest.mark.exception_test),
        pytest.param(False, True),
    ],
)
@pytest.mark.parametrize("zero_byte", [True, False])
@pytest.mark.valid_from("Osaka")
def test_tx_gas_limit_cap_full_calldata(
    state_test: StateTestFiller,
    pre: Alloc,
    zero_byte: bool,
    total_cost_floor_per_token: int,
    exceed_tx_gas_limit: bool,
    correct_intrinsic_cost_in_transaction_gas_limit: bool,
    fork: Fork,
):
    """Test the transaction gas limit cap behavior for full calldata."""
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    assert tx_gas_limit_cap is not None, "Fork does not have a transaction gas limit cap"
    gas_available = tx_gas_limit_cap - intrinsic_cost()

    max_tokens_in_calldata = gas_available // total_cost_floor_per_token
    num_of_bytes = max_tokens_in_calldata if zero_byte else max_tokens_in_calldata // 4

    num_of_bytes += int(exceed_tx_gas_limit)

    # Gas cost calculation based on EIP-7623: (https://eips.ethereum.org/EIPS/eip-7623)
    #
    # Simplified in this test case:
    # - No execution gas used (no opcodes are executed)
    # - Not a contract creation (no initcode)
    #
    # Token accounting:
    #   tokens_in_calldata = zero_bytes + 4 * non_zero_bytes

    byte_data = b"\x00" if zero_byte else b"\xff"

    correct_intrinsic_cost = intrinsic_cost(calldata=byte_data * num_of_bytes)
    if exceed_tx_gas_limit:
        assert correct_intrinsic_cost > tx_gas_limit_cap, (
            "Correct intrinsic cost should exceed the tx gas limit cap"
        )
    else:
        assert correct_intrinsic_cost <= tx_gas_limit_cap, (
            "Correct intrinsic cost should be less than or equal to the tx gas limit cap"
        )

    tx_gas_limit = (
        correct_intrinsic_cost
        if correct_intrinsic_cost_in_transaction_gas_limit
        else tx_gas_limit_cap
    )

    tx = Transaction(
        to=pre.fund_eoa(),
        data=byte_data * num_of_bytes,
        gas_limit=tx_gas_limit,
        sender=pre.fund_eoa(),
        error=TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM
        if correct_intrinsic_cost_in_transaction_gas_limit and exceed_tx_gas_limit
        else TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST
        if exceed_tx_gas_limit
        else None,
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.parametrize(
    "exceed_tx_gas_limit",
    [
        pytest.param(True),
        pytest.param(False),
    ],
)
@pytest.mark.valid_from("Osaka")
def test_tx_gas_limit_cap_contract_creation(
    state_test: StateTestFiller,
    pre: Alloc,
    total_cost_floor_per_token: int,
    exceed_tx_gas_limit: bool,
    fork: Fork,
):
    """Test the transaction gas limit cap behavior for contract creation."""
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    assert tx_gas_limit_cap is not None, "Fork does not have a transaction gas limit cap"
    gas_available = tx_gas_limit_cap - intrinsic_cost(contract_creation=True)

    max_tokens_in_calldata = gas_available // total_cost_floor_per_token
    num_of_bytes = (max_tokens_in_calldata // 4) + int(exceed_tx_gas_limit)

    # Cannot exceed max contract code size
    num_of_bytes = min(num_of_bytes, fork.max_code_size())

    code = Op.JUMPDEST * num_of_bytes

    # Craft a contract creation transaction that exceeds the transaction gas limit cap
    #
    # Total cost =
    # intrinsic cost (base tx cost + contract creation cost)
    # + calldata cost
    # + init code execution cost
    #
    # The contract body is filled with JUMPDEST instructions, so:
    # total cost = intrinsic cost + calldata cost + (num_of_jumpdest * 1 gas)
    #
    # If the total cost exceeds the tx limit cap, the transaction should fail

    total_cost = intrinsic_cost(contract_creation=True, calldata=code) + num_of_bytes

    tx = Transaction(
        to=None,
        data=code,
        gas_limit=tx_gas_limit_cap,
        sender=pre.fund_eoa(),
        error=TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST
        if total_cost > tx_gas_limit_cap
        else None,
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.parametrize(
    "exceed_tx_gas_limit,correct_intrinsic_cost_in_transaction_gas_limit",
    [
        pytest.param(True, False, marks=pytest.mark.exception_test),
        pytest.param(True, True, marks=pytest.mark.exception_test),
        pytest.param(False, True),
    ],
)
@pytest.mark.valid_from("Osaka")
def test_tx_gas_limit_cap_access_list_with_diff_keys(
    state_test: StateTestFiller,
    exceed_tx_gas_limit: bool,
    correct_intrinsic_cost_in_transaction_gas_limit: bool,
    pre: Alloc,
    fork: Fork,
):
    """Test the transaction gas limit cap behavior for access list with different storage keys."""
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    assert tx_gas_limit_cap is not None, "Fork does not have a transaction gas limit cap"
    gas_available = tx_gas_limit_cap - intrinsic_cost()

    gas_costs = fork.gas_costs()
    gas_per_address = gas_costs.G_ACCESS_LIST_ADDRESS
    gas_per_storage_key = gas_costs.G_ACCESS_LIST_STORAGE

    gas_after_address = gas_available - gas_per_address
    num_storage_keys = gas_after_address // gas_per_storage_key + int(exceed_tx_gas_limit)

    access_address = Address("0x1234567890123456789012345678901234567890")
    storage_keys = []
    for i in range(num_storage_keys):
        storage_keys.append(Hash(i))

    access_list = [
        AccessList(
            address=access_address,
            storage_keys=storage_keys,
        )
    ]

    correct_intrinsic_cost = intrinsic_cost(access_list=access_list)
    if exceed_tx_gas_limit:
        assert correct_intrinsic_cost > tx_gas_limit_cap, (
            "Correct intrinsic cost should exceed the tx gas limit cap"
        )
    else:
        assert correct_intrinsic_cost <= tx_gas_limit_cap, (
            "Correct intrinsic cost should be less than or equal to the tx gas limit cap"
        )

    tx_gas_limit = (
        correct_intrinsic_cost
        if correct_intrinsic_cost_in_transaction_gas_limit
        else tx_gas_limit_cap
    )

    tx = Transaction(
        to=pre.fund_eoa(),
        gas_limit=tx_gas_limit,
        sender=pre.fund_eoa(),
        access_list=access_list,
        error=TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM
        if correct_intrinsic_cost_in_transaction_gas_limit and exceed_tx_gas_limit
        else TransactionException.INTRINSIC_GAS_TOO_LOW
        if exceed_tx_gas_limit
        else None,
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.parametrize(
    "exceed_tx_gas_limit,correct_intrinsic_cost_in_transaction_gas_limit",
    [
        pytest.param(True, False, marks=pytest.mark.exception_test),
        pytest.param(True, True, marks=pytest.mark.exception_test),
        pytest.param(False, True),
    ],
)
@pytest.mark.valid_from("Osaka")
def test_tx_gas_limit_cap_access_list_with_diff_addr(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    exceed_tx_gas_limit: bool,
    correct_intrinsic_cost_in_transaction_gas_limit: bool,
):
    """Test the transaction gas limit cap behavior for access list with different addresses."""
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    assert tx_gas_limit_cap is not None, "Fork does not have a transaction gas limit cap"
    gas_available = tx_gas_limit_cap - intrinsic_cost()

    gas_costs = fork.gas_costs()
    gas_per_address = gas_costs.G_ACCESS_LIST_ADDRESS
    gas_per_storage_key = gas_costs.G_ACCESS_LIST_STORAGE

    account_num = gas_available // (gas_per_address + gas_per_storage_key) + int(
        exceed_tx_gas_limit
    )

    access_list = [
        AccessList(
            address=pre.fund_eoa(),
            storage_keys=[Hash(i)],
        )
        for i in range(account_num)
    ]

    correct_intrinsic_cost = intrinsic_cost(access_list=access_list)
    if exceed_tx_gas_limit:
        assert correct_intrinsic_cost > tx_gas_limit_cap, (
            "Correct intrinsic cost should exceed the tx gas limit cap"
        )
    else:
        assert correct_intrinsic_cost <= tx_gas_limit_cap, (
            "Correct intrinsic cost should be less than or equal to the tx gas limit cap"
        )

    tx_gas_limit = (
        correct_intrinsic_cost
        if correct_intrinsic_cost_in_transaction_gas_limit
        else tx_gas_limit_cap
    )

    tx = Transaction(
        to=pre.fund_eoa(),
        gas_limit=tx_gas_limit,
        sender=pre.fund_eoa(),
        access_list=access_list,
        error=TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM
        if correct_intrinsic_cost_in_transaction_gas_limit and exceed_tx_gas_limit
        else TransactionException.INTRINSIC_GAS_TOO_LOW
        if exceed_tx_gas_limit
        else None,
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.parametrize(
    "exceed_tx_gas_limit,correct_intrinsic_cost_in_transaction_gas_limit",
    [
        pytest.param(True, False, marks=pytest.mark.exception_test),
        pytest.param(True, True, marks=pytest.mark.exception_test),
        pytest.param(False, True),
    ],
)
@pytest.mark.valid_from("Osaka")
def test_tx_gas_limit_cap_authorized_tx(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    exceed_tx_gas_limit: bool,
    correct_intrinsic_cost_in_transaction_gas_limit: bool,
):
    """Test a transaction limit cap with authorized tx."""
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    assert tx_gas_limit_cap is not None, "Fork does not have a transaction gas limit cap"
    gas_available = tx_gas_limit_cap - intrinsic_cost()

    gas_costs = fork.gas_costs()
    gas_per_address = gas_costs.G_ACCESS_LIST_ADDRESS

    per_empty_account_cost = 25_000
    auth_list_length = gas_available // (gas_per_address + per_empty_account_cost) + int(
        exceed_tx_gas_limit
    )

    # EIP-7702 authorization transaction cost:
    #
    # 21000 + 16 * non-zero calldata bytes + 4 * zero calldata bytes
    # + 1900 * access list storage key count
    # + 2400 * access list address count
    # + PER_EMPTY_ACCOUNT_COST * authorization list length
    #
    # There is no calldata and no storage keys in this test case
    # and the access address list count is equal to the authorization list length
    # total cost = 21000 + (2400 + 25_000) * auth_list_length

    auth_address = pre.deploy_contract(code=Op.STOP)

    auth_signers = [pre.fund_eoa() for _ in range(auth_list_length)]

    access_list = [
        AccessList(
            address=addr,
            storage_keys=[],
        )
        for addr in auth_signers
    ]

    auth_tuples = [
        AuthorizationTuple(
            signer=signer,
            address=auth_address,
            nonce=signer.nonce,
        )
        for signer in auth_signers
    ]

    correct_intrinsic_cost = intrinsic_cost(
        access_list=access_list, authorization_list_or_count=auth_list_length
    )
    if exceed_tx_gas_limit:
        assert correct_intrinsic_cost > tx_gas_limit_cap, (
            "Correct intrinsic cost should exceed the tx gas limit cap"
        )
    else:
        assert correct_intrinsic_cost <= tx_gas_limit_cap, (
            "Correct intrinsic cost should be less than or equal to the tx gas limit cap"
        )

    tx_gas_limit = (
        correct_intrinsic_cost
        if correct_intrinsic_cost_in_transaction_gas_limit
        else tx_gas_limit_cap
    )

    tx = Transaction(
        to=pre.fund_eoa(),
        gas_limit=tx_gas_limit,
        sender=pre.fund_eoa(),
        access_list=access_list,
        authorization_list=auth_tuples,
        error=TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM
        if correct_intrinsic_cost_in_transaction_gas_limit and exceed_tx_gas_limit
        else TransactionException.INTRINSIC_GAS_TOO_LOW
        if exceed_tx_gas_limit
        else None,
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )
