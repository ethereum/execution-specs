"""
CREATE2 at call depth 1022 whose init code runs CREATE2 at the depth limit.

Ported from:
state_tests/stCreate2/Create2OnDepth1023Filler.json
state_tests/stCreate2/Create2OnDepth1024Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Conditional,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

INNER_CREATE2_INITCODE = bytes.fromhex("6000600060006000f5600155")
NESTED_CREATE2_INITCODE = bytes.fromhex(
    "686000600060006000f56000526000600960176000f5600155"
)


@pytest.mark.ported_from(
    [
        "state_tests/stCreate2/Create2OnDepth1023Filler.json",
        "state_tests/stCreate2/Create2OnDepth1024Filler.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "initcode",
    [
        pytest.param(INNER_CREATE2_INITCODE, id="depth1023"),
        pytest.param(NESTED_CREATE2_INITCODE, id="depth1024"),
    ],
)
def test_create2_on_depth(
    state_test: StateTestFiller,
    pre: Alloc,
    initcode: bytes,
) -> None:
    """Recurse to depth 1022, then CREATE2 with nested CREATE2 init code."""
    env = Environment(gas_limit=9223372036854775807)
    sender = pre.fund_eoa(amount=2**250)

    # Source: lll
    # { (MSTORE 0 (CALLDATALOAD 0)) (CALL (GAS) <caller> 0 0 32 0 0) }
    bouncer = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.CALL(address=Op.CALLER, args_size=0x20)
        + Op.STOP,
    )
    # Source: lll
    # { (MSTORE 0 (CALLDATALOAD 0)) (MSTORE 0 (ADD 2 (MLOAD 0))) (if (EQ (MLOAD 0) 0x0400) (seq (MSTORE 32 <initcode>) [[1]] (CREATE2 0 <64 - len> <len> 0))  (CALL (GAS) <bouncer> (EQ (MLOAD 0) 0x0400) 0 32 0 0)) }  # noqa: E501
    recurser = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.MSTORE(offset=0x0, value=Op.ADD(0x2, Op.MLOAD(offset=0x0)))
        + Conditional(
            condition=Op.EQ(Op.MLOAD(offset=0x0), 0x400),
            if_true=Op.MSTORE(
                offset=0x20, value=int.from_bytes(initcode, "big")
            )
            + Op.SSTORE(
                key=0x1,
                value=Op.CREATE2(
                    value=0,
                    offset=0x40 - len(initcode),
                    size=len(initcode),
                    salt=0,
                ),
            ),
            if_false=Op.POP(Op.CALL(address=bouncer, args_size=0x20)),
        )
        + Op.STOP,
    )

    created = compute_create_address(
        address=recurser, salt=0, initcode=initcode, opcode=Op.CREATE2
    )
    post: dict = {recurser: Account(storage={1: created})}
    if initcode == INNER_CREATE2_INITCODE:
        inner = compute_create_address(
            address=created, salt=0, initcode=b"", opcode=Op.CREATE2
        )
        post[created] = Account(storage={1: inner})
        post[inner] = Account(nonce=1)
    else:
        inner_initcode = NESTED_CREATE2_INITCODE[1:10]
        inner = compute_create_address(
            address=created,
            salt=0,
            initcode=inner_initcode,
            opcode=Op.CREATE2,
        )
        post[created] = Account(storage={1: inner})
        post[inner] = Account(nonce=1, storage={})
        post[
            compute_create_address(
                address=inner, salt=0, initcode=b"", opcode=Op.CREATE2
            )
        ] = Account.NONEXISTENT

    tx = Transaction(
        sender=sender,
        to=recurser,
        gas_limit=9151314442816847871,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
