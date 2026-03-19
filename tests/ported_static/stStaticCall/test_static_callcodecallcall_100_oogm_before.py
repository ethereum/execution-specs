"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callcodecallcall_100_OOGMBeforeFiller.json
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
    "000000000000000000000000cc95c09a27cbe0199e6d898e64b4dc1774f164e1",
    "0000000000000000000000004670334e92c4d14771faadb3c90c987cb337acca",
]

TX_GAS = [172000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_callcodecallcall_100_OOGMBeforeFiller.json",  # noqa: E501
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
def test_static_callcodecallcall_100_oogm_before(
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
            Op.SSTORE(key=0x3, value=0x1)
            + Op.POP(
                Op.STATICCALL(
                    gas=0x4E34,
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
        nonce=0,
        address=Address("0x4670334e92c4d14771faadb3c90c987cb337acca"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0x9C90,
                    address=Op.CALLDATALOAD(offset=0x0),
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x3, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x570b7a7eb7d0539d77442b6262127229b9b6c19f"),  # noqa: E501
    )
    # Source: LLL
    # {  (MSTORE 0 (CALLDATALOAD 0)) [[ 0 ]] (DELEGATECALL 150000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1  }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
            + Op.SSTORE(
                key=0x0,
                value=Op.DELEGATECALL(
                    gas=0x249F0,
                    address=0x570B7A7EB7D0539D77442B6262127229B9B6C19F,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xb1dddce88104538f48811f8e62af99666e0c3a4e"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
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
            + Op.STATICCALL(
                gas=0x4E34,
                address=0x335C5531B84765A7626E6E76688F18B81BE5259C,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xcc95c09a27cbe0199e6d898e64b4dc1774f164e1"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600160035200")),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6001600355604060006040600073335c5531b84765a7626e6e76688f18b81be5259c614e34fa50600160035200"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6040600060406000600035619c90fa50600160035200"
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "600035600052604060006040600073570b7a7eb7d0539d77442b6262127229b9b6c19f620249f0f4600055600160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b604060006040600073335c5531b84765a7626e6e76688f18b81be5259c614e34fa00"  # noqa: E501
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
                        "6001600355604060006040600073335c5531b84765a7626e6e76688f18b81be5259c614e34fa50600160035200"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6040600060406000600035619c90fa50600160035200"
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "600035600052604060006040600073570b7a7eb7d0539d77442b6262127229b9b6c19f620249f0f4600055600160015500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b604060006040600073335c5531b84765a7626e6e76688f18b81be5259c614e34fa00"  # noqa: E501
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
