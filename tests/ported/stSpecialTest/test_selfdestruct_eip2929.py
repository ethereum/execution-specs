"""
Martin: @tkstanczak requested a state-test regarding selfdestructs in relation to EIP-2929. I made one, which tests different variants of hot/cold accounts, and even precompile beneficiaries. https://github.com/holiman/goevmlab/blob/selfdestruct_2929/examples/selfdestruct_2929/main.go#L94

Ported from:
tests/static/state_tests/stSpecialTest/selfdestructEIP2929Filler.json

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0xcc
    push1 0x00
    call
    pop
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0xdd
    push1 0x00
    call
    pop
    push1 0x00
    push1 0x00
    ... (166 more instructions)

callee_2 code:
    push1 0x00
    calldataload
    push21 0xffffffffffffffffffffffffffffffffffffffffff
    and
    selfdestruct
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stSpecialTest/selfdestructEIP2929Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_selfdestruct_eip2929(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Martin: @tkstanczak requested a state-test regarding selfdestructs in relation to EIP-2929. I made one, which tests different variants of hot/cold accounts, and even precompile beneficiaries. https://github.com/holiman/goevmlab/blob/selfdestruct_2929/examples/selfdestruct_2929/main.go#L94."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0xb686be1a7a0f441fae9583884043ac034fe82089")
    callee = Address("0x7704d8a022a1ba8f3539fc82c7d7fb065abc0df3")
    callee_1 = Address("0x9ecbdbdbd8448cdd955755cdd81d6918e436f68a")
    callee_2 = Address("0xd2e5c26a2f035a63d0859e255621ed1e57148085")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10944489199640098,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[callee] = Account(balance=0, nonce=1)
    pre[callee_1] = Account(balance=0, nonce=1)
    pre[contract] = Account(
        balance=1,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0xcc] + Op.PUSH1[0x0] + Op.CALL + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0xdd] + Op.PUSH1[0x0] + Op.CALL + Op.POP
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x3] + Op.PUSH1[0x0] + Op.CALL + Op.POP
        + Op.PUSH1[0xaa] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.GAS
        + Op.CALL + Op.POP + Op.PUSH1[0xaa] + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.GAS + Op.CALL + Op.POP
        + Op.PUSH1[0xbb] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.GAS
        + Op.CALL + Op.POP + Op.PUSH1[0xbb] + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.GAS + Op.CALL + Op.POP
        + Op.PUSH1[0xcc] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.GAS
        + Op.CALL + Op.POP + Op.PUSH1[0xcc] + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.GAS + Op.CALL + Op.POP
        + Op.PUSH1[0xdd] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.GAS
        + Op.CALL + Op.POP + Op.PUSH1[0xdd] + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.GAS + Op.CALL + Op.POP + Op.PUSH1[0x1]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.GAS + Op.CALL + Op.POP
        + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.GAS
        + Op.CALL + Op.POP + Op.PUSH1[0x2] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH2[0xdead] + Op.GAS + Op.CALL + Op.POP + Op.PUSH1[0x2] + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.GAS + Op.CALL + Op.POP + Op.PUSH1[0x3]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0xdead] + Op.GAS + Op.CALL + Op.POP
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE
    ),
    )
    pre[callee_2] = Account(
        balance=1,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD
        + Op.PUSH21[0xffffffffffffffffffffffffffffffffffffffffff] + Op.AND
        + Op.SELFDESTRUCT
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=b"",
        gas_limit=8000000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
