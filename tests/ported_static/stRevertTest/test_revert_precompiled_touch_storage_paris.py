"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest
RevertPrecompiledTouch_storage_ParisFiller.json
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
    "00000000000000000000000087aaeb9e422487283b0b008ef445e32acb9dd1ae",
    "00000000000000000000000031f52a66cf9d94c60f089a2ca9c4e784261c57fa",
    "000000000000000000000000de1200b7ecaea2d15b57d0f331ad5ade8e924255",
    "00000000000000000000000010ef6d6218ada53728683cec4d5160c8c72159bd",
]

TX_GAS = [100000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stRevertTest/RevertPrecompiledTouch_storage_ParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
        pytest.param(2, 0, 0, id="case2"),
        pytest.param(3, 0, 0, id="case3"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_precompiled_touch_storage_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x68795c4aa09d6f4ed3e5deddf8c2ad3049a601da")
    sender = EOA(
        key=0x0FF8D58222F34F6890DDAA468C023B77D6691ED7D3C4DCDDAE38336212FAF54B
    )
    callee = Address("0x0dc4b229346287fe9fa441960081a9886b71c42d")
    callee_3 = Address("0x3a3eee808c401a574f92824dc64d89edb05fafe4")
    callee_4 = Address("0x46ac2e7e1550d911e5a72fbc51c15ca817dbb1d5")
    callee_5 = Address("0x4757608f18b70777ae788dd4056eeed52f7aa68f")
    callee_6 = Address("0x6d15138ce372d9b89ee38fc3973b715477426f11")
    callee_8 = Address("0x9deb46a3b3e955bd56ecc4072da4b42bd9b5db2c")
    callee_9 = Address("0xa8fd4cb9c2c538ed7ff94c3b711b2e08a08c7fb8")
    callee_10 = Address("0xda7f8add6896b7e58f28331a97b315dde5fb8cd1")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4012015,
    )

    pre[callee] = Account(balance=10, nonce=0, storage={0x0: 0x1})
    callee_1 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0xC350,
                    address=0x1,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0xC350,
                    address=0x2,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0xC350,
                    address=0x3,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0xC350,
                    address=0x4,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0xC350,
                    address=0x5,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0xC350,
                    address=0x6,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0xC350,
                    address=0x7,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0xC350,
                    address=0x8,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.GAS)
            + Op.SSTORE(key=0x2, value=Op.GAS)
            + Op.SSTORE(key=0x3, value=Op.GAS)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x10ef6d6218ada53728683cec4d5160c8c72159bd"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.DELEGATECALL(
                    gas=0xC350,
                    address=0x1,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.DELEGATECALL(
                    gas=0xC350,
                    address=0x2,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.DELEGATECALL(
                    gas=0xC350,
                    address=0x3,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.DELEGATECALL(
                    gas=0xC350,
                    address=0x4,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.DELEGATECALL(
                    gas=0xC350,
                    address=0x5,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.DELEGATECALL(
                    gas=0xC350,
                    address=0x6,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.DELEGATECALL(
                    gas=0xC350,
                    address=0x7,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.DELEGATECALL(
                    gas=0xC350,
                    address=0x8,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.GAS)
            + Op.SSTORE(key=0x2, value=Op.GAS)
            + Op.SSTORE(key=0x3, value=Op.GAS)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x31f52a66cf9d94c60f089a2ca9c4e784261c57fa"),  # noqa: E501
    )
    pre[callee_3] = Account(balance=10, nonce=0, storage={0x0: 0x1})
    pre[callee_4] = Account(balance=10, nonce=0, storage={0x0: 0x1})
    pre[callee_5] = Account(balance=10, nonce=0, storage={0x0: 0x1})
    pre[callee_6] = Account(balance=10, nonce=0, storage={0x0: 0x1})
    callee_7 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=0xC350,
                    address=0x1,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.CALL(
                    gas=0xC350,
                    address=0x2,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.CALL(
                    gas=0xC350,
                    address=0x3,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.CALL(
                    gas=0xC350,
                    address=0x4,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.CALL(
                    gas=0xC350,
                    address=0x5,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.CALL(
                    gas=0xC350,
                    address=0x6,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.CALL(
                    gas=0xC350,
                    address=0x7,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.CALL(
                    gas=0xC350,
                    address=0x8,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.GAS)
            + Op.SSTORE(key=0x2, value=Op.GAS)
            + Op.SSTORE(key=0x3, value=Op.GAS)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x87aaeb9e422487283b0b008ef445e32acb9dd1ae"),  # noqa: E501
    )
    pre[callee_8] = Account(balance=10, nonce=0, storage={0x0: 0x1})
    pre[callee_9] = Account(balance=10, nonce=0, storage={0x0: 0x1})
    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=1)
    pre[callee_10] = Account(balance=10, nonce=0, storage={0x0: 0x1})
    callee_11 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALLCODE(
                    gas=0xC350,
                    address=0x1,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=0xC350,
                    address=0x2,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=0xC350,
                    address=0x3,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=0xC350,
                    address=0x4,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=0xC350,
                    address=0x5,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=0xC350,
                    address=0x6,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=0xC350,
                    address=0x7,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=0xC350,
                    address=0x8,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.GAS)
            + Op.SSTORE(key=0x2, value=Op.GAS)
            + Op.SSTORE(key=0x3, value=Op.GAS)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xde1200b7ecaea2d15b57d0f331ad5ade8e924255"),  # noqa: E501
    )
    # Source: LLL
    # {  (CALLCODE (GAS) (CALLDATALOAD 0) 0 0 0 0 0) }
    contract = pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xe7c596de24ccc387daa5c017066aeb25ea8d2f3f"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(storage={0: 1}),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000600060006000600161c350fa506000600060006000600261c350fa506000600060006000600361c350fa506000600060006000600461c350fa506000600060006000600561c350fa506000600060006000600661c350fa506000600060006000600761c350fa506000600060006000600861c350fa505a6001555a6002555a60035500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6000600060006000600161c350f4506000600060006000600261c350f4506000600060006000600361c350f4506000600060006000600461c350f4506000600060006000600561c350f4506000600060006000600661c350f4506000600060006000600761c350f4506000600060006000600861c350f4505a6001555a6002555a60035500"  # noqa: E501
                    )
                ),
                callee_3: Account(storage={0: 1}),
                callee_4: Account(storage={0: 1}),
                callee_5: Account(storage={0: 1}),
                callee_6: Account(storage={0: 1}),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006000600060006000600161c350f15060006000600060006000600261c350f15060006000600060006000600361c350f15060006000600060006000600461c350f15060006000600060006000600561c350f15060006000600060006000600661c350f15060006000600060006000600761c350f15060006000600060006000600861c350f1505a6001555a6002555a60035500"  # noqa: E501
                    )
                ),
                callee_8: Account(storage={0: 1}),
                callee_9: Account(storage={0: 1}),
                callee_10: Account(storage={0: 1}),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60006000600060006000600161c350f25060006000600060006000600261c350f25060006000600060006000600361c350f25060006000600060006000600461c350f25060006000600060006000600561c350f25060006000600060006000600661c350f25060006000600060006000600761c350f25060006000600060006000600861c350f2505a6001555a6002555a60035500"  # noqa: E501
                    )
                ),
                contract: Account(
                    code=bytes.fromhex("600060006000600060006000355af200")
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(storage={0: 1}),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000600060006000600161c350fa506000600060006000600261c350fa506000600060006000600361c350fa506000600060006000600461c350fa506000600060006000600561c350fa506000600060006000600661c350fa506000600060006000600761c350fa506000600060006000600861c350fa505a6001555a6002555a60035500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6000600060006000600161c350f4506000600060006000600261c350f4506000600060006000600361c350f4506000600060006000600461c350f4506000600060006000600561c350f4506000600060006000600661c350f4506000600060006000600761c350f4506000600060006000600861c350f4505a6001555a6002555a60035500"  # noqa: E501
                    )
                ),
                callee_3: Account(storage={0: 1}),
                callee_4: Account(storage={0: 1}),
                callee_5: Account(storage={0: 1}),
                callee_6: Account(storage={0: 1}),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006000600060006000600161c350f15060006000600060006000600261c350f15060006000600060006000600361c350f15060006000600060006000600461c350f15060006000600060006000600561c350f15060006000600060006000600661c350f15060006000600060006000600761c350f15060006000600060006000600861c350f1505a6001555a6002555a60035500"  # noqa: E501
                    )
                ),
                callee_8: Account(storage={0: 1}),
                callee_9: Account(storage={0: 1}),
                callee_10: Account(storage={0: 1}),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60006000600060006000600161c350f25060006000600060006000600261c350f25060006000600060006000600361c350f25060006000600060006000600461c350f25060006000600060006000600561c350f25060006000600060006000600661c350f25060006000600060006000600761c350f25060006000600060006000600861c350f2505a6001555a6002555a60035500"  # noqa: E501
                    )
                ),
                contract: Account(
                    code=bytes.fromhex("600060006000600060006000355af200")
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(storage={0: 1}),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000600060006000600161c350fa506000600060006000600261c350fa506000600060006000600361c350fa506000600060006000600461c350fa506000600060006000600561c350fa506000600060006000600661c350fa506000600060006000600761c350fa506000600060006000600861c350fa505a6001555a6002555a60035500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6000600060006000600161c350f4506000600060006000600261c350f4506000600060006000600361c350f4506000600060006000600461c350f4506000600060006000600561c350f4506000600060006000600661c350f4506000600060006000600761c350f4506000600060006000600861c350f4505a6001555a6002555a60035500"  # noqa: E501
                    )
                ),
                callee_3: Account(storage={0: 1}),
                callee_4: Account(storage={0: 1}),
                callee_5: Account(storage={0: 1}),
                callee_6: Account(storage={0: 1}),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006000600060006000600161c350f15060006000600060006000600261c350f15060006000600060006000600361c350f15060006000600060006000600461c350f15060006000600060006000600561c350f15060006000600060006000600661c350f15060006000600060006000600761c350f15060006000600060006000600861c350f1505a6001555a6002555a60035500"  # noqa: E501
                    )
                ),
                callee_8: Account(storage={0: 1}),
                callee_9: Account(storage={0: 1}),
                callee_10: Account(storage={0: 1}),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60006000600060006000600161c350f25060006000600060006000600261c350f25060006000600060006000600361c350f25060006000600060006000600461c350f25060006000600060006000600561c350f25060006000600060006000600661c350f25060006000600060006000600761c350f25060006000600060006000600861c350f2505a6001555a6002555a60035500"  # noqa: E501
                    )
                ),
                contract: Account(
                    code=bytes.fromhex("600060006000600060006000355af200")
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(storage={0: 1}),
                callee_1: Account(
                    code=bytes.fromhex(
                        "6000600060006000600161c350fa506000600060006000600261c350fa506000600060006000600361c350fa506000600060006000600461c350fa506000600060006000600561c350fa506000600060006000600661c350fa506000600060006000600761c350fa506000600060006000600861c350fa505a6001555a6002555a60035500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6000600060006000600161c350f4506000600060006000600261c350f4506000600060006000600361c350f4506000600060006000600461c350f4506000600060006000600561c350f4506000600060006000600661c350f4506000600060006000600761c350f4506000600060006000600861c350f4505a6001555a6002555a60035500"  # noqa: E501
                    )
                ),
                callee_3: Account(storage={0: 1}),
                callee_4: Account(storage={0: 1}),
                callee_5: Account(storage={0: 1}),
                callee_6: Account(storage={0: 1}),
                callee_7: Account(
                    code=bytes.fromhex(
                        "60006000600060006000600161c350f15060006000600060006000600261c350f15060006000600060006000600361c350f15060006000600060006000600461c350f15060006000600060006000600561c350f15060006000600060006000600661c350f15060006000600060006000600761c350f15060006000600060006000600861c350f1505a6001555a6002555a60035500"  # noqa: E501
                    )
                ),
                callee_8: Account(storage={0: 1}),
                callee_9: Account(storage={0: 1}),
                callee_10: Account(storage={0: 1}),
                callee_11: Account(
                    code=bytes.fromhex(
                        "60006000600060006000600161c350f25060006000600060006000600261c350f25060006000600060006000600361c350f25060006000600060006000600461c350f25060006000600060006000600561c350f25060006000600060006000600661c350f25060006000600060006000600761c350f25060006000600060006000600861c350f2505a6001555a6002555a60035500"  # noqa: E501
                    )
                ),
                contract: Account(
                    code=bytes.fromhex("600060006000600060006000355af200")
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
        nonce=1,
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
