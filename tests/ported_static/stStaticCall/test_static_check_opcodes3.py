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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stStaticCall/static_CheckOpcodes3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_value, expected_post",
    [
        (
            "000000000000000000000000f697c2d8963df21523b18e96caaf6c7703a1882e",
            0,
            {
                Address("0x50f628d871a69f2db31e98d7fbf8ae6f1fc0d55c"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "000000000000000000000000f697c2d8963df21523b18e96caaf6c7703a1882e",
            100,
            {
                Address("0x50f628d871a69f2db31e98d7fbf8ae6f1fc0d55c"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "0000000000000000000000009b68a6b37af295c7fd23aa2269db8c875c2b86b4",
            0,
            {},
        ),
        (
            "0000000000000000000000009b68a6b37af295c7fd23aa2269db8c875c2b86b4",
            100,
            {},
        ),
        (
            "000000000000000000000000ba044a82b25080bc96678b9fa77678e014605c48",
            0,
            {
                Address("0x50f628d871a69f2db31e98d7fbf8ae6f1fc0d55c"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "000000000000000000000000ba044a82b25080bc96678b9fa77678e014605c48",
            100,
            {
                Address("0x50f628d871a69f2db31e98d7fbf8ae6f1fc0d55c"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "000000000000000000000000e541572ce4b4ccbb2b92aab0fb852f018d51c512",
            0,
            {
                Address("0x50f628d871a69f2db31e98d7fbf8ae6f1fc0d55c"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "000000000000000000000000e541572ce4b4ccbb2b92aab0fb852f018d51c512",
            100,
            {
                Address("0x50f628d871a69f2db31e98d7fbf8ae6f1fc0d55c"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "0000000000000000000000008113f9fc0868700534ecbecf1120a812cb1af0ac",
            0,
            {
                Address("0x50f628d871a69f2db31e98d7fbf8ae6f1fc0d55c"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "0000000000000000000000008113f9fc0868700534ecbecf1120a812cb1af0ac",
            100,
            {
                Address("0x50f628d871a69f2db31e98d7fbf8ae6f1fc0d55c"): Account(
                    storage={1: 1}
                )
            },
        ),
    ],
    ids=[
        "case0",
        "case1",
        "case2",
        "case3",
        "case4",
        "case5",
        "case6",
        "case7",
        "case8",
        "case9",
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_check_opcodes3(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_value: int,
    expected_post: dict,
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

    pre.deploy_contract(
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
    pre.deploy_contract(
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
    pre.deploy_contract(
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
    pre.deploy_contract(
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
    pre.deploy_contract(
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
    pre.deploy_contract(
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
    pre.deploy_contract(
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
    pre.deploy_contract(
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
    pre.deploy_contract(
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
    pre.deploy_contract(
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
    pre.deploy_contract(
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

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=335000,
        value=tx_value,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
