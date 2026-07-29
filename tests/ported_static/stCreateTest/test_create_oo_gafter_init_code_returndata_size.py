"""
Verify a CREATE whose child completes its init code but cannot afford the
code deposit: the creation fails (no account is deployed), yet the parent
frame survives on its 63/64 retention and the transaction succeeds.

Ported from:
state_tests/stCreateTest/CreateOOGafterInitCodeReturndataSizeFiller.json

@manually-enhanced: Do not overwrite. The gas limit is derived from the
fork so the child's 63/64 grant covers init execution but not the code
deposit (including EIP-8037 deposit state gas), and the budget carries
the CREATE's peak new-account state charge, refunded when the child
fails.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_VALUE = 1


@pytest.mark.ported_from(
    [
        "state_tests/stCreateTest/CreateOOGafterInitCodeReturndataSizeFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
def test_create_oo_gafter_init_code_returndata_size(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """CREATE fails at the code deposit; the parent frame completes."""
    # The child would deploy two stores; it never runs, only its deposit
    # price matters.
    child_runtime = Op.SSTORE(key=0x1, value=0x1) + Op.SSTORE(
        key=0x2, value=0x1
    )
    runtime_size = len(bytes(child_runtime))

    # Child init code: return the runtime code from memory.
    child_initcode = Op.MSTORE(
        offset=0x0,
        value=int.from_bytes(bytes(child_runtime), "big"),
        new_memory_size=0x20,
    ) + Op.RETURN(
        offset=32 - runtime_size,
        size=runtime_size,
    )
    initcode_bytes = bytes(child_initcode)

    # Parent: stage the init code in memory, CREATE from it, then read
    # RETURNDATASIZE (zero after the deposit failure) before stopping.
    stage_code = Op.MSTORE(
        offset=0x0,
        value=int.from_bytes(initcode_bytes, "big"),
        new_memory_size=0x20,
    )
    create_code = Op.CREATE(
        value=0x0,
        offset=32 - len(initcode_bytes),
        size=len(initcode_bytes),
        new_memory_size=0x20,
        old_memory_size=0x20,
        init_code_size=len(initcode_bytes),
    )
    tail_code = Op.POP + Op.EXP(0x2, Op.RETURNDATASIZE) + Op.STOP
    contract = pre.deploy_contract(code=stage_code + create_code + tail_code)

    # Grant the child enough for its init execution but one gas short of
    # the code deposit, so the deposit is what fails. Under EIP-8037 the
    # regular deposit cost is only the keccak word cost (the per-byte
    # price moved into deposit state gas); before it, 200 per byte.
    child_exec = child_initcode.gas_cost(fork)
    if fork.is_eip_enabled(8037):
        deposit_regular = fork.gas_costs().OPCODE_KECCAK256_PER_WORD * (
            (runtime_size + 31) // 32
        )
    else:
        deposit_regular = runtime_size * fork.gas_costs().CODE_DEPOSIT_PER_BYTE
    deposit = deposit_regular + fork.code_deposit_state_gas(
        code_size=runtime_size
    )
    available = (child_exec + deposit - 1) * 64 // 63
    forwarded = available - available // 64
    assert child_exec <= forwarded < child_exec + deposit, (
        "63/64 grant must cover init execution but not the deposit"
    )
    # The parent's 1/64 retention must still afford the tail.
    assert available // 64 > tail_code.gas_cost(fork), (
        "retention must cover the post-CREATE tail"
    )

    gas_limit = (
        fork.transaction_intrinsic_cost_calculator()(sends_value=True)
        + stage_code.gas_cost(fork)
        + create_code.gas_cost(fork)
        + available
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        gas_limit=gas_limit,
        value=TX_VALUE,
    )

    post = {
        # The transferred value proves the parent frame completed.
        contract: Account(balance=TX_VALUE, storage={}),
        compute_create_address(address=contract, nonce=1): Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
