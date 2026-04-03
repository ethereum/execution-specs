"""
Test that CREATE/CREATE2 do not warm the contract address on aborted calls.

When a CREATE or CREATE2 is aborted before execution (due to insufficient
balance or sender nonce overflow), the would-be contract address must NOT
be added to the warm access set. This was a bug in the original spec where
the address was warmed before validation checks.

Note: call depth overflow (the third abort condition in the spec) is not
tested here because EIP-150's 63/64 gas forwarding rule makes it infeasible
to reach the 1024 call depth limit — gas is exhausted around depth ~300.
The depth check shares the same `if` block as the balance and nonce checks,
so it is implicitly covered.

See https://github.com/ethereum/execution-specs/issues/1019 and
https://github.com/ethereum/execution-specs/issues/1541.

Tests for [EIP-2929: Gas cost increases for state access opcodes]
    (https://eips.ethereum.org/EIPS/eip-2929).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    CodeGasMeasure,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    compute_create_address,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-2929.md"
REFERENCE_SPEC_VERSION = "0e11417265a623adb680c527b15d0cb6701b870b"


@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "create_opcode",
    [
        pytest.param(Op.CREATE, id="CREATE"),
        pytest.param(Op.CREATE2, id="CREATE2"),
    ],
)
def test_create_insufficient_balance(
    state_test: StateTestFiller,
    pre: Alloc,
    env: Environment,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Test that a failed CREATE/CREATE2 due to insufficient balance does not
    warm the contract address.

    A creator contract with zero balance attempts to create with value=1.
    The create aborts, and a subsequent BALANCE check on the would-be
    contract address verifies it remains cold (costs G_COLD_ACCOUNT_ACCESS
    instead of G_WARM_STORAGE_READ).
    """
    initcode = Op.STOP

    creator_code = Op.MSTORE(
        0, Op.PUSH32(bytes(initcode).ljust(32, b"\0"))
    ) + Op.SSTORE(
        0,
        create_opcode(value=1, offset=0, size=len(initcode)),
    )

    # Creator has zero balance, so CREATE with value=1 will abort
    creator_address = pre.deploy_contract(
        creator_code, balance=0, storage={0: 1}
    )

    # Pre-compute the address that would have been created
    contract_address = compute_create_address(
        address=creator_address,
        nonce=1,
        salt=0,
        initcode=initcode,
        opcode=create_opcode,
    )

    # Measure gas cost of BALANCE on the would-be contract address;
    # cold access proves the address was not warmed by the failed create
    cold_balance = Op.BALANCE(contract_address, address_warm=False)
    checker_address = pre.deploy_contract(
        CodeGasMeasure(
            code=cold_balance,
            extra_stack_items=1,
            sstore_key=1,
        )
    )

    entry_address = pre.deploy_contract(
        Op.CALL(gas=Op.GAS, address=creator_address)
        + Op.CALL(gas=Op.GAS, address=checker_address)
        + Op.STOP
    )

    tx = Transaction(
        to=entry_address,
        gas_limit=1_000_000,
        sender=pre.fund_eoa(),
    )

    post = {
        # CREATE returned 0 (failed)
        creator_address: Account(storage={0: 0}),
        # BALANCE gas cost matches cold access
        checker_address: Account(storage={1: cold_balance.gas_cost(fork)}),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "create_opcode",
    [
        pytest.param(Op.CREATE, id="CREATE"),
        pytest.param(Op.CREATE2, id="CREATE2"),
    ],
)
def test_create_nonce_overflow(
    state_test: StateTestFiller,
    pre: Alloc,
    env: Environment,
    fork: Fork,
    create_opcode: Op,
) -> None:
    """
    Test that a failed CREATE/CREATE2 due to sender nonce overflow does not
    warm the contract address.

    A creator contract with nonce 2^64-1 (max) attempts to create. The
    create aborts because the nonce cannot be incremented, and a subsequent
    BALANCE check verifies the would-be contract address remains cold.
    """
    initcode = Op.STOP

    creator_code = Op.MSTORE(
        0, Op.PUSH32(bytes(initcode).ljust(32, b"\0"))
    ) + Op.SSTORE(
        0,
        create_opcode(value=0, offset=0, size=len(initcode)),
    )

    # Nonce at max value (2^64-1) causes CREATE to abort
    creator_address = pre.deploy_contract(
        creator_code, nonce=2**64 - 1, storage={0: 1}
    )

    # Pre-compute the address that would have been created
    contract_address = compute_create_address(
        address=creator_address,
        nonce=2**64 - 1,
        salt=0,
        initcode=initcode,
        opcode=create_opcode,
    )

    # Measure gas cost of BALANCE on the would-be contract address;
    # cold access proves the address was not warmed by the failed create
    cold_balance = Op.BALANCE(contract_address, address_warm=False)
    checker_address = pre.deploy_contract(
        CodeGasMeasure(
            code=cold_balance,
            extra_stack_items=1,
            sstore_key=1,
        )
    )

    entry_address = pre.deploy_contract(
        Op.CALL(gas=Op.GAS, address=creator_address)
        + Op.CALL(gas=Op.GAS, address=checker_address)
        + Op.STOP
    )

    tx = Transaction(
        to=entry_address,
        gas_limit=1_000_000,
        sender=pre.fund_eoa(),
    )

    post = {
        # CREATE returned 0 (failed)
        creator_address: Account(storage={0: 0}),
        # BALANCE gas cost matches cold access
        checker_address: Account(storage={1: cold_balance.gas_cost(fork)}),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)
