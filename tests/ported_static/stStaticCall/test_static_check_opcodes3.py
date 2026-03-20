"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_CheckOpcodes3Filler.json
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
    "000000000000000000000000f697c2d8963df21523b18e96caaf6c7703a1882e",
    "0000000000000000000000009b68a6b37af295c7fd23aa2269db8c875c2b86b4",
    "000000000000000000000000ba044a82b25080bc96678b9fa77678e014605c48",
    "000000000000000000000000e541572ce4b4ccbb2b92aab0fb852f018d51c512",
    "0000000000000000000000008113f9fc0868700534ecbecf1120a812cb1af0ac",
]

TX_GAS = [335000]

TX_VALUE = [0, 100]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stStaticCall/static_CheckOpcodes3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(0, 0, 1, id="case1"),
        pytest.param(1, 0, 0, id="case2"),
        pytest.param(1, 0, 1, id="case3"),
        pytest.param(2, 0, 0, id="case4"),
        pytest.param(2, 0, 1, id="case5"),
        pytest.param(3, 0, 0, id="case6"),
        pytest.param(3, 0, 1, id="case7"),
        pytest.param(4, 0, 0, id="case8"),
        pytest.param(4, 0, 1, id="case9"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_check_opcodes3(
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
            Op.MSTORE(
                offset=0x0,
                value=Op.STATICCALL(
                    gas=0x186A0,
                    address=Op.CALLDATALOAD(offset=0x0),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPI(pc=0x24, condition=Op.EQ(0x1, Op.MLOAD(offset=0x0)))
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x2A)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x22,
                condition=Op.EQ(
                    0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                    Op.ORIGIN,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x28)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x4B,
                condition=Op.EQ(
                    0x8113F9FC0868700534ECBECF1120A812CB1AF0AC,
                    Op.CALLER,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x51)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x74,
                condition=Op.EQ(
                    0x4AF0C90F8F7B7834E7E7BD57DDA960412F9650F9,
                    Op.ADDRESS,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x7A)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x0, Op.CALLVALUE))
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x90)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x4af0c90f8f7b7834e7e7bd57dda960412f9650f9"),  # noqa: E501
    )
    # Source: LLL
    # { [[1]] (STATICCALL 100000 (CALLDATALOAD 0) 0 0 0 0) }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x1,
                value=Op.STATICCALL(
                    gas=0x186A0,
                    address=Op.CALLDATALOAD(offset=0x0),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x50f628d871a69f2db31e98d7fbf8ae6f1fc0d55c"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x22,
                condition=Op.EQ(
                    0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                    Op.ORIGIN,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x28)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x4B,
                condition=Op.EQ(
                    0xE541572CE4B4CCBB2B92AAB0FB852F018D51C512,
                    Op.CALLER,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x51)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x74,
                condition=Op.EQ(
                    0x6D797B6A2C5F22885C4068990F19AE845D698A79,
                    Op.ADDRESS,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x7A)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x0, Op.CALLVALUE))
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x90)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x6d797b6a2c5f22885c4068990f19ae845d698a79"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x4AF0C90F8F7B7834E7E7BD57DDA960412F9650F9,
            )
            + Op.MSTORE(
                offset=0x0,
                value=Op.DELEGATECALL(
                    gas=0x186A0,
                    address=0x2E5DC1C94AF89D7C115126FCEBAD7A5C50F5FE35,
                    args_offset=0x0,
                    args_size=0x20,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPI(pc=0x4E, condition=Op.EQ(0x1, Op.MLOAD(offset=0x0)))
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x54)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=10,
        nonce=0,
        address=Address("0x8113f9fc0868700534ecbecf1120a812cb1af0ac"),  # noqa: E501
    )
    callee_4 = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0xA131950507C8977B0DE1790C8E76A1A28DD92805,
            )
            + Op.MSTORE(
                offset=0x0,
                value=Op.CALL(
                    gas=0x186A0,
                    address=0x2E5DC1C94AF89D7C115126FCEBAD7A5C50F5FE35,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x20,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.MSTORE(offset=0x2, value=0x1)
            + Op.STOP
        ),
        balance=10,
        nonce=0,
        address=Address("0x9b68a6b37af295c7fd23aa2269db8c875c2b86b4"),  # noqa: E501
    )
    callee_5 = pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x22,
                condition=Op.EQ(
                    0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                    Op.ORIGIN,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x28)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x4B,
                condition=Op.EQ(
                    0x2E5DC1C94AF89D7C115126FCEBAD7A5C50F5FE35,
                    Op.CALLER,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x51)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x74,
                condition=Op.EQ(
                    0xA131950507C8977B0DE1790C8E76A1A28DD92805,
                    Op.ADDRESS,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x7A)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x0, Op.CALLVALUE))
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x90)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xa131950507c8977b0de1790c8e76a1a28dd92805"),  # noqa: E501
    )
    callee_6 = pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x22,
                condition=Op.EQ(
                    0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                    Op.ORIGIN,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x28)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x4B,
                condition=Op.EQ(
                    0xBA044A82B25080BC96678B9FA77678E014605C48,
                    Op.CALLER,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x51)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x74,
                condition=Op.EQ(
                    0xB93CF5121157D61AB42345F5A5E9815B19CEC2CC,
                    Op.ADDRESS,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x7A)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x0, Op.CALLVALUE))
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x90)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xb93cf5121157d61ab42345f5a5e9815b19cec2cc"),  # noqa: E501
    )
    callee_7 = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x20,
                value=0xB93CF5121157D61AB42345F5A5E9815B19CEC2CC,
            )
            + Op.MSTORE(
                offset=0x0,
                value=Op.CALLCODE(
                    gas=0x186A0,
                    address=0x2E5DC1C94AF89D7C115126FCEBAD7A5C50F5FE35,
                    value=0x0,
                    args_offset=0x20,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPI(pc=0x50, condition=Op.EQ(0x1, Op.MLOAD(offset=0x0)))
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x56)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=10,
        nonce=0,
        address=Address("0xba044a82b25080bc96678b9fa77678e014605c48"),  # noqa: E501
    )
    callee_8 = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x6D797B6A2C5F22885C4068990F19AE845D698A79,
            )
            + Op.MSTORE(
                offset=0x0,
                value=Op.CALLCODE(
                    gas=0x186A0,
                    address=0x2E5DC1C94AF89D7C115126FCEBAD7A5C50F5FE35,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x20,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPI(pc=0x50, condition=Op.EQ(0x1, Op.MLOAD(offset=0x0)))
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x56)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=10,
        nonce=0,
        address=Address("0xe541572ce4b4ccbb2b92aab0fb852f018d51c512"),  # noqa: E501
    )
    callee_9 = pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x22,
                condition=Op.EQ(
                    0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                    Op.ORIGIN,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x28)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x4B,
                condition=Op.EQ(
                    0x9B68A6B37AF295C7FD23AA2269DB8C875C2B86B4,
                    Op.CALLER,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x51)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x74,
                condition=Op.EQ(
                    0xEF6A70E5546CA5339758B2F3B819780625C233C3,
                    Op.ADDRESS,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x7A)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x1, Op.CALLVALUE))
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x90)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xef6a70e5546ca5339758b2f3b819780625c233c3"),  # noqa: E501
    )
    callee_10 = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0xA131950507C8977B0DE1790C8E76A1A28DD92805,
            )
            + Op.MSTORE(
                offset=0x0,
                value=Op.CALL(
                    gas=0x186A0,
                    address=0x2E5DC1C94AF89D7C115126FCEBAD7A5C50F5FE35,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x20,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPI(pc=0x50, condition=Op.EQ(0x1, Op.MLOAD(offset=0x0)))
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x56)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=10,
        nonce=0,
        address=Address("0xf697c2d8963df21523b18e96caaf6c7703a1882e"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa6000526000516001146024576002600155602a565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33738113f9fc0868700534ecbecf1120a812cb1af0ac14604b5760026001556051565b60016001525b30734af0c90f8f7b7834e7e7bd57dda960412f9650f9146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa60015500"
                    ),
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373e541572ce4b4ccbb2b92aab0fb852f018d51c51214604b5760026001556051565b60016001525b30736d797b6a2c5f22885c4068990f19ae845d698a79146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "734af0c90f8f7b7834e7e7bd57dda960412f9650f96000526000600060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f4600052600051600114604e5760026001556054565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f16000526001600152600160025200"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33732e5dc1c94af89d7c115126fcebad7a5c50f5fe3514604b5760026001556051565b60016001525b3073a131950507c8977b0de1790c8e76a1a28dd92805146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373ba044a82b25080bc96678b9fa77678e014605c4814604b5760026001556051565b60016001525b3073b93cf5121157d61ab42345f5a5e9815b19cec2cc146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "73b93cf5121157d61ab42345f5a5e9815b19cec2cc60205260006000604060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "736d797b6a2c5f22885c4068990f19ae845d698a7960005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33739b68a6b37af295c7fd23aa2269db8c875c2b86b414604b5760026001556051565b60016001525b3073ef6a70e5546ca5339758b2f3b819780625c233c3146074576002600155607a565b60016001525b34600114608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f160005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa6000526000516001146024576002600155602a565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33738113f9fc0868700534ecbecf1120a812cb1af0ac14604b5760026001556051565b60016001525b30734af0c90f8f7b7834e7e7bd57dda960412f9650f9146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa60015500"
                    ),
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373e541572ce4b4ccbb2b92aab0fb852f018d51c51214604b5760026001556051565b60016001525b30736d797b6a2c5f22885c4068990f19ae845d698a79146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "734af0c90f8f7b7834e7e7bd57dda960412f9650f96000526000600060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f4600052600051600114604e5760026001556054565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f16000526001600152600160025200"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33732e5dc1c94af89d7c115126fcebad7a5c50f5fe3514604b5760026001556051565b60016001525b3073a131950507c8977b0de1790c8e76a1a28dd92805146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373ba044a82b25080bc96678b9fa77678e014605c4814604b5760026001556051565b60016001525b3073b93cf5121157d61ab42345f5a5e9815b19cec2cc146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "73b93cf5121157d61ab42345f5a5e9815b19cec2cc60205260006000604060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "736d797b6a2c5f22885c4068990f19ae845d698a7960005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33739b68a6b37af295c7fd23aa2269db8c875c2b86b414604b5760026001556051565b60016001525b3073ef6a70e5546ca5339758b2f3b819780625c233c3146074576002600155607a565b60016001525b34600114608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f160005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
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
                        "6000600060006000600035620186a0fa6000526000516001146024576002600155602a565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33738113f9fc0868700534ecbecf1120a812cb1af0ac14604b5760026001556051565b60016001525b30734af0c90f8f7b7834e7e7bd57dda960412f9650f9146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa60015500"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373e541572ce4b4ccbb2b92aab0fb852f018d51c51214604b5760026001556051565b60016001525b30736d797b6a2c5f22885c4068990f19ae845d698a79146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "734af0c90f8f7b7834e7e7bd57dda960412f9650f96000526000600060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f4600052600051600114604e5760026001556054565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f16000526001600152600160025200"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33732e5dc1c94af89d7c115126fcebad7a5c50f5fe3514604b5760026001556051565b60016001525b3073a131950507c8977b0de1790c8e76a1a28dd92805146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373ba044a82b25080bc96678b9fa77678e014605c4814604b5760026001556051565b60016001525b3073b93cf5121157d61ab42345f5a5e9815b19cec2cc146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "73b93cf5121157d61ab42345f5a5e9815b19cec2cc60205260006000604060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "736d797b6a2c5f22885c4068990f19ae845d698a7960005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33739b68a6b37af295c7fd23aa2269db8c875c2b86b414604b5760026001556051565b60016001525b3073ef6a70e5546ca5339758b2f3b819780625c233c3146074576002600155607a565b60016001525b34600114608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f160005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa6000526000516001146024576002600155602a565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33738113f9fc0868700534ecbecf1120a812cb1af0ac14604b5760026001556051565b60016001525b30734af0c90f8f7b7834e7e7bd57dda960412f9650f9146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa60015500"
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373e541572ce4b4ccbb2b92aab0fb852f018d51c51214604b5760026001556051565b60016001525b30736d797b6a2c5f22885c4068990f19ae845d698a79146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "734af0c90f8f7b7834e7e7bd57dda960412f9650f96000526000600060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f4600052600051600114604e5760026001556054565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f16000526001600152600160025200"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33732e5dc1c94af89d7c115126fcebad7a5c50f5fe3514604b5760026001556051565b60016001525b3073a131950507c8977b0de1790c8e76a1a28dd92805146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373ba044a82b25080bc96678b9fa77678e014605c4814604b5760026001556051565b60016001525b3073b93cf5121157d61ab42345f5a5e9815b19cec2cc146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "73b93cf5121157d61ab42345f5a5e9815b19cec2cc60205260006000604060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "736d797b6a2c5f22885c4068990f19ae845d698a7960005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33739b68a6b37af295c7fd23aa2269db8c875c2b86b414604b5760026001556051565b60016001525b3073ef6a70e5546ca5339758b2f3b819780625c233c3146074576002600155607a565b60016001525b34600114608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f160005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa6000526000516001146024576002600155602a565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33738113f9fc0868700534ecbecf1120a812cb1af0ac14604b5760026001556051565b60016001525b30734af0c90f8f7b7834e7e7bd57dda960412f9650f9146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa60015500"
                    ),
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373e541572ce4b4ccbb2b92aab0fb852f018d51c51214604b5760026001556051565b60016001525b30736d797b6a2c5f22885c4068990f19ae845d698a79146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "734af0c90f8f7b7834e7e7bd57dda960412f9650f96000526000600060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f4600052600051600114604e5760026001556054565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f16000526001600152600160025200"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33732e5dc1c94af89d7c115126fcebad7a5c50f5fe3514604b5760026001556051565b60016001525b3073a131950507c8977b0de1790c8e76a1a28dd92805146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373ba044a82b25080bc96678b9fa77678e014605c4814604b5760026001556051565b60016001525b3073b93cf5121157d61ab42345f5a5e9815b19cec2cc146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "73b93cf5121157d61ab42345f5a5e9815b19cec2cc60205260006000604060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "736d797b6a2c5f22885c4068990f19ae845d698a7960005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33739b68a6b37af295c7fd23aa2269db8c875c2b86b414604b5760026001556051565b60016001525b3073ef6a70e5546ca5339758b2f3b819780625c233c3146074576002600155607a565b60016001525b34600114608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f160005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa6000526000516001146024576002600155602a565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33738113f9fc0868700534ecbecf1120a812cb1af0ac14604b5760026001556051565b60016001525b30734af0c90f8f7b7834e7e7bd57dda960412f9650f9146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa60015500"
                    ),
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373e541572ce4b4ccbb2b92aab0fb852f018d51c51214604b5760026001556051565b60016001525b30736d797b6a2c5f22885c4068990f19ae845d698a79146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "734af0c90f8f7b7834e7e7bd57dda960412f9650f96000526000600060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f4600052600051600114604e5760026001556054565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f16000526001600152600160025200"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33732e5dc1c94af89d7c115126fcebad7a5c50f5fe3514604b5760026001556051565b60016001525b3073a131950507c8977b0de1790c8e76a1a28dd92805146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373ba044a82b25080bc96678b9fa77678e014605c4814604b5760026001556051565b60016001525b3073b93cf5121157d61ab42345f5a5e9815b19cec2cc146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "73b93cf5121157d61ab42345f5a5e9815b19cec2cc60205260006000604060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "736d797b6a2c5f22885c4068990f19ae845d698a7960005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33739b68a6b37af295c7fd23aa2269db8c875c2b86b414604b5760026001556051565b60016001525b3073ef6a70e5546ca5339758b2f3b819780625c233c3146074576002600155607a565b60016001525b34600114608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f160005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa6000526000516001146024576002600155602a565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33738113f9fc0868700534ecbecf1120a812cb1af0ac14604b5760026001556051565b60016001525b30734af0c90f8f7b7834e7e7bd57dda960412f9650f9146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa60015500"
                    ),
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373e541572ce4b4ccbb2b92aab0fb852f018d51c51214604b5760026001556051565b60016001525b30736d797b6a2c5f22885c4068990f19ae845d698a79146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "734af0c90f8f7b7834e7e7bd57dda960412f9650f96000526000600060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f4600052600051600114604e5760026001556054565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f16000526001600152600160025200"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33732e5dc1c94af89d7c115126fcebad7a5c50f5fe3514604b5760026001556051565b60016001525b3073a131950507c8977b0de1790c8e76a1a28dd92805146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373ba044a82b25080bc96678b9fa77678e014605c4814604b5760026001556051565b60016001525b3073b93cf5121157d61ab42345f5a5e9815b19cec2cc146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "73b93cf5121157d61ab42345f5a5e9815b19cec2cc60205260006000604060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "736d797b6a2c5f22885c4068990f19ae845d698a7960005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33739b68a6b37af295c7fd23aa2269db8c875c2b86b414604b5760026001556051565b60016001525b3073ef6a70e5546ca5339758b2f3b819780625c233c3146074576002600155607a565b60016001525b34600114608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f160005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa6000526000516001146024576002600155602a565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33738113f9fc0868700534ecbecf1120a812cb1af0ac14604b5760026001556051565b60016001525b30734af0c90f8f7b7834e7e7bd57dda960412f9650f9146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa60015500"
                    ),
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373e541572ce4b4ccbb2b92aab0fb852f018d51c51214604b5760026001556051565b60016001525b30736d797b6a2c5f22885c4068990f19ae845d698a79146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "734af0c90f8f7b7834e7e7bd57dda960412f9650f96000526000600060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f4600052600051600114604e5760026001556054565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f16000526001600152600160025200"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33732e5dc1c94af89d7c115126fcebad7a5c50f5fe3514604b5760026001556051565b60016001525b3073a131950507c8977b0de1790c8e76a1a28dd92805146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373ba044a82b25080bc96678b9fa77678e014605c4814604b5760026001556051565b60016001525b3073b93cf5121157d61ab42345f5a5e9815b19cec2cc146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "73b93cf5121157d61ab42345f5a5e9815b19cec2cc60205260006000604060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "736d797b6a2c5f22885c4068990f19ae845d698a7960005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33739b68a6b37af295c7fd23aa2269db8c875c2b86b414604b5760026001556051565b60016001525b3073ef6a70e5546ca5339758b2f3b819780625c233c3146074576002600155607a565b60016001525b34600114608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f160005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa6000526000516001146024576002600155602a565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33738113f9fc0868700534ecbecf1120a812cb1af0ac14604b5760026001556051565b60016001525b30734af0c90f8f7b7834e7e7bd57dda960412f9650f9146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa60015500"
                    ),
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373e541572ce4b4ccbb2b92aab0fb852f018d51c51214604b5760026001556051565b60016001525b30736d797b6a2c5f22885c4068990f19ae845d698a79146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "734af0c90f8f7b7834e7e7bd57dda960412f9650f96000526000600060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f4600052600051600114604e5760026001556054565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f16000526001600152600160025200"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33732e5dc1c94af89d7c115126fcebad7a5c50f5fe3514604b5760026001556051565b60016001525b3073a131950507c8977b0de1790c8e76a1a28dd92805146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373ba044a82b25080bc96678b9fa77678e014605c4814604b5760026001556051565b60016001525b3073b93cf5121157d61ab42345f5a5e9815b19cec2cc146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "73b93cf5121157d61ab42345f5a5e9815b19cec2cc60205260006000604060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "736d797b6a2c5f22885c4068990f19ae845d698a7960005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33739b68a6b37af295c7fd23aa2269db8c875c2b86b414604b5760026001556051565b60016001525b3073ef6a70e5546ca5339758b2f3b819780625c233c3146074576002600155607a565b60016001525b34600114608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f160005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa6000526000516001146024576002600155602a565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33738113f9fc0868700534ecbecf1120a812cb1af0ac14604b5760026001556051565b60016001525b30734af0c90f8f7b7834e7e7bd57dda960412f9650f9146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={1: 1},
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa60015500"
                    ),
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373e541572ce4b4ccbb2b92aab0fb852f018d51c51214604b5760026001556051565b60016001525b30736d797b6a2c5f22885c4068990f19ae845d698a79146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "734af0c90f8f7b7834e7e7bd57dda960412f9650f96000526000600060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f4600052600051600114604e5760026001556054565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f16000526001600152600160025200"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33732e5dc1c94af89d7c115126fcebad7a5c50f5fe3514604b5760026001556051565b60016001525b3073a131950507c8977b0de1790c8e76a1a28dd92805146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_6: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b3373ba044a82b25080bc96678b9fa77678e014605c4814604b5760026001556051565b60016001525b3073b93cf5121157d61ab42345f5a5e9815b19cec2cc146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_7: Account(
                    code=bytes.fromhex(
                        "73b93cf5121157d61ab42345f5a5e9815b19cec2cc60205260006000604060206000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_8: Account(
                    code=bytes.fromhex(
                        "736d797b6a2c5f22885c4068990f19ae845d698a7960005260006000602060006001732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f260005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_9: Account(
                    code=bytes.fromhex(
                        "3273faa10b404ab607779993c016cd5da73ae1f29d7e1460225760026001556028565b60016001525b33739b68a6b37af295c7fd23aa2269db8c875c2b86b414604b5760026001556051565b60016001525b3073ef6a70e5546ca5339758b2f3b819780625c233c3146074576002600155607a565b60016001525b34600114608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_10: Account(
                    code=bytes.fromhex(
                        "73a131950507c8977b0de1790c8e76a1a28dd9280560005260006000602060006000732e5dc1c94af89d7c115126fcebad7a5c50f5fe35620186a0f160005260005160011460505760026001556056565b60016001525b00"  # noqa: E501
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
