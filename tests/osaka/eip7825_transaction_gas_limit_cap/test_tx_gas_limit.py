"""
Transaction gas limit cap tests.

Tests for transaction gas limit cap in [EIP-7825: Transaction Gas Limit
Cap](https://eips.ethereum.org/EIPS/eip-7825).

Note: Most tests are limited to Osaka (valid_at/valid_until) because EIP-8037
allows tx.gas_limit > TX_MAX_GAS_LIMIT with excess going to
state_gas_reservoir, changing the expected validation behavior.
"""

from typing import List

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Environment,
    Fork,
    Hash,
    Op,
    ParameterSet,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
    TransactionReceipt,
    add_kzg_version,
    max_count_with_gas_limit,
)

from .spec import Spec, ref_spec_7825

# Update reference spec constants
REFERENCE_SPEC_GIT_PATH = ref_spec_7825.git_path
REFERENCE_SPEC_VERSION = ref_spec_7825.version


def tx_gas_limit_cap_tests(fork: Fork) -> List[ParameterSet]:
    """
    Return a list of tests for transaction gas limit cap parametrized for each
    different fork.
    """
    fork_tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    if fork_tx_gas_limit_cap is None:
        # Use a default value for forks that don't have a transaction gas limit
        # cap
        return [
            pytest.param(
                Spec.tx_gas_limit_cap + 1, None, id="tx_gas_limit_cap_none"
            ),
        ]

    if fork.state_gas_reservoir_enabled():
        return [
            pytest.param(fork_tx_gas_limit_cap, None, id="at_cap"),
            pytest.param(fork_tx_gas_limit_cap + 1, None, id="above_cap"),
        ]

    return [
        pytest.param(
            fork_tx_gas_limit_cap + 1,
            TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM,
            id="tx_gas_limit_cap_exceeds_maximum",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(fork_tx_gas_limit_cap, None, id="tx_gas_limit_cap_over"),
    ]


@pytest.mark.inclusion_test
@pytest.mark.parametrize_by_fork("tx_gas_limit,error", tx_gas_limit_cap_tests)
@pytest.mark.with_all_tx_types
@pytest.mark.valid_from("Prague")
@pytest.mark.valid_before("EIP8037")
def test_transaction_gas_limit_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_gas_limit: int,
    error: TransactionException | None,
    tx_type: int,
) -> None:
    """Test the transaction gas limit cap for all transaction types."""
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
        tx_kwargs["blob_versioned_hashes"] = add_kzg_version(
            [0], Spec.blob_commitment_version_kzg
        )
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
    post = {
        contract_address: Account(storage=storage if error is None else {})
    }

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
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    fork: Fork,
    env: Environment,
) -> None:
    """Test the transaction gas limit cap behavior for subcall context."""
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    assert tx_gas_limit_cap is not None, (
        "Fork does not have a transaction gas limit cap"
    )

    caller_address = pre.deploy_contract(
        code=Op.SSTORE(
            0,
            opcode(
                gas=tx_gas_limit_cap + 1,
                address=pre.deploy_contract(
                    code=Op.MSTORE(0, Op.GAS) + Op.RETURN(0, 0x20)
                ),
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


@pytest.mark.inclusion_test
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
) -> None:
    """
    Test multiple transactions with total gas larger than the block gas limit.
    """
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    assert tx_gas_limit_cap is not None, (
        "Fork does not have a transaction gas limit cap"
    )

    tx_count = env.gas_limit // tx_gas_limit_cap

    gas_spender_contract = pre.deploy_contract(code=Op.INVALID)
    block = Block(
        txs=[
            Transaction(
                to=gas_spender_contract,
                sender=pre.fund_eoa(),
                gas_limit=tx_gas_limit_cap,
                error=TransactionException.GAS_ALLOWANCE_EXCEEDED
                if i >= tx_count
                else None,
            )
            for i in range(tx_count + int(exceed_block_gas_limit))
        ],
        exception=TransactionException.GAS_ALLOWANCE_EXCEEDED
        if exceed_block_gas_limit
        else None,
    )

    blockchain_test(pre=pre, post={}, blocks=[block])


@pytest.mark.parametrize(
    "exceed_gas_refund_limit",
    [
        pytest.param(True),
        pytest.param(False),
    ],
)
@pytest.mark.valid_from("Osaka")
def test_maximum_gas_refund(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    exceed_gas_refund_limit: bool,
) -> None:
    """Test the maximum gas refund behavior according to EIP-3529."""
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    assert tx_gas_limit_cap is not None
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()()
    refund_quotient = fork.max_refund_quotient()

    def memory_expansion(words: int) -> Bytecode:
        return Op.MSTORE.with_metadata(
            new_memory_size=32 * (words + 1), old_memory_size=0
        )(32 * words, 0)

    # Spend half the cap without generating refunds, then find the storage
    # clearing count immediately below or above the actual refund ceiling.
    memory_words = max_count_with_gas_limit(
        lambda words: intrinsic_cost + memory_expansion(words).gas_cost(fork),
        tx_gas_limit_cap // 2,
    )
    burn_code = memory_expansion(memory_words)
    base_cost = intrinsic_cost + burn_code.gas_cost(fork)

    def clear_storage(count: int) -> Bytecode:
        return sum(
            (
                Op.SSTORE.with_metadata(
                    key_warm=False, original_value=1, new_value=0
                )(slot, Op.PUSH0)
                for slot in range(count)
            ),
            Bytecode(),
        )

    max_storage_count = max_count_with_gas_limit(
        lambda count: base_cost + clear_storage(count).gas_cost(fork),
        tx_gas_limit_cap,
    )
    # refund <= gas_used // quotient iff refund * quotient <= gas_used.
    refund_boundary = max_count_with_gas_limit(
        lambda count: clear_storage(count).refund(fork) * refund_quotient
        - clear_storage(count).gas_cost(fork),
        base_cost,
        max_count=max_storage_count - 1,
    )
    iteration_count = refund_boundary + int(exceed_gas_refund_limit)
    opcode = burn_code + clear_storage(iteration_count)
    gas_used = intrinsic_cost + opcode.gas_cost(fork)
    refund = opcode.refund(fork)
    maximum_refund = gas_used // refund_quotient
    assert (refund > maximum_refund) == exceed_gas_refund_limit
    assert gas_used <= tx_gas_limit_cap
    assert len(opcode) <= fork.max_code_size()

    contract = pre.deploy_contract(
        code=opcode,
        storage=dict.fromkeys(range(iteration_count), 1),
    )
    tx = Transaction(
        to=contract,
        sender=pre.fund_eoa(),
        gas_limit=tx_gas_limit_cap,
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=gas_used - min(refund, maximum_refund)
        ),
    )
    state_test(
        pre=pre,
        post={
            contract: Account(storage=dict.fromkeys(range(iteration_count), 0))
        },
        tx=tx,
    )


@pytest.mark.inclusion_test
@pytest.mark.bigmem
@pytest.mark.xdist_group(name="bigmem")
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
@pytest.mark.valid_before("EIP8037")
@pytest.mark.eels_base_coverage
def test_tx_gas_limit_cap_full_calldata(
    state_test: StateTestFiller,
    pre: Alloc,
    zero_byte: bool,
    exceed_tx_gas_limit: bool,
    correct_intrinsic_cost_in_transaction_gas_limit: bool,
    fork: Fork,
) -> None:
    """Test the transaction gas limit cap behavior for full calldata."""
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    assert tx_gas_limit_cap is not None, (
        "Fork does not have a transaction gas limit cap"
    )
    byte_data = b"\x00" if zero_byte else b"\xff"
    max_num_of_bytes = max_count_with_gas_limit(
        lambda calldata_size: intrinsic_cost(
            calldata=byte_data * calldata_size
        ),
        tx_gas_limit_cap,
    )
    num_of_bytes = max_num_of_bytes + int(exceed_tx_gas_limit)

    correct_intrinsic_cost = intrinsic_cost(calldata=byte_data * num_of_bytes)
    if exceed_tx_gas_limit:
        assert correct_intrinsic_cost > tx_gas_limit_cap, (
            "Correct intrinsic cost should exceed the tx gas limit cap"
        )
    else:
        assert correct_intrinsic_cost <= tx_gas_limit_cap, (
            "Correct intrinsic cost should be less than or "
            "equal to the tx gas limit cap"
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
        if correct_intrinsic_cost_in_transaction_gas_limit
        and exceed_tx_gas_limit
        else TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST
        if exceed_tx_gas_limit
        else None,
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.inclusion_test
@pytest.mark.parametrize_by_fork("tx_gas_limit,error", tx_gas_limit_cap_tests)
@pytest.mark.valid_from("Osaka")
def test_tx_gas_limit_cap_contract_creation(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    error: TransactionException | None,
    fork: Fork,
) -> None:
    """Test the transaction gas limit cap behavior for contract creation."""
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    assert tx_gas_limit_cap is not None, (
        "Fork does not have a transaction gas limit cap"
    )
    top_frame_cost = fork.transaction_top_frame_gas_calculator()(
        contract_creation=True
    )

    def creation_cost(size: int) -> int:
        initcode = Op.JUMPDEST * size
        return max(
            intrinsic_cost(contract_creation=True, calldata=initcode),
            intrinsic_cost(
                contract_creation=True,
                calldata=initcode,
                return_cost_deducted_prior_execution=True,
            )
            + top_frame_cost
            + initcode.gas_cost(fork),
        )

    num_of_bytes = max_count_with_gas_limit(
        creation_cost,
        tx_gas_limit_cap,
        max_count=fork.max_initcode_size(),
    )
    tx = Transaction(
        to=None,
        data=Op.JUMPDEST * num_of_bytes,
        gas_limit=tx_gas_limit,
        sender=pre.fund_eoa(),
        error=error,
    )
    state_test(
        pre=pre,
        post={tx.created_contract: Account(nonce=1, code=b"")}
        if error is None
        else {},
        tx=tx,
    )


@pytest.mark.inclusion_test
@pytest.mark.parametrize(
    "exceed_tx_gas_limit,correct_intrinsic_cost_in_transaction_gas_limit",
    [
        pytest.param(True, False, marks=pytest.mark.exception_test),
        pytest.param(True, True, marks=pytest.mark.exception_test),
        pytest.param(False, True),
    ],
)
@pytest.mark.valid_from("Osaka")
@pytest.mark.valid_before("EIP8037")
def test_tx_gas_limit_cap_access_list_with_diff_keys(
    state_test: StateTestFiller,
    exceed_tx_gas_limit: bool,
    correct_intrinsic_cost_in_transaction_gas_limit: bool,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test the transaction gas limit cap behavior for access list with different
    storage keys.
    """
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    assert tx_gas_limit_cap is not None, (
        "Fork does not have a transaction gas limit cap"
    )
    access_address = Address("0x1234567890123456789012345678901234567890")

    def intrinsic_cost_for_num_storage_keys(storage_key_count: int) -> int:
        return intrinsic_cost(
            access_list=[
                AccessList(
                    address=access_address,
                    storage_keys=[Hash(i) for i in range(storage_key_count)],
                )
            ]
        )

    num_storage_keys = max_count_with_gas_limit(
        intrinsic_cost_for_num_storage_keys, tx_gas_limit_cap
    ) + int(exceed_tx_gas_limit)
    storage_keys = [Hash(i) for i in range(num_storage_keys)]

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
            "Correct intrinsic cost should be less than or "
            "equal to the tx gas limit cap"
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
        if correct_intrinsic_cost_in_transaction_gas_limit
        and exceed_tx_gas_limit
        else TransactionException.INTRINSIC_GAS_TOO_LOW
        if exceed_tx_gas_limit
        else None,
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.inclusion_test
@pytest.mark.parametrize(
    "exceed_tx_gas_limit,correct_intrinsic_cost_in_transaction_gas_limit",
    [
        pytest.param(True, False, marks=pytest.mark.exception_test),
        pytest.param(True, True, marks=pytest.mark.exception_test),
        pytest.param(False, True),
    ],
)
@pytest.mark.valid_from("Osaka")
@pytest.mark.valid_before("EIP8037")
def test_tx_gas_limit_cap_access_list_with_diff_addr(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    exceed_tx_gas_limit: bool,
    correct_intrinsic_cost_in_transaction_gas_limit: bool,
) -> None:
    """
    Test the transaction gas limit cap behavior for access list with different
    addresses.
    """
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    assert tx_gas_limit_cap is not None, (
        "Fork does not have a transaction gas limit cap"
    )

    def make_access_list(account_count: int) -> List[AccessList]:
        return [
            AccessList(
                address=Address(i + 1),
                storage_keys=[Hash(i)],
            )
            for i in range(account_count)
        ]

    def intrinsic_cost_for_num_accounts(account_count: int) -> int:
        return intrinsic_cost(access_list=make_access_list(account_count))

    account_num = max_count_with_gas_limit(
        intrinsic_cost_for_num_accounts, tx_gas_limit_cap
    ) + int(exceed_tx_gas_limit)
    access_list = make_access_list(account_num)

    correct_intrinsic_cost = intrinsic_cost(access_list=access_list)
    if exceed_tx_gas_limit:
        assert correct_intrinsic_cost > tx_gas_limit_cap, (
            "Correct intrinsic cost should exceed the tx gas limit cap"
        )
    else:
        assert correct_intrinsic_cost <= tx_gas_limit_cap, (
            "Correct intrinsic cost should be less than or "
            "equal to the tx gas limit cap"
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
        if correct_intrinsic_cost_in_transaction_gas_limit
        and exceed_tx_gas_limit
        else TransactionException.INTRINSIC_GAS_TOO_LOW
        if exceed_tx_gas_limit
        else None,
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
    )


@pytest.mark.inclusion_test
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
) -> None:
    """Test a transaction limit cap with authorized tx."""
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    assert tx_gas_limit_cap is not None, (
        "Fork does not have a transaction gas limit cap"
    )

    def make_access_list(auth_count: int) -> List[AccessList]:
        return [
            AccessList(
                address=Address(i + 1),
                storage_keys=[],
            )
            for i in range(auth_count)
        ]

    def capped_intrinsic_cost(auth_count: int) -> int:
        """Return the intrinsic gas that counts toward the cap."""
        cost = intrinsic_cost(
            access_list=make_access_list(auth_count),
            authorization_list_or_count=auth_count,
        )
        return cost

    auth_list_length = max_count_with_gas_limit(
        capped_intrinsic_cost, tx_gas_limit_cap
    ) + int(exceed_tx_gas_limit)

    # EIP-7702 authorization transaction cost:
    # 21000 + 16 * non-zero calldata bytes + 4 * zero calldata bytes + 1900 *
    # access list storage key count + 2400 * access list address count + access
    # list data cost + AUTH_PER_EMPTY_ACCOUNT_COST * authorization list
    # length
    #
    # There is no calldata and no storage keys in this test case.
    # However, each access-list address includes data bytes that may contribute
    # additional cost depending on fork repricing.

    auth_address = pre.deploy_contract(code=Op.STOP)

    access_list = make_access_list(auth_list_length)
    auth_signers = [pre.fund_eoa() for _ in range(auth_list_length)]

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
    correct_capped_cost = capped_intrinsic_cost(auth_list_length)
    if exceed_tx_gas_limit:
        assert correct_capped_cost > tx_gas_limit_cap, (
            "Correct capped intrinsic cost should exceed the tx gas limit cap"
        )
    else:
        assert correct_capped_cost <= tx_gas_limit_cap, (
            "Correct capped intrinsic cost should be less than or "
            "equal to the tx gas limit cap"
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
        # EIP-8037 reports a cap overflow as INTRINSIC_GAS_TOO_LOW.
        error=(
            TransactionException.INTRINSIC_GAS_TOO_LOW
            if fork.is_eip_enabled(8037)
            else TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM
        )
        if correct_intrinsic_cost_in_transaction_gas_limit
        and exceed_tx_gas_limit
        else TransactionException.INTRINSIC_GAS_TOO_LOW
        if exceed_tx_gas_limit
        else None,
    )

    env = Environment()
    if fork.is_eip_enabled(8037):
        # Size the block so it fits the state reservoir.
        env = Environment(gas_limit=correct_intrinsic_cost)

    state_test(
        env=env,
        pre=pre,
        post={},
        tx=tx,
    )
