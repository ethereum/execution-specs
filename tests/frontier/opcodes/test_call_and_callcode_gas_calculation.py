"""
Tests nested CALL/CALLCODE/DELEGATECALL/STATICCALL gas usage with positive
value transfer (where applicable).

This test investigates an issue identified in EthereumJS, as reported in:
https://github.com/ethereumjs/ethereumjs-monorepo/issues/3194.

The issue pertains to the incorrect gas calculation for
CALL/CALLCODE/DELEGATECALL/STATICCALL operations with a positive value
transfer, due to the pre-addition of the gas stipend (2300) to the currently
available gas instead of adding it to the new call frame. This bug was specific
to the case where insufficient gas was provided for the CALL/CALLCODE
operation. Due to the pre-addition of the stipend to the currently available
gas, the case for insufficient gas was not properly failing with an out-of-gas
error.

Test setup:

Given two smart contract accounts, 0x0A (caller) and 0x0B (callee):
1. An arbitrary transaction calls into the contract 0x0A.
2. Contract 0x0A executes a CALL to contract 0x0B with a specific gas limit
(X).
3. Contract 0x0B then attempts a CALL/CALLCODE to a non-existent contract
0x0C, with a positive value transfer (activating the gas stipend).
4. If the gas X provided by contract 0x0A to 0x0B is sufficient, contract
0x0B will push 0x01 onto the stack after returning to the call frame in
0x0A. Otherwise, it should push 0x00, indicating the insufficiency of
gas X (for the bug in EthereumJS, the CALL/CALLCODE operation would
return 0x01 due to the pre-addition of the gas stipend).
5. The resulting stack value is saved into contract 0x0A's storage,
allowing us to verify whether the provided gas was sufficient or
insufficient.
"""

from typing import Dict

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytecode,
    Environment,
    Op,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks.forks.forks import Berlin, Byzantium, Homestead
from execution_testing.forks.helpers import Fork


@pytest.fixture
def callee_init_stack_gas(callee_opcode: Op, fork: Fork) -> int:
    """
    Calculate the initial stack gas for the callee opcode.
    """
    if fork < Byzantium:
        # all *CALL arguments handled with PUSHes
        return len(callee_opcode.kwargs) * 3
    else:
        # gas argument handled with GAS which is cheaper
        return (len(callee_opcode.kwargs) - 1) * 3 + 2


@pytest.fixture
def sufficient_gas(
    callee_opcode: Op, callee_init_stack_gas: int, fork: Fork
) -> int:
    """
    Calculate the sufficient gas for the nested call opcode with positive
    value transfer.
    """
    # memory_exp_cost is zero for our case.
    cost = 0

    if fork >= Berlin:
        cost += 2600  # call and address_access_cost
    elif Byzantium <= fork < Berlin:
        cost += 700  # call
    elif fork == Homestead:
        cost += 40  # call
        cost += 1  # mandatory callee gas allowance
    else:
        raise Exception("Only forks Homestead and >=Byzantium supported")

    is_value_call = callee_opcode in [Op.CALL, Op.CALLCODE]
    if is_value_call:
        cost += 9000  # positive_value_cost

    if callee_opcode == Op.CALL:
        cost += 25000  # empty_account_cost

    cost += callee_init_stack_gas

    return cost


@pytest.fixture
def callee_code(pre: Alloc, callee_opcode: Op, fork: Fork) -> Bytecode:
    """
    Code called by the caller contract:
      PUSH1 0x00 * 4
      PUSH1 0x01 <- for positive value transfer, if applies
      PUSH2 Contract.nonexistent
      PUSH1 0x00 or GAS <- value doesn't matter:
        - PUSH1 0x01: pre Byzantium tests, as they require `gas_left` to be at
          least `gas`. In these cases we want non-zero `gas`, so that that
          condition check can also be triggered - see `gas_shortage` parameter
          values.
        - GAS: other forks, to not alter previous test behavior
      CALL/CALLCODE/DELEGATECALL/STATICCALL.
    """
    # The address needs to be empty and different for each execution of the
    # fixture, otherwise the calculations (empty_account_cost) are incorrect.
    is_value_call = callee_opcode in [Op.CALL, Op.CALLCODE]
    extra_args = {"value": 1} if is_value_call else {}

    return callee_opcode(
        unchecked=False,
        gas=1 if fork < Byzantium else Op.GAS,
        address=pre.empty_account(),
        args_offset=0,
        args_size=0,
        ret_offset=0,
        ret_size=0,
        **extra_args,
    )


