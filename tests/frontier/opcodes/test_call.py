"""Test `CALL` opcode."""

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
)


# TODO: There's an issue with gas definitions on forks previous to Berlin,
# remove this when fixed. https://github.com/ethereum/execution-spec-
# tests/pull/1952#discussion_r2237634275
@pytest.mark.valid_from("Berlin")
def test_call_large_offset_mstore(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    CALL with ret_offset larger than memory size and ret_size zero Then do an
    MSTORE in that offset to see if memory was expanded in CALL.

    This is for bug in a faulty EVM implementation where memory is expanded
    when it shouldn't.
    """
    sender = pre.fund_eoa()

    mem_offset = 128  # arbitrary number

    # Cost of pushing args onto the stack (each PUSH costs G_VERY_LOW)
    call_push_cost = (Op.PUSH1(0) * len(Op.CALL.kwargs)).gas_cost(fork)
    mstore_push_cost = (Op.PUSH1(0) * len(Op.MSTORE.kwargs)).gas_cost(fork)

    call_measure = CodeGasMeasure(
        code=Op.CALL(gas=0, ret_offset=mem_offset, ret_size=0),
        overhead_cost=call_push_cost,
        extra_stack_items=1,  # Because CALL pushes 1 item to the stack
        sstore_key=0,
        stop=False,  # Because it's the first CodeGasMeasure
    )
    mstore_measure = CodeGasMeasure(
        code=Op.MSTORE(offset=mem_offset, value=1),
        overhead_cost=mstore_push_cost,
        extra_stack_items=0,
        sstore_key=1,
    )

    contract = pre.deploy_contract(call_measure + mstore_measure)

    tx = Transaction(
        gas_limit=500_000,
        to=contract,
        value=0,
        sender=sender,
    )

    # this call cost is just the address_access_cost
    call_cost = Op.CALL(address_warm=False).gas_cost(fork)

    # mstore cost: base cost + expansion cost
    mstore_cost = Op.MSTORE(new_memory_size=mem_offset + 32).gas_cost(fork)
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            contract: Account(
                storage={
                    0: call_cost,
                    1: mstore_cost,
                },
            )
        },
    )


# TODO: There's an issue with gas definitions on forks previous to Berlin,
# remove this when fixed. https://github.com/ethereum/execution-spec-
# tests/pull/1952#discussion_r2237634275
@pytest.mark.valid_from("Berlin")
def test_call_memory_expands_on_early_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    When CALL reverts early (e.g. because of not enough balance by the sender),
    memory should be expanded anyway. We check this with an MSTORE.

    This is for a bug in an EVM implementation where memory is expanded after
    executing a CALL, but not when an early revert happens.
    """
    sender = pre.fund_eoa()

    # arbitrary number, greater than memory size to trigger an expansion
    ret_size = 128

    # Cost of pushing args onto the stack (each PUSH costs G_VERY_LOW)
    call_push_cost = (Op.PUSH1(0) * len(Op.CALL.kwargs)).gas_cost(fork)
    mstore_push_cost = (Op.PUSH1(0) * len(Op.MSTORE.kwargs)).gas_cost(fork)

    call_measure = CodeGasMeasure(
        # CALL with value
        code=Op.CALL(gas=0, value=100, ret_size=ret_size),
        overhead_cost=call_push_cost,
        # Because CALL pushes 1 item to the stack
        extra_stack_items=1,
        sstore_key=0,
        # Because it's the first CodeGasMeasure
        stop=False,
    )
    mstore_measure = CodeGasMeasure(
        # Low offset for not expanding memory
        code=Op.MSTORE(offset=ret_size // 2, value=1),
        overhead_cost=mstore_push_cost,
        extra_stack_items=0,
        sstore_key=1,
    )

    # Contract without enough balance to send value transfer
    contract = pre.deploy_contract(
        code=call_measure + mstore_measure, balance=0
    )

    tx = Transaction(
        gas_limit=500_000,
        to=contract,
        value=0,
        sender=sender,
    )

    # call cost:
    #   address_access_cost+new_acc_cost+memory_expansion_cost+value-stipend
    # G_CALL_STIPEND is a threshold check, not a gas cost — keep from gas_costs
    gsc = fork.gas_costs()
    call_cost = (
        Op.CALL(
            address_warm=False,
            value_transfer=True,
            account_new=True,
            new_memory_size=ret_size,
        ).gas_cost(fork)
        - gsc.GAS_CALL_STIPEND
    )

    # mstore cost: base cost. No memory expansion cost needed, it was expanded
    # on CALL.
    mstore_cost = Op.MSTORE(new_memory_size=0).gas_cost(fork)
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            contract: Account(
                storage={
                    0: call_cost,
                    1: mstore_cost,
                },
            )
        },
    )


# TODO: There's an issue with gas definitions on forks previous to Berlin,
# remove this when fixed. https://github.com/ethereum/execution-spec-
# tests/pull/1952#discussion_r2237634275
@pytest.mark.with_all_call_opcodes
@pytest.mark.valid_from("Berlin")
def test_call_large_args_offset_size_zero(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
) -> None:
    """
    Test xCALL with an extremely large args_offset and args_size set to zero.
    Since the size is zero, the large offset should not cause a revert.
    """
    sender = pre.fund_eoa()

    very_large_offset = 2**100

    # Cost of pushing args onto the stack (each PUSH costs G_VERY_LOW)
    push_cost = (Op.PUSH1(0) * len(call_opcode.kwargs)).gas_cost(fork)

    call_measure = CodeGasMeasure(
        code=call_opcode(gas=0, args_offset=very_large_offset, args_size=0),
        overhead_cost=push_cost,
        extra_stack_items=1,  # Because xCALL pushes 1 item to the stack
        sstore_key=0,
    )

    contract = pre.deploy_contract(call_measure)

    tx = Transaction(
        gas_limit=500_000,
        to=contract,
        value=0,
        sender=sender,
    )

    # this call cost is just the address_access_cost
    call_cost = call_opcode(address_warm=False).gas_cost(fork)

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            contract: Account(
                storage={
                    0: call_cost,
                },
            )
        },
    )
