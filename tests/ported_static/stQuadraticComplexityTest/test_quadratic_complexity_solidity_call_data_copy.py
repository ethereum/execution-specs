"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stQuadraticComplexityTest
QuadraticComplexitySolidity_CallDataCopyFiller.json
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

TX_DATA = [
    "61a47706000000000000000000000000000000000000000000000000000000000000c350",
    "61a47706000000000000000000000000000000000000000000000000000000000000c350",
]

TX_GAS = [150000, 250000000]

TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stQuadraticComplexityTest/QuadraticComplexitySolidity_CallDataCopyFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 1, 0, id="case1"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_quadratic_complexity_solidity_call_data_copy(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x6A7EEAC5F12B409D42028F66B0B2132535EE158CFDA439E3BFDD4558E8F4BF6C
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=350000000,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x0)
            + Op.EXP(0x2, 0xE0)
            + Op.SWAP1
            + Op.DIV
            + Op.JUMPI(pc=0x15, condition=Op.EQ(0x61A47706, Op.DUP1))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x1E]
            + Op.CALLDATALOAD(offset=0x4)
            + Op.JUMP(pc=0x24)
            + Op.JUMPDEST
            + Op.RETURN(offset=0x0, size=0x0)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.DUP2
            + Op.PUSH1[0x0]
            + Op.DUP2
            + Op.SWAP1
            + Op.SSTORE
            + Op.POP
            + Op.PUSH20[0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B]
            + Op.SWAP1
            + Op.POP
            + Op.JUMPDEST
            + Op.JUMPI(pc=0xBF, condition=Op.ISZERO(Op.SGT(Op.DUP3, 0x0)))
            + Op.AND(Op.SUB(Op.EXP(0x2, 0xA0), 0x1), Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.MSTORE(
                offset=Op.DUP2,
                value=0x6A75737400000000000000000000000000000000000000000000000000000000,  # noqa: E501
            )
            + Op.PUSH1[0x4]
            + Op.ADD
            + Op.MSTORE(
                offset=Op.DUP2,
                value=0x63616C6C00000000000000000000000000000000000000000000000000000000,  # noqa: E501
            )
            + Op.PUSH1[0x20]
            + Op.ADD
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.DUP6
            + Op.SUB(Op.GAS, 0x15)
            + Op.POP(Op.CALL)
            + Op.POP
            + Op.SUB(Op.DUP3, 0x1)
            + Op.SWAP2
            + Op.POP
            + Op.JUMP(pc=0x45)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.JUMP
        ),
        balance=0x11C37937E08000,
        nonce=0,
        address=Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: LLL
    # { (CALLDATACOPY 0 0 50000) }
    callee = pre.deploy_contract(
        code=(
            Op.CALLDATACOPY(dest_offset=0x0, offset=0x0, size=0xC350) + Op.STOP
        ),
        balance=0x4C4B40,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x11C37937E08000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": -1, "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract: Account(
                    storage={},
                    nonce=0,
                    code=bytes.fromhex(
                        "60003560e060020a9004806361a4770614601557005b601e6004356024565b60006000f35b60008160008190555073b94f5374fce5edbc8e2a8697c15331677e6ebf0b90505b600082131560bf5780600160a060020a03166000600060007f6a7573740000000000000000000000000000000000000000000000000000000081526004017f63616c6c000000000000000000000000000000000000000000000000000000008152602001600060008560155a03f150506001820391506045565b505056"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={},
                    nonce=0,
                    code=bytes.fromhex("61c350600060003700"),
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