@pytest.fixture
def sender(pre: Alloc) -> EOA:
    """Sender for all transactions."""
    return pre.fund_eoa()


@pytest.fixture
def callee_address(pre: Alloc, callee_code: Bytecode) -> Address:
    """Address of the callee."""
    return pre.deploy_contract(callee_code, balance=0x03)


@pytest.fixture
def caller_code(
    sufficient_gas: int, gas_shortage: int, callee_address: Address
) -> Bytecode:
    """
    Code to CALL the callee contract:
      PUSH1 0x00 * 5
      PUSH2 Contract.callee
      PUSH2 caller_gas <- gas limit set for CALL to callee contract
      CALL
      PUSH1 0x00
      SSTORE.
    """
    caller_gas_limit = sufficient_gas - gas_shortage

    return Op.SSTORE(
        0, Op.CALL(caller_gas_limit, callee_address, 0, 0, 0, 0, 0)
    )


@pytest.fixture
def caller_address(pre: Alloc, caller_code: Bytecode) -> Address:
    """
    Code to CALL the callee contract:
      PUSH1 0x00 * 5
      PUSH2 Contract.callee
      PUSH2 caller_gas <- gas limit set for CALL to callee contract
      CALL
      PUSH1 0x00
      SSTORE.
    """
    return pre.deploy_contract(caller_code, balance=0x03)


@pytest.fixture
def caller_tx(sender: EOA, caller_address: Address, fork: Fork) -> Transaction:
    """Transaction that performs the call to the caller contract."""
    return Transaction(
        to=caller_address,
        value=1,
        gas_limit=500_000,
        sender=sender,
        protected=fork >= Byzantium,
    )


@pytest.fixture
def post(  # noqa: D103
    caller_address: Address, gas_shortage: int
) -> Dict[Address, Account]:
    return {
        caller_address: Account(
            storage={0x00: 0x01 if gas_shortage == 0 else 0x00}
        ),
    }


@pytest.mark.parametrize(
    "callee_opcode", [Op.CALL, Op.CALLCODE, Op.DELEGATECALL, Op.STATICCALL]
)
@pytest.mark.parametrize("gas_shortage", [0, 1])
@pytest.mark.valid_from("London")
def test_value_transfer_gas_calculation(
    state_test: StateTestFiller,
    pre: Alloc,
    caller_tx: Transaction,
    post: Dict[str, Account],
) -> None:
    """
    Tests the nested CALL/CALLCODE/DELEGATECALL/STATICCALL opcode gas
    consumption with a positive value transfer.
    """
    state_test(env=Environment(), pre=pre, post=post, tx=caller_tx)


@pytest.mark.parametrize(
    "callee_opcode", [Op.CALL, Op.CALLCODE, Op.DELEGATECALL, Op.STATICCALL]
)
@pytest.mark.parametrize("gas_shortage", [0, 1])
@pytest.mark.valid_from("Byzantium")
@pytest.mark.valid_until("Berlin")
def test_value_transfer_gas_calculation_byzantium(
    state_test: StateTestFiller,
    pre: Alloc,
    caller_tx: Transaction,
    post: Dict[str, Account],
) -> None:
    """
    Tests the nested CALL/CALLCODE/DELEGATECALL/STATICCALL opcode gas
    consumption with a positive value transfer.
    """
    state_test(env=Environment(), pre=pre, post=post, tx=caller_tx)


@pytest.mark.parametrize(
    "callee_opcode", [Op.CALL, Op.CALLCODE, Op.DELEGATECALL]
)
# pre-Byzantium rules have one more condition to fail on:
# the check for `gas_left` to be at least `gas` allowance specified
# in the CALL. We will be setting that allowance to `1` and either
# making the call miss that amount or fail on the earlier gas check.
@pytest.mark.parametrize("gas_shortage", [0, 1, 2])
@pytest.mark.valid_at("Homestead")
def test_value_transfer_gas_calculation_homestead(
    state_test: StateTestFiller,
    pre: Alloc,
    caller_tx: Transaction,
    post: Dict[str, Account],
) -> None:
    """
    Tests the nested CALL/CALLCODE/DELEGATECALL opcode gas
    consumption with a positive value transfer.
    """
    state_test(env=Environment(), pre=pre, post=post, tx=caller_tx)
