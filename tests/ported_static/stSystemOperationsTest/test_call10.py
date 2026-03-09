"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSystemOperationsTest/Call10Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stSystemOperationsTest/Call10Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call10(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0xE7C72B378297589ACEE4E0BA3272841BCFC5E220F86DE253F890274CFEE9E474
    )
    callee = Address("0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    pre[callee] = Account(balance=7000, nonce=0)
    # Source: LLL
    # { (def 'i 0x80) (for {} (< @i 10) [i](+ @i 1) [[ 0 ]](CALL 0xfffffffffff <eoa:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 1 0 50000 0 0) ) [[ 1 ]] @i}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.JUMPDEST
            + Op.JUMPI(
                pc=0x42,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xA)),
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0xFFFFFFFFFFF,
                    address=0xD9B97C712EBCE43F3C19179BBEF44B550F9E8BC0,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0xC350,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x0)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80))
            + Op.STOP
        ),
        balance=1000,
        nonce=0,
        address=Address("0xfda03fa18cbda0970e18071f363bea4c9c90dfb6"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=200000,
        value=10,
    )

    post = {
        contract: Account(storage={0: 1, 1: 10}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
