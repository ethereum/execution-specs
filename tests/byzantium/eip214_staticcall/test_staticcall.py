"""
Tests for EIP-214 STATICCALL opcode behavior.

STATICCALL creates a read-only call context where state-modifying operations
are forbidden. This includes CALL with non-zero value to any address.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    BlockAccessListExpectation,
    Conditional,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    compute_create_address,
)

from .spec import ref_spec_214

REFERENCE_SPEC_GIT_PATH = ref_spec_214.git_path
REFERENCE_SPEC_VERSION = ref_spec_214.version


def bal_marker_storage_changes(
    marker: int, staticcall_result: int
) -> list[BalStorageSlot]:
    """
    Build BAL storage changes for the common pattern of marker slots.

    Most tests write to slots 0, 1, 2 where:
    - slot 0: marker value
    - slot 1: STATICCALL result (0 or 1)
    - slot 2: marker value
    """
    return [
        BalStorageSlot(
            slot=0,
            slot_changes=[
                BalStorageChange(block_access_index=1, post_value=marker)
            ],
        ),
        BalStorageSlot(
            slot=1,
            slot_changes=[
                BalStorageChange(
                    block_access_index=1, post_value=staticcall_result
                )
            ],
        ),
        BalStorageSlot(
            slot=2,
            slot_changes=[
                BalStorageChange(block_access_index=1, post_value=marker)
            ],
        ),
    ]


def bal_expectation_for_contract_with_markers(
    marker: int,
    staticcall_result: int,
    balance_change: int | None = None,
    initial_balance: int = 0,
) -> BalAccountExpectation:
    """
    Build BAL expectation for a contract that writes marker storage slots.

    Args:
        marker: The marker value written to slots 0 and 2
        staticcall_result: The value written to slot 1 (STATICCALL result)
        balance_change: If provided, include a balance change
        initial_balance: The initial balance (for computing post_balance)

    """
    return BalAccountExpectation(
        storage_changes=bal_marker_storage_changes(marker, staticcall_result),
        balance_changes=(
            [
                BalBalanceChange(
                    block_access_index=1,
                    post_balance=initial_balance + balance_change,
                )
            ]
            if balance_change is not None
            else []
        ),
    )


@pytest.mark.with_all_precompiles
@pytest.mark.parametrize(
    "call_value", [0, 2], ids=["zero_value", "nonzero_value"]
)
@pytest.mark.ported_from(
    "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/"
    "stStaticFlagEnabled/StaticcallForPrecompilesIssue683Filler.yml"
)
@pytest.mark.valid_from("Byzantium")
def test_staticcall_reentrant_call_to_precompile(
    pre: Alloc,
    state_test: StateTestFiller,
    precompile: Address,
    call_value: int,
    fork: Fork,
) -> None:
    """
    Test CALL to precompile inside STATICCALL with zero and non-zero value.

    Regression test for ethereum/tests#683.
    Source: https://github.com/ethereum/execution-specs/pull/1960#discussion_r2656834142

    A single contract STATICCALLs itself. On reentry (detected via CALLVALUE=0,
    since STATICCALL doesn't forward value), it attempts CALL to a precompile.

    - call_value=0: CALL succeeds in static context → STATICCALL returns 1
    - call_value>0: CALL violates static context, reverts frame → STATICCALL
      returns 0
    """
    alice = pre.fund_eoa()

    # Contract that STATICCALLs itself on reentry (CALLVALUE=0),
    # attempts CALL to precompile
    target_code = Conditional(
        # CALLVALUE=0 indicates we're inside the STATICCALL (reentry)
        condition=Op.ISZERO(Op.CALLVALUE),
        # try CALL with parametrized value (fails if value > 0)
        if_true=Op.CALL(address=precompile, value=call_value),
        # STATICCALL to self, store result (0=fail, 1=success)
        if_false=Op.SSTORE(0, Op.STATICCALL(address=Op.ADDRESS)),
    )

    target_balance = 1000
    target = pre.deploy_contract(code=target_code, balance=target_balance)

    tx_value = 100
    tx = Transaction(
        sender=alice,
        to=target,
        gas_limit=1_000_000,
        value=tx_value,
        protected=True,
    )

    bal_expectation = None
    if fork.header_bal_hash_required():
        # Target contract always receives tx value
        target_balance_changes = [
            BalBalanceChange(
                block_access_index=1, post_balance=target_balance + tx_value
            )
        ]

        # call_value > 0: SSTORE(0, 0) is a read; call_value == 0: real change
        account_expectations: dict[Address, BalAccountExpectation | None] = {
            target: (
                BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=0,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=1
                                )
                            ],
                        ),
                    ],
                    balance_changes=target_balance_changes,
                )
                if call_value == 0
                else BalAccountExpectation(
                    storage_reads=[0],
                    balance_changes=target_balance_changes,
                )
            ),
        }

        if call_value == 0:
            account_expectations[precompile] = BalAccountExpectation.empty()
        else:
            account_expectations[precompile] = None  # reverted before accessed

        bal_expectation = BlockAccessListExpectation(
            account_expectations=account_expectations
        )

    state_test(
        pre=pre,
        tx=tx,
        expected_block_access_list=bal_expectation,
        post={
            target: Account(
                balance=target_balance + tx_value,
                storage={0: 1 if call_value == 0 else 0},
            ),
        },
    )


@pytest.mark.with_all_precompiles
@pytest.mark.parametrize(
    "call_value", [0, 2], ids=["zero_value", "nonzero_value"]
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stStaticFlagEnabled/CallWithZeroValueToPrecompileFromTransactionFiller.yml",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stStaticFlagEnabled/CallWithNOTZeroValueToPrecompileFromTransactionFiller.yml",
    ],
)
@pytest.mark.valid_from("Byzantium")
def test_staticcall_call_to_precompile(
    pre: Alloc,
    state_test: StateTestFiller,
    precompile: Address,
    call_value: int,
    fork: Fork,
) -> None:
    """
    Test CALL to precompile inside STATICCALL with zero and non-zero value.

    Contract A STATICCALLs contract B. Contract B attempts to CALL precompile.
    With value = 0, this succeeds. With value > 0, this fails (static context).
    """
    alice = pre.fund_eoa()

    initial_contract_balance = 1000
    marker = 0xFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEED

    # Contract B: attempts CALL to precompile with the parametrized value
    contract_b = pre.deploy_contract(
        code=Op.CALL(gas=100_000, address=precompile, value=call_value),
        balance=initial_contract_balance,
    )

    # Contract A: STATICCALLs contract B and stores the result
    contract_a = pre.deploy_contract(
        code=(
            Op.SSTORE(0, marker)
            + Op.SSTORE(1, Op.STATICCALL(gas=200_000, address=contract_b))
            + Op.SSTORE(2, marker)
        ),
        balance=initial_contract_balance,
    )

    tx_value = 100
    staticcall_result = 1 if call_value == 0 else 0

    bal_expectation = None
    if fork.header_bal_hash_required():
        contract_a_balance_changes = [
            BalBalanceChange(
                block_access_index=1,
                post_balance=initial_contract_balance + tx_value,
            )
        ]

        # slot 1 read when call_value > 0
        account_expectations: dict[Address, BalAccountExpectation | None] = {
            contract_a: (
                bal_expectation_for_contract_with_markers(
                    marker=marker,
                    staticcall_result=staticcall_result,
                    balance_change=tx_value,
                    initial_balance=initial_contract_balance,
                )
                if call_value == 0
                else BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=0,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=marker
                                )
                            ],
                        ),
                        BalStorageSlot(
                            slot=2,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=marker
                                )
                            ],
                        ),
                    ],
                    storage_reads=[1],
                    balance_changes=contract_a_balance_changes,
                )
            ),
            contract_b: BalAccountExpectation.empty(),  # STATICCALLed
        }

        if call_value == 0:
            account_expectations[precompile] = BalAccountExpectation.empty()
        else:
            account_expectations[precompile] = None  # reverted before accessed

        bal_expectation = BlockAccessListExpectation(
            account_expectations=account_expectations
        )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=alice,
            to=contract_a,
            gas_limit=500_000,
            value=tx_value,
            protected=True,
        ),
        expected_block_access_list=bal_expectation,
        post={
            contract_a: Account(
                balance=initial_contract_balance + tx_value,
                storage={
                    0: marker,
                    1: staticcall_result,
                    2: marker,
                },
            ),
            contract_b: Account(balance=initial_contract_balance),
        },
    )


@pytest.mark.with_all_precompiles
@pytest.mark.parametrize(
    "call_value", [0, 2], ids=["zero_value", "nonzero_value"]
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stStaticFlagEnabled/CallWithZeroValueToPrecompileFromCalledContractFiller.yml",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stStaticFlagEnabled/CallWithNOTZeroValueToPrecompileFromCalledContractFiller.yml",
    ],
)
@pytest.mark.valid_from("Byzantium")
def test_staticcall_nested_call_to_precompile(
    pre: Alloc,
    state_test: StateTestFiller,
    precompile: Address,
    call_value: int,
    fork: Fork,
) -> None:
    """
    Test STATICCALL behavior with an extra call depth layer.

    Contract B (target) receives tx and CALLs contract A.
    Contract A STATICCALLs contract C.
    Contract C attempts to CALL the precompile.
    With value = 0, this succeeds. With value > 0, this fails (static context).
    """
    alice = pre.fund_eoa()

    initial_contract_balance = 1000
    marker = 0xFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEED

    # Contract C: attempts CALL to precompile with the parametrized value
    contract_c = pre.deploy_contract(
        code=Op.CALL(gas=100_000, address=precompile, value=call_value),
        balance=initial_contract_balance,
    )

    # Contract A: STATICCALLs contract C, stores markers and result
    contract_a = pre.deploy_contract(
        code=(
            Op.SSTORE(0, marker)
            + Op.SSTORE(1, Op.STATICCALL(gas=200_000, address=contract_c))
            + Op.SSTORE(2, marker)
        ),
        balance=initial_contract_balance,
    )

    # Contract B (target): CALLs contract A, stores markers and result
    contract_b = pre.deploy_contract(
        code=(
            Op.SSTORE(0, marker)
            + Op.SSTORE(1, Op.CALL(gas=300_000, address=contract_a))
            + Op.SSTORE(2, marker)
        ),
        balance=initial_contract_balance,
    )

    tx_value = 100
    staticcall_result = 1 if call_value == 0 else 0

    bal_expectation = None
    if fork.header_bal_hash_required():
        # slot 1 read when call_value > 0
        account_expectations: dict[Address, BalAccountExpectation | None] = {
            contract_a: (
                bal_expectation_for_contract_with_markers(
                    marker=marker,
                    staticcall_result=staticcall_result,
                )
                if call_value == 0
                else BalAccountExpectation(
                    storage_changes=[
                        BalStorageSlot(
                            slot=0,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=marker
                                )
                            ],
                        ),
                        BalStorageSlot(
                            slot=2,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=1, post_value=marker
                                )
                            ],
                        ),
                    ],
                    storage_reads=[1],
                )
            ),
            contract_b: bal_expectation_for_contract_with_markers(
                marker=marker,
                staticcall_result=1,  # CALL to A always succeeds
                balance_change=tx_value,
                initial_balance=initial_contract_balance,
            ),
            contract_c: BalAccountExpectation.empty(),  # STATICCALLed
        }

        if call_value == 0:
            account_expectations[precompile] = BalAccountExpectation.empty()
        else:
            account_expectations[precompile] = None  # reverted before accessed

        bal_expectation = BlockAccessListExpectation(
            account_expectations=account_expectations
        )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=alice,
            to=contract_b,
            gas_limit=500_000,
            value=tx_value,
            protected=True,
        ),
        expected_block_access_list=bal_expectation,
        post={
            contract_a: Account(
                balance=initial_contract_balance,
                storage={
                    0: marker,
                    # only succeeds if call_value == 0
                    1: staticcall_result,
                    2: marker,
                },
            ),
            contract_b: Account(
                balance=initial_contract_balance + tx_value,
                storage={
                    0: marker,
                    1: 1,  # CALL to A always succeeds
                    2: marker,
                },
            ),
            contract_c: Account(balance=initial_contract_balance),
        },
    )


@pytest.mark.with_all_precompiles
@pytest.mark.parametrize(
    "call_value", [0, 2], ids=["zero_value", "nonzero_value"]
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stStaticFlagEnabled/CallWithZeroValueToPrecompileFromContractInitializationFiller.yml",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stStaticFlagEnabled/CallWithNOTZeroValueToPrecompileFromContractInitializationFiller.yml",
    ],
)
@pytest.mark.parametrize(
    "create_opcode",
    [
        pytest.param(Op.CREATE, marks=pytest.mark.valid_from("Byzantium")),
        pytest.param(
            Op.CREATE2, marks=pytest.mark.valid_from("Constantinople")
        ),
    ],
)
def test_staticcall_call_to_precompile_from_contract_init(
    pre: Alloc,
    state_test: StateTestFiller,
    precompile: Address,
    call_value: int,
    create_opcode: Op,
    fork: Fork,
) -> None:
    """
    Test STATICCALL behavior during contract initialization (CREATE).

    Contract A CREATEs a new contract whose init code STATICCALLs contract B.
    Contract B attempts to CALL the precompile.
    With value = 0, this succeeds. With value > 0, this fails in static
    context.
    """
    alice = pre.fund_eoa()
    marker = 0xFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEED

    contract_initial_balance = 1000

    # Contract B: attempts CALL to precompile with the parametrized value
    contract_b = pre.deploy_contract(
        code=Op.CALL(gas=100_000, address=precompile, value=call_value),
        balance=contract_initial_balance,
    )

    # Init code: stores markers and STATICCALL result during initialization
    # Note: storage written during init but no return means the created
    # contract will have empty code.
    initcode = (
        Op.SSTORE(0, marker)
        + Op.SSTORE(1, Op.STATICCALL(gas=200_000, address=contract_b))
        + Op.SSTORE(2, marker)
    )

    # Contract A: CREATEs new contract using init_code from calldata
    contract_a = pre.deploy_contract(
        code=(
            Op.SSTORE(0, marker)
            + Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
            + Op.SSTORE(
                1,
                create_opcode(value=0, offset=0, size=Op.CALLDATASIZE),
            )
            + Op.SSTORE(2, marker)
        ),
        balance=contract_initial_balance,
    )
    created_contract = compute_create_address(
        nonce=1,
        address=contract_a,
        opcode=create_opcode,
        initcode=initcode,
    )

    tx_value = 100
    staticcall_result = 1 if call_value == 0 else 0

    bal_expectation = None
    if fork.header_bal_hash_required():
        # stores created_contract in slot 1, receives tx value
        account_expectations: dict[Address, BalAccountExpectation | None] = {
            contract_a: BalAccountExpectation(
                storage_changes=[
                    BalStorageSlot(
                        slot=0,
                        slot_changes=[
                            BalStorageChange(
                                block_access_index=1, post_value=marker
                            )
                        ],
                    ),
                    BalStorageSlot(
                        slot=1,
                        slot_changes=[
                            BalStorageChange(
                                block_access_index=1,
                                post_value=created_contract,
                            )
                        ],
                    ),
                    BalStorageSlot(
                        slot=2,
                        slot_changes=[
                            BalStorageChange(
                                block_access_index=1, post_value=marker
                            )
                        ],
                    ),
                ],
                balance_changes=[
                    BalBalanceChange(
                        block_access_index=1,
                        post_balance=contract_initial_balance + tx_value,
                    )
                ],
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=2)
                ],
            ),
            contract_b: BalAccountExpectation.empty(),  # STATICCALLed
        }

        # slot 1 read when call_value > 0
        created_nonce_changes = [
            BalNonceChange(block_access_index=1, post_nonce=1)
        ]
        account_expectations[created_contract] = (
            BalAccountExpectation(
                storage_changes=bal_marker_storage_changes(
                    marker, staticcall_result
                ),
                nonce_changes=created_nonce_changes,
            )
            if call_value == 0
            else BalAccountExpectation(
                storage_changes=[
                    BalStorageSlot(
                        slot=0,
                        slot_changes=[
                            BalStorageChange(
                                block_access_index=1, post_value=marker
                            )
                        ],
                    ),
                    BalStorageSlot(
                        slot=2,
                        slot_changes=[
                            BalStorageChange(
                                block_access_index=1, post_value=marker
                            )
                        ],
                    ),
                ],
                storage_reads=[1],
                nonce_changes=created_nonce_changes,
            )
        )

        if call_value == 0:
            account_expectations[precompile] = BalAccountExpectation.empty()
        else:
            account_expectations[precompile] = None  # reverted before accessed

        bal_expectation = BlockAccessListExpectation(
            account_expectations=account_expectations
        )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=alice,
            to=contract_a,
            gas_limit=4_000_000,
            value=tx_value,
            data=bytes(initcode),
            protected=True,
        ),
        expected_block_access_list=bal_expectation,
        post={
            contract_a: Account(
                balance=contract_initial_balance + tx_value,
                storage={0: marker, 1: created_contract, 2: marker},
            ),
            created_contract: Account(
                storage={
                    0: marker,
                    # only succeeds if call_value == 0
                    1: staticcall_result,
                    2: marker,
                },
                code=b"",
            ),
            contract_b: Account(balance=contract_initial_balance),
        },
    )
