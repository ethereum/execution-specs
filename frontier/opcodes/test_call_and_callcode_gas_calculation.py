"""
abstract: Tests the nested CALL/CALLCODE opcode gas consumption with a positive value transfer.
    This test is designed to investigate an issue identified in EthereumJS, as reported in:
    https://github.com/ethereumjs/ethereumjs-monorepo/issues/3194.

    The issue pertains to the incorrect gas calculation for CALL/CALLCODE operations with a
    positive value transfer, due to the pre-addition of the gas stipend (2300) to the currently
    available gas instead of adding it to the new call frame. This bug was specific to the case
    where insufficient gas was provided for the CALL/CALLCODE operation. Due to the pre-addition
    of the stipend to the currently available gas, the case for insufficient gas was not properly
    failing with an out-of-gas error.

    Test setup: Given two smart contract accounts, 0x0A (caller) and 0x0B (callee):
    1) An arbitrary transaction calls into the contract 0x0A.
    2) Contract 0x0A executes a CALL to contract 0x0B with a specific gas limit (X).
    3) Contract 0x0B then attempts a CALL/CALLCODE to a non-existent contract 0x0C,
       with a positive value transfer (activating the gas stipend).
    4) If the gas X provided by contract 0x0A to 0x0B is sufficient, contract 0x0B
       will push 0x01 onto the stack after returning to the call frame in 0x0A. Otherwise, it
       should push 0x00, indicating the insufficiency of gas X (for the bug in EthereumJS, the
       CALL/CALLCODE operation would return 0x01 due to the pre-addition of the gas stipend).
    5) The resulting stack value is saved into contract 0x0A's storage, allowing us to
       verify whether the provided gas was sufficient or insufficient.
"""

from dataclasses import dataclass
from typing import Dict

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Environment,
    StateTestFiller,
    TestAddress,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

"""
PUSH opcode cost is 3, GAS opcode cost is 2.
We need 6 PUSH's and one GAS to fill the stack for both CALL & CALLCODE, in the callee contract.
"""
CALLEE_INIT_STACK_GAS = 6 * 3 + 2

"""
CALL gas breakdowns: (https://www.evm.codes/#f1)
memory_exp_cost + code_exec_cost + address_access_cost + positive_value_cost + empty_account_cost
= 0 + 0 + 2600 + 9000 + 25000 = 36600
"""
CALL_GAS = 36600
CALL_SUFFICIENT_GAS = CALL_GAS + CALLEE_INIT_STACK_GAS

"""
CALLCODE gas breakdowns: (https://www.evm.codes/#f2)
memory_exp_cost + code_exec_cost + address_access_cost + positive_value_cost
= 0 + 0 + 2600 + 9000 = 11600
"""
CALLCODE_GAS = 11600
CALLCODE_SUFFICIENT_GAS = CALLCODE_GAS + CALLEE_INIT_STACK_GAS


@dataclass(frozen=True)
class Contract:
    """Contract accounts used in the test."""

    caller: int = 0x0A
    callee: int = 0x0B
    nonexistent: int = 0x0C


@pytest.fixture
def caller_code(caller_gas_limit: int) -> bytes:
    """
    Code to CALL the callee contract:
        PUSH1 0x00 * 5
        PUSH2 Contract.callee
        PUSH2 caller_gas <- gas limit set for CALL to callee contract
        CALL
        PUSH1 0x00
        SSTORE
    """
    return Op.SSTORE(0, Op.CALL(caller_gas_limit, Contract.callee, 0, 0, 0, 0, 0))


@pytest.fixture
def callee_code(callee_opcode: Op) -> bytes:
    """
    Code called by the caller contract:
        PUSH1 0x00 * 4
        PUSH1 0x01 <- for positive value transfer
        PUSH2 Contract.nonexistent
        GAS <- value doesn't matter
        CALL/CALLCODE
    """
    return callee_opcode(Op.GAS(), Contract.nonexistent, 1, 0, 0, 0, 0)


@pytest.fixture
def caller_tx() -> Transaction:
    """Transaction that performs the call to the caller contract."""
    return Transaction(
        chain_id=0x01,
        nonce=0,
        to=Address(Contract.caller),
        value=1,
        gas_limit=500000,
        gas_price=7,
    )


@pytest.fixture
def pre(caller_code: bytes, callee_code: bytes) -> Dict[Address, Account]:  # noqa: D103
    return {
        Address(Contract.caller): Account(
            balance=0x03,
            code=caller_code,
            nonce=1,
        ),
        Address(Contract.callee): Account(
            balance=0x03,
            code=callee_code,
            nonce=1,
        ),
        TestAddress: Account(
            balance=0x0BA1A9CE,
        ),
    }


@pytest.fixture
def post(is_sufficient_gas: bool) -> Dict[Address, Account]:  # noqa: D103
    return {
        Address(Contract.caller): Account(storage={0x00: 0x01 if is_sufficient_gas else 0x00}),
    }


@pytest.mark.parametrize(
    "callee_opcode, caller_gas_limit, is_sufficient_gas",
    [
        (Op.CALL, CALL_SUFFICIENT_GAS, True),
        (Op.CALL, CALL_SUFFICIENT_GAS - 1, False),
        (Op.CALLCODE, CALLCODE_SUFFICIENT_GAS, True),
        (Op.CALLCODE, CALLCODE_SUFFICIENT_GAS - 1, False),
    ],
)
@pytest.mark.valid_from("London")
@pytest.mark.valid_until("Shanghai")
def test_value_transfer_gas_calculation(
    state_test: StateTestFiller,
    pre: Dict[str, Account],
    caller_tx: Transaction,
    post: Dict[str, Account],
):
    """
    Tests the nested CALL/CALLCODE opcode gas consumption with a positive value transfer.
    """
    state_test(env=Environment(), pre=pre, post=post, tx=caller_tx)
