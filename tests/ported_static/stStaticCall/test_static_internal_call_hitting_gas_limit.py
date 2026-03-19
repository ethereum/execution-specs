"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_InternalCallHittingGasLimitFiller.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_InternalCallHittingGasLimitFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_internal_call_hitting_gas_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adf5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0x07C857D62C76CE09F2E8EC3FA9277578C67B69C6547364568FDDB841071E5BD7
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1C,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350)),
            )
            + Op.POP(Op.EXTCODESIZE(address=0x1))
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x0)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x285bb5c8a71646ab9a5796d4a718cc4826af8d06"),  # noqa: E501
    )
    # Source: LLL
    # { (STATICCALL 5000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=0x1388,
                address=0x285BB5C8A71646AB9A5796D4A718CC4826AF8D06,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xF4240,
        nonce=0,
        address=Address("0x5a755ead8f1201283f750b2f77af7d03399d5feb"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xF4240)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600073285bb5c8a71646ab9a5796d4a718cc4826af8d06611388fa00"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=21100,
        value=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
