"""
Requires a separate pre-alloc group due to time required to fill when...

Ported from:
tests/static/state_tests/stStaticCall/static_LoopCallsThenRevertFiller.json
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
    "",
    "",
]

TX_GAS = [10000000, 9000000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_LoopCallsThenRevertFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 1, 0, id="case1"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_loop_calls_then_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Requires a separate pre-alloc group due to time required to fill..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.ADD(0x1, Op.MLOAD(offset=0x0)))
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x59c89b27361fd637262b13489f28923c835e17b2"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.JUMPDEST
            + Op.MSTORE(
                offset=0x0, value=Op.SUB(Op.CALLDATALOAD(offset=0x0), 0x1)
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0xC350,
                    address=0x59C89B27361FD637262B13489F28923C835E17B2,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPI(pc=0x0, condition=Op.MLOAD(offset=0x0))
        ),
        storage={0x0: 0x352},
        nonce=0,
        address=Address("0x7a2af5cc0310371cce006e472ed3b5d68e62f839"),  # noqa: E501
    )
    # Source: LLL
    # { (MSTORE 0 850) [[ 0 ]] (CALL (- (GAS) 10000) <contract:0xa000000000000000000000000000000000000000> 0 0 32 0 0) [[ 1 ]] 1 }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x352)
            + Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x2710),
                    address=0x7A2AF5CC0310371CCE006E472ED3B5D68E62F839,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x20,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xd64495cbba16d27a88b96f2a72417b957ed4cae6"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("60005160010160005200")),
                callee_1: Account(
                    storage={0: 850},
                    code=bytes.fromhex(
                        "5b60016000350360005260006000600060007359c89b27361fd637262b13489f28923c835e17b261c350fa50600051600057"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "61035260005260006000602060006000737a2af5cc0310371cce006e472ed3b5d68e62f8396127105a03f1600055600160015500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("60005160010160005200")),
                callee_1: Account(
                    storage={0: 850},
                    code=bytes.fromhex(
                        "5b60016000350360005260006000600060007359c89b27361fd637262b13489f28923c835e17b261c350fa50600051600057"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "61035260005260006000602060006000737a2af5cc0310371cce006e472ed3b5d68e62f8396127105a03f1600055600160015500"  # noqa: E501
                    ),
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
