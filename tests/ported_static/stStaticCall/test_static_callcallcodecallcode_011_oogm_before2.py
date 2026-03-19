"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callcallcodecallcode_011_OOGMBefore2Filler.json
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
    "00000000000000000000000087f0bb05316a8d8146646a151a64f38ae9d25176",
    "0000000000000000000000001dffdbfbe33709f17b6e90137242c109917a994b",
    "00000000000000000000000094c82267a4e8333afb80073fbaed3fe5973adc7c",
]

TX_GAS = [172000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMBefore2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
        pytest.param(2, 0, 0, id="case2"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_callcallcodecallcode_011_oogm_before2(
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
            + Op.POP(
                Op.CALLCODE(
                    gas=0x4E34,
                    address=0xD4286AC3FCAC436406BC95F5B0176AD49AED7F7C,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x20, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x1dffdbfbe33709f17b6e90137242c109917a994b"),  # noqa: E501
    )
    # Source: LLL
    # {  (MSTORE 0 (CALLDATALOAD 0)) [[ 0 ]] (STATICCALL 150000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
            + Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0x249F0,
                    address=0x8BDE6A10A1792232FD09B528800D9AC2A6835424,
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
        address=Address("0x6e143211e9d36eaeebe65f6ed69d6c28500040d6"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x3, value=0x1)
            + Op.POP(
                Op.CALLCODE(
                    gas=0x4E34,
                    address=0xD4286AC3FCAC436406BC95F5B0176AD49AED7F7C,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x20, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x87f0bb05316a8d8146646a151a64f38ae9d25176"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x20, value=0x1)
            + Op.POP(
                Op.CALLCODE(
                    gas=0x9C90,
                    address=Op.CALLDATALOAD(offset=0x0),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x20, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x8bde6a10a1792232fd09b528800d9ac2a6835424"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALLCODE(
                    gas=0x4E34,
                    address=0xD4286AC3FCAC436406BC95F5B0176AD49AED7F7C,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x20, value=0x1)
            + Op.STOP
        ),
        balance=10,
        nonce=0,
        address=Address("0x94c82267a4e8333afb80073fbaed3fe5973adc7c"),  # noqa: E501
    )
    callee_4 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x20, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xd4286ac3fcac436406bc95f5b0176ad49aed7f7c"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b6040600060406000600073d4286ac3fcac436406bc95f5b0176ad49aed7f7c614e34f250600160205200"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000356000526040600060406000738bde6a10a1792232fd09b528800d9ac2a6835424620249f0fa600055600160015500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60016003556040600060406000600073d4286ac3fcac436406bc95f5b0176ad49aed7f7c614e34f250600160205200"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "600160205260406000604060006000600035619c90f250600160205200"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6040600060406000600173d4286ac3fcac436406bc95f5b0176ad49aed7f7c614e34f250600160205200"  # noqa: E501
                    )
                ),
                callee_4: Account(code=bytes.fromhex("600160205200")),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b6040600060406000600073d4286ac3fcac436406bc95f5b0176ad49aed7f7c614e34f250600160205200"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000356000526040600060406000738bde6a10a1792232fd09b528800d9ac2a6835424620249f0fa600055600160015500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60016003556040600060406000600073d4286ac3fcac436406bc95f5b0176ad49aed7f7c614e34f250600160205200"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "600160205260406000604060006000600035619c90f250600160205200"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6040600060406000600173d4286ac3fcac436406bc95f5b0176ad49aed7f7c614e34f250600160205200"  # noqa: E501
                    )
                ),
                callee_4: Account(code=bytes.fromhex("600160205200")),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b6040600060406000600073d4286ac3fcac436406bc95f5b0176ad49aed7f7c614e34f250600160205200"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000356000526040600060406000738bde6a10a1792232fd09b528800d9ac2a6835424620249f0fa600055600160015500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60016003556040600060406000600073d4286ac3fcac436406bc95f5b0176ad49aed7f7c614e34f250600160205200"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "600160205260406000604060006000600035619c90f250600160205200"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6040600060406000600173d4286ac3fcac436406bc95f5b0176ad49aed7f7c614e34f250600160205200"  # noqa: E501
                    )
                ),
                callee_4: Account(code=bytes.fromhex("600160205200")),
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
