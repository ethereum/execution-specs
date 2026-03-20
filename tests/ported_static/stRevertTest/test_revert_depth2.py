"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest/RevertDepth2Filler.json
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

TX_GAS = [170685, 136685]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRevertTest/RevertDepth2Filler.json"],
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
def test_revert_depth2(
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
            Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
            + Op.SSTORE(
                key=0x1,
                value=Op.CALL(
                    gas=0xC350,
                    address=0xC47BCBF49DD735566CFDE927821E938D5B33014C,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x0707f29673f05e46feeb7c4766419a222010ae45"),  # noqa: E501
    )
    # Source: LLL
    # { [[0]] (ADD 1 (SLOAD 0)) [[1]] (CALL 150000 <contract:0xb000000000000000000000000000000000000000> 0 0 0 0 0) [[2]] (CALL 150000 <contract:0xd000000000000000000000000000000000000000> 0 0 0 0 0)}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
            + Op.SSTORE(
                key=0x1,
                value=Op.CALL(
                    gas=0x249F0,
                    address=0x707F29673F05E46FEEB7C4766419A222010AE45,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x2,
                value=Op.CALL(
                    gas=0x249F0,
                    address=0x78ED2EB0809CD080C7837DC83AFC388A2B98D200,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x68ea09e164a8b66de117a2c306b3966e6d71ca93"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
            + Op.SSTORE(
                key=0x1,
                value=Op.CALL(
                    gas=0xC350,
                    address=0xC47BCBF49DD735566CFDE927821E938D5B33014C,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x2, value=Op.GAS)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x78ed2eb0809cd080c7837dc83afc388a2b98d200"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0))) + Op.STOP
        ),
        nonce=0,
        address=Address("0xc47bcbf49dd735566cfde927821e938d5b33014c"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000546001016000556000600060006000600073c47bcbf49dd735566cfde927821e938d5b33014c61c350f160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60005460010160005560006000600060006000730707f29673f05e46feeb7c4766419a222010ae45620249f0f1600155600060006000600060007378ed2eb0809cd080c7837dc83afc388a2b98d200620249f0f160025500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000546001016000556000600060006000600073c47bcbf49dd735566cfde927821e938d5b33014c61c350f16001555a60025500"  # noqa: E501
                    )
                ),
                callee_2: Account(code=bytes.fromhex("60005460010160005500")),
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000546001016000556000600060006000600073c47bcbf49dd735566cfde927821e938d5b33014c61c350f160015500"  # noqa: E501
                    )
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60005460010160005560006000600060006000730707f29673f05e46feeb7c4766419a222010ae45620249f0f1600155600060006000600060007378ed2eb0809cd080c7837dc83afc388a2b98d200620249f0f160025500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000546001016000556000600060006000600073c47bcbf49dd735566cfde927821e938d5b33014c61c350f16001555a60025500"  # noqa: E501
                    )
                ),
                callee_2: Account(code=bytes.fromhex("60005460010160005500")),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
