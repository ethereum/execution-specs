"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_callcallcallcode_001Filler.json
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
    "0000000000000000000000009121e482add3986513a14639db36d5ec5ae41fb8",
    "000000000000000000000000bf23f3306533431b2ee5e4ca95e0a0834c090105",
]

TX_GAS = [3000000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_callcallcallcode_001Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_callcallcallcode_001(
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
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    callee = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x335c5531b84765a7626e6e76688f18b81be5259c"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x3, value=0x1)
            + Op.POP(
                Op.STATICCALL(
                    gas=0x493E0,
                    address=0x82D1FD8C6ED53A58BD8B065074A6B572A7CA89FA,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x3, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x5ccb387ab81f41f0b490664795e7004d5d14bf91"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x3, value=0x1)
            + Op.POP(
                Op.STATICCALL(
                    gas=0x493E0,
                    address=0xF18DDE9381A558C4BE0B84B0F3A17E22B3F9FFCE,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x3, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x69ce59f2414271f3e079542ef3893a021d7d68ea"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x3, value=0x1)
            + Op.SSTORE(key=0x4, value=Op.CALLER)
            + Op.SSTORE(key=0x7, value=Op.CALLVALUE)
            + Op.SSTORE(key=0x14A, value=Op.ADDRESS)
            + Op.SSTORE(key=0x14C, value=Op.ORIGIN)
            + Op.SSTORE(key=0x150, value=Op.CALLDATASIZE)
            + Op.SSTORE(key=0x152, value=Op.CODESIZE)
            + Op.SSTORE(key=0x154, value=Op.GASPRICE)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x7e63847aad8ca50fb7c04777dce6871a6bf8de0c"),  # noqa: E501
    )
    callee_4 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x3, value=0x1)
            + Op.POP(
                Op.DELEGATECALL(
                    gas=0x3D090,
                    address=0x7E63847AAD8CA50FB7C04777DCE6871A6BF8DE0C,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x3, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x82d1fd8c6ed53a58bd8b065074a6b572a7ca89fa"),  # noqa: E501
    )
    callee_5 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0x55730,
                    address=0x5CCB387AB81F41F0B490664795E7004D5D14BF91,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x3, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x9121e482add3986513a14639db36d5ec5ae41fb8"),  # noqa: E501
    )
    callee_6 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0x55730,
                    address=0x69CE59F2414271F3E079542EF3893A021D7D68EA,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xbf23f3306533431b2ee5e4ca95e0a0834c090105"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1 }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=Op.CALLDATALOAD(offset=0x0),
                    value=Op.CALLVALUE,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    callee_7 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x3, value=0x1)
            + Op.POP(
                Op.DELEGATECALL(
                    gas=0x3D090,
                    address=0x335C5531B84765A7626E6E76688F18B81BE5259C,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x3, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xf18dde9381a558c4be0b84b0f3a17e22b3f9ffce"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600160035200")),
                callee_1: Account(
                    code=bytes.fromhex(
                        "600160035260406000604060007382d1fd8c6ed53a58bd8b065074a6b572a7ca89fa620493e0fa50600160035200"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6001600352604060006040600073f18dde9381a558c4be0b84b0f3a17e22b3f9ffce620493e0fa50600160035200"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "600160035533600455346007553061014a553261014c55366101505538610152553a6101545500"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "60016003526040600060406000737e63847aad8ca50fb7c04777dce6871a6bf8de0c6203d090f450600160035200"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "6040600060406000735ccb387ab81f41f0b490664795e7004d5d14bf9162055730fa600055600160035200"  # noqa: E501
                    ),
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "60406000604060007369ce59f2414271f3e079542ef3893a021d7d68ea62055730fa60005500"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000600060006000346000355af1600055600160015500"
                    ),
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6001600352604060006040600073335c5531b84765a7626e6e76688f18b81be5259c6203d090f450600160035200"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600160035200")),
                callee_1: Account(
                    code=bytes.fromhex(
                        "600160035260406000604060007382d1fd8c6ed53a58bd8b065074a6b572a7ca89fa620493e0fa50600160035200"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6001600352604060006040600073f18dde9381a558c4be0b84b0f3a17e22b3f9ffce620493e0fa50600160035200"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "600160035533600455346007553061014a553261014c55366101505538610152553a6101545500"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "60016003526040600060406000737e63847aad8ca50fb7c04777dce6871a6bf8de0c6203d090f450600160035200"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "6040600060406000735ccb387ab81f41f0b490664795e7004d5d14bf9162055730fa600055600160035200"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "60406000604060007369ce59f2414271f3e079542ef3893a021d7d68ea62055730fa60005500"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000600060006000346000355af1600055600160015500"
                    ),
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6001600352604060006040600073335c5531b84765a7626e6e76688f18b81be5259c6203d090f450600160035200"  # noqa: E501
                    )
                ),
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
