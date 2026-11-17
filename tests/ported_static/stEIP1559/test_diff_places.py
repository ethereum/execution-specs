"""
Read BASEFEE and GASPRICE from different execution contexts.

Ported from:
state_tests/stEIP1559/baseFeeDiffPlacesFiller.yml
state_tests/stEIP1559/baseFeeDiffPlacesOsakaFiller.yml
state_tests/stEIP1559/gasPriceDiffPlacesFiller.yml
state_tests/stEIP1559/gasPriceDiffPlacesOsakaFiller.yml

@manually-enhanced: Do not overwrite. Merged into one parametrized test.
"""

from typing import Dict

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Conditional,
    Environment,
    Initcode,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

from tests.ported_static.constants import HIGH_GAS_LIMIT

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

PORTED_FROM = [
    "state_tests/stEIP1559/baseFeeDiffPlacesFiller.yml",
    "state_tests/stEIP1559/baseFeeDiffPlacesOsakaFiller.yml",
    "state_tests/stEIP1559/gasPriceDiffPlacesFiller.yml",
    "state_tests/stEIP1559/gasPriceDiffPlacesOsakaFiller.yml",
]

GAS_PRICE = 2000
GOAT = 0x60A7
RECURSION_DEPTH = 1023
RECURSION_GAS_LIMIT = 0x10000000000000
CREATE2_SALT = 0x5A17
FAILING_CALL_GAS = 25_000

CALL_OPS = {
    "call": Op.CALL,
    "callcode": Op.CALLCODE,
    "delegatecall": Op.DELEGATECALL,
    "staticcall": Op.STATICCALL,
}
CREATE_OPS = {"create": Op.CREATE, "create2": Op.CREATE2}

ACTIONS = (
    ["direct"]
    + list(CALL_OPS)
    + [f"{outer}_{inner}" for inner in CALL_OPS for outer in CALL_OPS]
    + ["after_revert", "after_oog", "after_selfdestruct"]
    + list(CREATE_OPS)
    + [f"{create}_{call}" for create in CREATE_OPS for call in CALL_OPS]
)

OPCODES = pytest.mark.parametrize(
    "opcode", [Op.BASEFEE, Op.GASPRICE], ids=["base_fee", "gas_price"]
)


def expected_value(opcode: Op, fork: Fork) -> int:
    """Return the value the opcode is expected to push."""
    if opcode == Op.BASEFEE:
        base_fee = Environment().set_fork_requirements(fork).base_fee_per_gas
        assert base_fee is not None
        return int(base_fee)
    return GAS_PRICE


def call_into(op: Op, address: Address | Bytecode) -> Bytecode:
    """Call `address` with `op`, copying 32 bytes of output to memory 0."""
    return op(address=address, ret_offset=0, ret_size=0x20)


def run_and_create(
    create: str, initcode_holder: Address, create_value: int = 0
) -> Bytecode:
    """Create a contract with the initcode held by `initcode_holder`."""
    size = Op.EXTCODESIZE(initcode_holder)
    code = Op.EXTCODECOPY(
        address=initcode_holder, dest_offset=0x20, offset=0, size=size
    )
    if create == "create":
        return code + Op.CREATE(value=create_value, offset=0x20, size=size)
    return code + Op.CREATE2(
        value=create_value, offset=0x20, size=size, salt=CREATE2_SALT
    )


