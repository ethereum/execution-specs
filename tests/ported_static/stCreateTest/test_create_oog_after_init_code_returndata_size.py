"""
Verify that a CREATE whose child runs its init code to completion but cannot
afford the code deposit leaves no return data behind: the creation fails, no
account is deployed, and RETURNDATASIZE in the parent frame reads zero.

Ported from:
state_tests/stCreateTest/CreateOOGafterInitCodeReturndataSizeFiller.json

@manually-enhanced: Do not overwrite. The filler probed RETURNDATASIZE
indirectly, through the extra gas an `EXP` with a non-zero exponent costs;
the parent now reports the value to a calling frame that stores it, so the
observation is asserted directly. The budget is derived from the fork,
working backwards from the report the parent must afford out of its 1/64.
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

RETURN_DATA_SIZE_SLOT = 0x1
CALL_STATUS_SLOT = 0x2


@pytest.mark.ported_from(
    [
        "state_tests/stCreateTest/CreateOOGafterInitCodeReturndataSizeFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
def test_create_oog_after_init_code_returndata_size(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """CREATE fails at the code deposit; no return data is produced."""
    # The child returns this many zero bytes out of memory it never wrote to.
    # Only the size matters: depositing them is what it cannot afford, and
    # `code_deposit_size` folds that charge into RETURN's own gas cost, so the
    # boundary below comes from the fork's model with no EIP branch.
    deployed_code_size = 10
    child_initcode = Op.RETURN(
        offset=0x0,
        size=deployed_code_size,
        new_memory_size=deployed_code_size,
        code_deposit_size=deployed_code_size,
    )
    initcode_bytes = bytes(child_initcode)

    # Parent: stage the init code in memory, CREATE from it, then report
    # RETURNDATASIZE to its caller.
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
    # Returning the observation rather than storing it is what makes this
    # test possible at all: the parent runs this on the 1/64 CREATE leaves
    # it, and no SSTORE fits there -- EIP-2200 halts any SSTORE outright
    # below 2300 gas, which would force a budget far past the deposit
    # boundary the test exists to probe.
    report_code = (
        Op.POP
        + Op.MSTORE(
            offset=0x0,
            value=Op.RETURNDATASIZE,
            new_memory_size=0x20,
            old_memory_size=0x20,
        )
        + Op.RETURN(
            offset=0x0,
            size=0x20,
            new_memory_size=0x20,
            old_memory_size=0x20,
        )
    )
    parent = pre.deploy_contract(code=stage_code + create_code + report_code)

    # Work backwards from the report, which the parent pays for out of the
    # 1/64 it retains: that fixes the gas CREATE is reached with, and the
    # 63/64 the child is granted follows.
    retained = report_code.gas_cost(fork)
    available = retained * 64
    granted = available - available // 64
    assert available // 64 >= retained, (
        "retention must cover the parent's report"
    )
    # The grant has to run the init code to completion, then fall short of the
    # deposit that its RETURN triggers. A bare RETURN carrying only the deposit
    # metadata prices that charge on its own.
    child_cost = child_initcode.gas_cost(fork)
    deposit_cost = Op.RETURN(code_deposit_size=deployed_code_size).gas_cost(
        fork
    )
    assert child_cost - deposit_cost <= granted < child_cost, (
        "grant must cover the child's init execution but not the deposit"
    )

    parent_budget = (
        stage_code.gas_cost(fork) + create_code.gas_cost(fork) + available
    )

    # The caller has gas to spare, so it can afford to store what the parent
    # reports. Offsetting by one keeps a zero reading distinguishable from a
    # parent that never returned anything.
    entry = pre.deploy_contract(
        code=Op.SSTORE(
            CALL_STATUS_SLOT,
            Op.CALL(
                gas=parent_budget,
                address=parent,
                ret_offset=0x0,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(RETURN_DATA_SIZE_SLOT, Op.ADD(Op.MLOAD(0x0), 1))
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=entry,
        # Load-bearing under EIP-8037: with a reservoir the deposit's state
        # gas is paid out of it rather than out of the child's grant, the
        # deposit succeeds, and the contract deploys after all.
        state_gas_reservoir=0,
    )

    post = {
        entry: Account(
            storage={
                # The parent frame ran to completion on its retention.
                CALL_STATUS_SLOT: 1,
                # A failed code deposit produces no return data.
                RETURN_DATA_SIZE_SLOT: 1,
            }
        ),
        compute_create_address(address=parent, nonce=1): Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
