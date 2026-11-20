"""
STATICCALL a 60 KB contract 50 times in a loop.

Ported from:
state_tests/stStaticCall/static_Call50000bytesContract50_1Filler.json
state_tests/stStaticCall/static_Call50000bytesContract50_2Filler.json
state_tests/stStaticCall/static_Call50000bytesContract50_3Filler.json

@manually-enhanced: Do not overwrite. Merged; oversized code generated.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Environment,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
)

from tests.ported_static.constants import HIGH_GAS_LIMIT

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CONTRACT_BALANCE = 0xFFFFFFFFFFFFF
LOOP_COUNT = 50
CALL_GAS = 88_250_000_000
TX_GAS = 882_500_000_000
OVERSIZED_ADDRESSES = {
    ("add_chain", True): Address(0x784C659B2B4D2B69AB5564D60F4E565C7A1CEB2B),
    ("add_chain", False): Address(0x80C3355386CD2326418157DBD8764B380B971F67),
    ("jumpdests", True): Address(0x1836FD8C1DB3E96AE2A516F50C27483CD48D2EF0),
    ("jumpdests", False): Address(0xEA3174AB39F002DEF28B14B425DC9E7E67FED805),
    ("jump_over_jumpdests", True): Address(
        0x653CF6168B15C28D212F20D652C34BBE734A8718
    ),
    ("jump_over_jumpdests", False): Address(
        0x0431FBE9C18DC43AF2C372A7554BB2826176BDFD
    ),
}


def oversized_code(body: str, stores: bool) -> bytes:
    """Return the oversized callee's code, ending in an SSTORE or not."""
    if body == "add_chain":
        code = Op.PUSH1[1] + (Op.PUSH1[1] + Op.ADD) * 20_000
        tail = Op.PUSH1[0] + Op.SSTORE if stores else Op.PUSH1[0]
        return bytes(code + tail)
    if body == "jumpdests":
        code = Op.PUSH1[1] + Op.JUMPDEST * 60_000
    elif body == "jump_over_jumpdests":
        code = Op.PUSH1[1] + Op.JUMP(55_950) + Op.JUMPDEST * 60_000
    else:
        raise ValueError(f"Unknown body: {body}")
    code += Op.PUSH1[1] + Op.ADD
    if stores:
        code += Op.PUSH1[0] + Op.SSTORE
    return bytes(code)


def loop_code(callee: Address, stores: bool) -> Bytecode:
    """Return a loop that STATICCALLs `callee` `LOOP_COUNT` times."""
    counter = Op.MLOAD(0x80)
    call = Op.STATICCALL(gas=CALL_GAS, address=callee)
    write = Op.SSTORE if stores else Op.MSTORE
    return (
        Op.JUMPDEST
        + Op.JUMPI(0x3E, Op.ISZERO(Op.LT(counter, LOOP_COUNT)))
        + write(0x0, call)
        + Op.MSTORE(0x80, Op.ADD(counter, 1))
        + Op.JUMP(0x0)
        + Op.JUMPDEST
        + write(0x1 if stores else 0x20, counter)
        + Op.STOP
    )


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_Call50000bytesContract50_1Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_Call50000bytesContract50_2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_Call50000bytesContract50_3Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.slow
@pytest.mark.parametrize("stores", [True, False], ids=["sstore", "mstore"])
@pytest.mark.parametrize(
    "body",
    [
        pytest.param("add_chain", id="contract50_1"),
        pytest.param("jumpdests", id="contract50_2"),
        pytest.param("jump_over_jumpdests", id="contract50_3"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_call50000bytes_contract50(
    state_test: StateTestFiller,
    pre: Alloc,
    body: str,
    stores: bool,
) -> None:
    """
    Verify a loop of STATICCALLs into an oversized contract.

    The oversized code exceeds the deployable code size, so it is placed
    in the pre-state directly at a fixed address. Every case deploys all
    six callees, so the cases share one pre-state. With `stores`, the
    callee ends in an SSTORE, which fails in the static frame and burns
    the forwarded gas, so the loop runs out of gas.
    """
    env = Environment(gas_limit=HIGH_GAS_LIMIT)

    for (each_body, each_stores), address in OVERSIZED_ADDRESSES.items():
        pre[address] = Account(
            code=oversized_code(each_body, each_stores),
            balance=CONTRACT_BALANCE,
        )
    oversized = OVERSIZED_ADDRESSES[(body, stores)]
    loop = pre.deploy_contract(
        code=loop_code(oversized, stores), balance=CONTRACT_BALANCE
    )
    target = pre.deploy_contract(
        code=Op.SSTORE(
            0, Op.CALL(address=Op.CALLDATALOAD(0), value=Op.CALLVALUE)
        )
        + Op.SSTORE(1, 1)
        + Op.STOP
    )

    tx = Transaction(
        sender=pre.fund_eoa(amount=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF),
        to=target,
        data=Hash(loop, left_padding=True),
        gas_limit=TX_GAS,
        value=10,
    )

    post = {
        target: Account(storage={0: 0 if stores else 1, 1: 1}),
        loop: Account(storage={}),
        oversized: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