@pytest.mark.ported_from(PORTED_FROM)
@pytest.mark.valid_from("Cancun")
@pytest.mark.execute(
    pytest.mark.skip(reason="Expects the base fee of the test env")
)
@OPCODES
@pytest.mark.parametrize("action", ACTIONS)
def test_diff_places(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    action: str,
) -> None:
    """Read the opcode directly, through calls, and in created code."""
    template = Op.MSTORE(offset=0, value=opcode)
    expected = expected_value(opcode, fork)
    sender = pre.fund_eoa()
    post: Dict[Address, Account] = {}

    runner = pre.deploy_contract(code=template + Op.RETURN(0, 0x20))
    relays = {
        name: pre.deploy_contract(
            code=Op.POP(call_into(op, runner)) + Op.RETURN(0, 0x20)
        )
        for name, op in CALL_OPS.items()
    }
    reverter = pre.deploy_contract(
        code=template
        + Op.SSTORE(0, Op.MLOAD(0))
        + Op.REVERT(offset=0, size=0x20),
        storage={0: GOAT},
    )
    out_of_gas = pre.deploy_contract(
        code=template + Op.SSTORE(0, Op.MLOAD(0)) + Op.INVALID,
        storage={0: GOAT},
    )
    self_destructor = pre.deploy_contract(code=Op.SELFDESTRUCT(0))
    constructor_holder = pre.deploy_contract(
        code=template
        + Op.MSTORE(0x40, Op.MLOAD(0))
        + Op.RETURN(offset=0x3F, size=0x21),
    )
    runtime_holder = pre.deploy_contract(
        code=Initcode(deploy_code=template + Op.RETURN(0, 0x20)),
    )

    body: Bytecode
    if action == "direct":
        body = template
    elif action in CALL_OPS:
        body = Op.POP(call_into(CALL_OPS[action], runner))
    elif action in ("after_revert", "after_oog", "after_selfdestruct"):
        failing = {
            "after_revert": reverter,
            "after_oog": out_of_gas,
            "after_selfdestruct": self_destructor,
        }[action]
        body = (
            template
            + Op.SSTORE(1, Op.MLOAD(0))
            + Op.MSTORE(0, GOAT)
            + Op.POP(Op.CALL(gas=FAILING_CALL_GAS, address=failing))
            + template
        )
        post[reverter] = Account(storage={0: GOAT})
        post[out_of_gas] = Account(storage={0: GOAT})
    elif action in CREATE_OPS:
        body = Op.EXTCODECOPY(
            address=run_and_create(action, constructor_holder),
            dest_offset=0,
            offset=1,
            size=0x20,
        )
    else:
        first, second = action.split("_")
        if first in CREATE_OPS:
            body = Op.POP(
                call_into(
                    CALL_OPS[second], run_and_create(first, runtime_holder)
                )
            )
        else:
            body = Op.POP(call_into(CALL_OPS[first], relays[second]))

    checker = pre.deploy_contract(
        code=Op.MSTORE(0, GOAT) + body + Op.SSTORE(0, Op.MLOAD(0)),
    )
    storage = {0: expected}
    if action.startswith("after_"):
        storage[1] = expected
    post[checker] = Account(storage=storage)

    tx = Transaction(sender=sender, to=checker, gas_price=GAS_PRICE)
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(PORTED_FROM)
@pytest.mark.valid_from("Cancun")
@pytest.mark.execute(
    pytest.mark.skip(reason="Expects the base fee of the test env")
)
@pytest.mark.valid_until("Prague")
@OPCODES
def test_diff_places_deep_recursion(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
) -> None:
    """Read the opcode at the bottom of a deep recursion."""
    template = Op.MSTORE(offset=0, value=opcode)
    sender = pre.fund_eoa(amount=RECURSION_GAS_LIMIT * GAS_PRICE)
    recursor = pre.deploy_contract(
        code=Conditional(
            condition=Op.ISZERO(Op.CALLDATALOAD(0)),
            if_true=template,
            if_false=Op.MSTORE(0, Op.SUB(Op.CALLDATALOAD(0), 1))
            + Op.POP(
                Op.CALL(
                    address=Op.ADDRESS,
                    args_offset=0,
                    args_size=0x20,
                    ret_offset=0,
                    ret_size=0x20,
                )
            ),
        )
        + Op.RETURN(0, 0x20),
    )
    checker = pre.deploy_contract(
        code=Op.MSTORE(0, RECURSION_DEPTH)
        + Op.POP(
            Op.CALL(
                address=recursor,
                args_offset=0,
                args_size=0x20,
                ret_offset=0,
                ret_size=0x20,
            )
        )
        + Op.SSTORE(0, Op.MLOAD(0)),
    )

    tx = Transaction(
        sender=sender,
        to=checker,
        gas_limit=RECURSION_GAS_LIMIT,
        gas_price=GAS_PRICE,
    )
    post = {checker: Account(storage={0: expected_value(opcode, fork)})}
    state_test(
        env=Environment(gas_limit=HIGH_GAS_LIMIT), pre=pre, post=post, tx=tx
    )
