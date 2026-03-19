"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest/RevertOpcodeDirectCallFiller.json
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
    "000000000000000000000000ceb48d108c874b5b014acdd1a2466d65a3d01de6",
    "000000000000000000000000ceb48d108c874b5b014acdd1a2466d65a3d01de6",
]

TX_GAS = [460000, 62912]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stRevertTest/RevertOpcodeDirectCallFiller.json",  # noqa: E501
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
def test_revert_opcode_direct_call(
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
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0xC)
            + Op.REVERT(offset=0x0, size=0x1)
            + Op.SSTORE(key=0x3, value=0xD)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0x93a599bde9a3b6390afdb06952aa5ec0b8c44f3b"),  # noqa: E501
    )
    # Source: LLL
    # { [[0]] (CALL 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]] 14 }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0xC350,
                    address=0x93A599BDE9A3B6390AFDB06952AA5EC0B8C44F3B,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x2, value=0xE)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0xceb48d108c874b5b014acdd1a2466d65a3d01de6"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0xA,
                value=Op.CALL(
                    gas=0xEA60,
                    address=Op.CALLDATALOAD(offset=0x0),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0xf94d87faf19d8c731e70e1b0a25f9668718f6e17"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600c60015560016000fd600d60035500")
                ),
                contract: Account(
                    storage={2: 14},
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f1600055600e60025500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000600060006000600060003561ea60f1600a5500"
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("600c60015560016000fd600d60035500")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f1600055600e60025500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000600060006000600060003561ea60f1600a5500"
                    )
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
