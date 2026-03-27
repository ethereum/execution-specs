"""
Test_revert_depth2.

Ported from:
state_tests/stRevertTest/RevertDepth2Filler.json
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
]
TX_GAS = [170685, 136685]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertDepth2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1",
        ),
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
    """Test_revert_depth2."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { [[0]] (ADD 1 (SLOAD 0)) [[1]] (CALL 150000 <contract:0xb000000000000000000000000000000000000000> 0 0 0 0 0) [[2]] (CALL 150000 <contract:0xd000000000000000000000000000000000000000> 0 0 0 0 0)}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
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
        + Op.STOP,
        nonce=0,
        address=Address("0x68ea09e164a8b66de117a2c306b3966e6d71ca93"),  # noqa: E501
    )
    # Source: lll
    # { [[0]] (ADD 1 (SLOAD 0)) [[1]] (CALL 50000 <contract:0xc000000000000000000000000000000000000000> 0 0 0 0 0)}  # noqa: E501
    addr_0xb000000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
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
        + Op.STOP,
        nonce=0,
        address=Address("0x0707f29673f05e46feeb7c4766419a222010ae45"),  # noqa: E501
    )
    # Source: lll
    # { [[0]] (ADD 1 (SLOAD 0)) }
    addr_0xc000000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
        + Op.STOP,
        nonce=0,
        address=Address("0xc47bcbf49dd735566cfde927821e938d5b33014c"),  # noqa: E501
    )
    # Source: lll
    # { [[0]] (ADD 1 (SLOAD 0)) [[1]] (CALL 50000 <contract:0xc000000000000000000000000000000000000000> 0 0 0 0 0) [[2]] (GAS)}  # noqa: E501
    addr_0xd000000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
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
        + Op.STOP,
        nonce=0,
        address=Address("0x78ed2eb0809cd080c7837dc83afc388a2b98d200"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 0, 1: 0, 2: 0}),
                addr_0xb000000000000000000000000000000000000000: Account(
                    storage={0: 0, 1: 0}
                ),
                addr_0xc000000000000000000000000000000000000000: Account(
                    storage={0: 0}
                ),
                addr_0xd000000000000000000000000000000000000000: Account(
                    storage={0: 0, 1: 0, 2: 0}
                ),
                sender: Account(nonce=1),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=0,
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
