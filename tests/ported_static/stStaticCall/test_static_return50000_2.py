"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_Return50000_2Filler.json
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
    ["tests/static/state_tests/stStaticCall/static_Return50000_2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_return50000_2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0xE7C72B378297589ACEE4E0BA3272841BCFC5E220F86DE253F890274CFEE9E474
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89250000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0xC34F))
            + Op.RETURN(offset=Op.MLOAD(offset=0x0), size=0x1)
            + Op.STOP
        ),
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address("0x0d08fb89197bd8f97c770ed75e28ed610a3016e9"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    # Source: LLL
    # { [[ 0 ]] (CALL (GAS) <contract:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[ 1 ]] 1 }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=0xDF43BBA207127B641624B20497FA07055F4A3939,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address("0x9a8ca98b299a0220faad60948d01ce83ccc97831"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.JUMPDEST
            + Op.JUMPI(
                pc=0x3D,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350)),
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0x61C,
                    address=0xD08FB89197BD8F97C770ED75E28ED610A3016E9,
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
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address("0xdf43bba207127b641624b20497fa07055f4a3939"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("61c34f356000526001600051f300")
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600073df43bba207127b641624b20497fa07055f4a39395af1600055600160015500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={0: 1, 1: 50000},
                    code=bytes.fromhex(
                        "5b61c3506080511015603d576000600061c3506000730d08fb89197bd8f97c770ed75e28ed610a3016e961061cfa6000556001608051016080526000565b60805160015500"  # noqa: E501
                    ),
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=15500000,
        value=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
