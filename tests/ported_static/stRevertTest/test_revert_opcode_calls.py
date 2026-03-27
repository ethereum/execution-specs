"""
Test_revert_opcode_calls.

Ported from:
state_tests/stRevertTest/RevertOpcodeCallsFiller.json
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
    "000000000000000000000000737f82ed94146e759790d925492df5a8ced35885",
    "0000000000000000000000006b8268ac8921e6a6e59a4b1d51a76f4e807e17af",
    "000000000000000000000000bf3fc188d9c8d699ffa12f0369e3b2bcf8428f7c",
]
TX_GAS = [460000, 83622]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertOpcodeCallsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="d0-g1",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1-g0",
        ),
        pytest.param(
            1,
            1,
            0,
            id="d1-g1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2-g0",
        ),
        pytest.param(
            2,
            1,
            0,
            id="d2-g1",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3-g0",
        ),
        pytest.param(
            3,
            1,
            0,
            id="d3-g1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_revert_opcode_calls."""
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
    # {  [[10]] (CALL 260000 (CALLDATALOAD 0) 0 0 0 0 0)}
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0xA,
            value=Op.CALL(
                gas=0x3F7A0,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address("0x1ada72179309fd8a562e308928e38763a543ed6c"),  # noqa: E501
    )
    # Source: lll
    # { [[0]] (CALL 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]] 14 }  # noqa: E501
    addr_0xb0005374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
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
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address("0xceb48d108c874b5b014acdd1a2466d65a3d01de6"),  # noqa: E501
    )
    # Source: lll
    # { [[0]] (CALLCODE 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]] 14 }  # noqa: E501
    addr_0xb1005374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
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
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address("0x737f82ed94146e759790d925492df5a8ced35885"),  # noqa: E501
    )
    # Source: lll
    # { [[0]] (DELEGATECALL 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) [[2]] 14 }  # noqa: E501
    addr_0xb2005374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.DELEGATECALL(
                gas=0xC350,
                address=0x93A599BDE9A3B6390AFDB06952AA5EC0B8C44F3B,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x2, value=0xE)
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address("0x6b8268ac8921e6a6e59a4b1d51a76f4e807e17af"),  # noqa: E501
    )
    # Source: lll
    # { [[0]] (CALL 100000 <contract:0xb3305374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]] 14 }  # noqa: E501
    addr_0xb3005374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x186A0,
                address=0x652761B88018EA027F6F27E456FE55C2DC5D6A91,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x2, value=0xE)
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address("0xbf3fc188d9c8d699ffa12f0369e3b2bcf8428f7c"),  # noqa: E501
    )
    # Source: lll
    # { [[4]] (CALL 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[5]] 14 }  # noqa: E501
    addr_0xb3305374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x4,
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
        + Op.SSTORE(key=0x5, value=0xE)
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address("0x652761b88018ea027f6f27e456fe55c2dc5d6a91"),  # noqa: E501
    )
    # Source: lll
    # { [[1]] 12 (REVERT 0 1) [[3]] 13 }
    addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0xC)
        + Op.REVERT(offset=0x0, size=0x1)
        + Op.SSTORE(key=0x3, value=0xD)
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address("0x93a599bde9a3b6390afdb06952aa5ec0b8c44f3b"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={}
                ),
                target: Account(storage={10: 1}),
                addr_0xb0005374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={0: 0, 2: 14}, nonce=0
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={}
                ),
                addr_0xb0005374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={}
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={}
                ),
                target: Account(storage={10: 1}),
                addr_0xb1005374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={0: 0, 2: 14}, nonce=0
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={}
                ),
                addr_0xb1005374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={}
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={}
                ),
                target: Account(storage={10: 1}),
                addr_0xb2005374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={0: 0, 2: 14}, nonce=0
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={}
                ),
                addr_0xb2005374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={}
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": [0], "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={}
                ),
                target: Account(storage={10: 1}),
                addr_0xb3005374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={0: 1, 2: 14}, nonce=0
                ),
                addr_0xb3305374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={4: 0, 5: 14}, nonce=0
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": [1], "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={}
                ),
                target: Account(storage={10: 0}),
                addr_0xb3005374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={0: 0, 2: 0}, nonce=0
                ),
                addr_0xb3305374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={4: 0, 5: 0}, nonce=0
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
