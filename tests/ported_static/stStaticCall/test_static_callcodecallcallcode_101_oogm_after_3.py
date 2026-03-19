"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callcodecallcallcode_101_OOGMAfter_3Filler.json
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
    "00000000000000000000000077d2ecb3f4d887934c7c8f304831ea89e08cb30d",
    "000000000000000000000000e2fa228586f5c62a6728d17728f4622d05d84e45",
]

TX_GAS = [172000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMAfter_3Filler.json",  # noqa: E501
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
def test_static_callcodecallcallcode_101_oogm_after_3(
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
        gas_limit=10000000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=0x9C90,
                address=0x65BE40505E6165809F16BFC5CDBA14169BC97614,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x2aba60e14f876dac315953942316a9a2f80c3ad5"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x335c5531b84765a7626e6e76688f18b81be5259c"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.DELEGATECALL(
                    gas=0x4E34,
                    address=0xB126C622075B1189FB6C45E851641CFADDF65B36,
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
        address=Address("0x65be40505e6165809f16bfc5cdba14169bc97614"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.DELEGATECALL(
                    gas=0xEAF6,
                    address=0xB867C4BF480D6DCD06716BCDB0F9BCF3BB5710BF,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.GAS)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x77d2ecb3f4d887934c7c8f304831ea89e08cb30d"),  # noqa: E501
    )
    callee_4 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.DELEGATECALL(
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
        address=Address("0x96bba71c203b7339624a350fe004f71c3d669aee"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (CALLCODE (GAS) (CALLDATALOAD 0) 0 0 0 0 0) [[ 1 ]] 1 }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALLCODE(
                    gas=Op.GAS,
                    address=Op.CALLDATALOAD(offset=0x0),
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
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xaab59f13d96113334fab5c68e4e62b61f6cbf647"),  # noqa: E501
    )
    callee_5 = pre.deploy_contract(
        code=Op.SSTORE(key=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xb126c622075b1189fb6c45e851641cfaddf65b36"),  # noqa: E501
    )
    callee_6 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0x9C90,
                    address=0x96BBA71C203B7339624A350FE004F71C3D669AEE,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x3E,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350)),
            )
            + Op.POP(Op.EXTCODESIZE(address=0x1))
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x22)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xb867c4bf480d6dcd06716bcdb0f9bcf3bb5710bf"),  # noqa: E501
    )
    callee_7 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.DELEGATECALL(
                    gas=0xEAF6,
                    address=0x2ABA60E14F876DAC315953942316A9A2F80C3AD5,
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
        address=Address("0xe2fa228586f5c62a6728d17728f4622d05d84e45"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "60406000604060007365be40505e6165809f16bfc5cdba14169bc97614619c90fa00"  # noqa: E501
                    )
                ),
                callee_1: Account(code=bytes.fromhex("600160035200")),
                callee_2: Account(
                    code=bytes.fromhex(
                        "604060006040600073b126c622075b1189fb6c45e851641cfaddf65b36614e34f450600160035200"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "604060006040600073b867c4bf480d6dcd06716bcdb0f9bcf3bb5710bf61eaf6f46000555a60015500"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "604060006040600073335c5531b84765a7626e6e76688f18b81be5259c614e34f450600160035200"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "600060006000600060006000355af2600055600160015500"
                    ),
                ),
                callee_5: Account(code=bytes.fromhex("600160035500")),
                callee_6: Account(
                    code=bytes.fromhex(
                        "60406000604060007396bba71c203b7339624a350fe004f71c3d669aee619c90fa505b61c3506080511015603e5760013b506001608051016080526022565b00"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6040600060406000732aba60e14f876dac315953942316a9a2f80c3ad561eaf6f4600055600160015500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "60406000604060007365be40505e6165809f16bfc5cdba14169bc97614619c90fa00"  # noqa: E501
                    )
                ),
                callee_1: Account(code=bytes.fromhex("600160035200")),
                callee_2: Account(
                    code=bytes.fromhex(
                        "604060006040600073b126c622075b1189fb6c45e851641cfaddf65b36614e34f450600160035200"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "604060006040600073b867c4bf480d6dcd06716bcdb0f9bcf3bb5710bf61eaf6f46000555a60015500"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "604060006040600073335c5531b84765a7626e6e76688f18b81be5259c614e34f450600160035200"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "600060006000600060006000355af2600055600160015500"
                    ),
                ),
                callee_5: Account(code=bytes.fromhex("600160035500")),
                callee_6: Account(
                    code=bytes.fromhex(
                        "60406000604060007396bba71c203b7339624a350fe004f71c3d669aee619c90fa505b61c3506080511015603e5760013b506001608051016080526022565b00"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "6040600060406000732aba60e14f876dac315953942316a9a2f80c3ad561eaf6f4600055600160015500"  # noqa: E501
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
