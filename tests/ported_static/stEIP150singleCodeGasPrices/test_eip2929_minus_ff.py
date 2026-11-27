"""
Test the gas of SELFDESTRUCT to a cold or pre-warmed beneficiary.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/stEIP150singleCodeGasPrices/eip2929-ffFiller.yml

@manually-enhanced: Do not overwrite. `gas_meter` optionally warms the
`beneficiary` with one access opcode, then measures a `CALL` into
`self_destructor`, which `SELFDESTRUCT`s to the `beneficiary`, and
finally a `BALANCE` of the (by then always warm) `beneficiary`. The
expected values come from the framework gas calculation, with the
`SELFDESTRUCT` beneficiary marked warm only when a warm-up ran.
"""

from typing import Generator

import pytest
from _pytest.mark.structures import ParameterSet
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op, Opcode

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

WARM_UP_OPCODES: list[Opcode] = [
    Op.BALANCE,
    Op.EXTCODESIZE,
    Op.EXTCODECOPY,
    Op.EXTCODEHASH,
    Op.CALL,
    Op.CALLCODE,
    Op.DELEGATECALL,
    Op.STATICCALL,
]
WARM_UP_CALL_GAS = 0x10000
SELF_DESTRUCTOR_CALL_GAS = 0x1000000


def warm_up_opcodes_by_fork(
    fork: Fork,
) -> Generator[ParameterSet, None, None]:
    """Yield no warm-up, then every warm-up opcode that exists on `fork`."""
    yield pytest.param(None, id="cold")
    valid_opcodes = set(fork.valid_opcodes())
    for opcode in WARM_UP_OPCODES:
        if opcode in valid_opcodes:
            yield pytest.param(opcode, id=opcode._name_.lower())


@pytest.mark.ported_from(
    ["state_tests/stEIP150singleCodeGasPrices/eip2929-ffFiller.yml"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize_by_fork("warm_up_opcode", warm_up_opcodes_by_fork)
def test_eip2929_minus_ff(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    warm_up_opcode: Opcode | None,
) -> None:
    """Store the gas of a CALL into a SELFDESTRUCT after a warm-up."""
    sender = pre.fund_eoa()

    beneficiary = pre.deploy_contract(code=Op.STOP)

    def self_destructor_code(beneficiary_warm: bool) -> Bytecode:
        return (
            Op.SELFDESTRUCT(address=beneficiary, address_warm=beneficiary_warm)
            + Op.STOP
        )

    self_destructor = pre.deploy_contract(
        code=self_destructor_code(beneficiary_warm=False),
        balance=10**18,
    )

    warm_up: Bytecode
    match warm_up_opcode:
        case None:
            warm_up = Bytecode()
        case Op.EXTCODECOPY:
            warm_up = Op.EXTCODECOPY(
                address=beneficiary, dest_offset=0, offset=0, size=1
            )
        case Op.CALL | Op.CALLCODE | Op.DELEGATECALL | Op.STATICCALL:
            warm_up = Op.POP(
                warm_up_opcode(gas=WARM_UP_CALL_GAS, address=beneficiary)
            )
        case _:
            warm_up = Op.POP(warm_up_opcode(address=beneficiary))
    beneficiary_warm = warm_up_opcode is not None

    call_self_destructor = Op.CALL(
        gas=SELF_DESTRUCTOR_CALL_GAS,
        address=self_destructor,
        address_warm=True,
        inner_call_cost=self_destructor_code(beneficiary_warm).gas_cost(fork),
    )
    read_beneficiary_balance = Op.BALANCE(
        address=beneficiary, address_warm=True
    )

    gas_meter = pre.deploy_contract(
        code=Op.POP(Op.BALANCE(address=self_destructor))
        + warm_up
        + CodeGasMeasure(
            code=call_self_destructor, extra_stack_items=1, sstore_key=0
        )
        + CodeGasMeasure(
            code=read_beneficiary_balance, extra_stack_items=1, sstore_key=1
        )
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=gas_meter,
        protected=fork.supports_protected_txs(),
    )

    post = {
        gas_meter: Account(
            storage={
                0: call_self_destructor.gas_cost(fork),
                1: read_beneficiary_balance.gas_cost(fork),
            }
        )
    }

    state_test(pre=pre, post=post, tx=tx)
