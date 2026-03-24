"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest
RevertPrecompiledTouch_noncestorageFiller.json
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
    [
        "tests/static/state_tests/stRevertTest/RevertPrecompiledTouch_noncestorageFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "00000000000000000000000087aaeb9e422487283b0b008ef445e32acb9dd1ae",
        "00000000000000000000000031f52a66cf9d94c60f089a2ca9c4e784261c57fa",
        "000000000000000000000000de1200b7ecaea2d15b57d0f331ad5ade8e924255",
        "00000000000000000000000010ef6d6218ada53728683cec4d5160c8c72159bd",
    ],
    ids=["case0", "case1", "case2", "case3"],
)
@pytest.mark.pre_alloc_mutable
def test_revert_precompiled_touch_noncestorage(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x68795c4aa09d6f4ed3e5deddf8c2ad3049a601da")
    sender = EOA(
        key=0x0FF8D58222F34F6890DDAA468C023B77D6691ED7D3C4DCDDAE38336212FAF54B
    )
    callee = Address("0x0d6d2da01a9da2c336e2affe3e6a9d0787069b56")
    callee_1 = Address("0x0e145edea519e730a2c24124733e22e8b8de1202")
    callee_3 = Address("0x1e28db5341d617cce6178f0bbccb352c51c5909d")
    callee_6 = Address("0x9bce9e56a0a95f42d0b6a7b550e26604d7c5299f")
    callee_7 = Address("0xae321ab38d9488985a884ed293f2c1466d2c806b")
    callee_8 = Address("0xb0a7b7b80bc0f95f8890e6e2070ddc906bbfdbcd")
    callee_10 = Address("0xe2041123687b446e6f4ba274bfed4ce0206d4c8e")
    callee_11 = Address("0xf6165bb84beb5028557005861faa9b085c1381d9")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4012015,
    )

    pre[callee] = Account(balance=0, nonce=1, storage={0x0: 0x1})
    pre[callee_1] = Account(balance=0, nonce=1, storage={0x0: 0x1})
    pre.deploy_contract(
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
    pre[callee_3] = Account(balance=0, nonce=1, storage={0x0: 0x1})
    pre.deploy_contract(
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
    pre.deploy_contract(
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
    pre[callee_6] = Account(balance=0, nonce=1, storage={0x0: 0x1})
    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=1)
    pre[callee_7] = Account(balance=0, nonce=1, storage={0x0: 0x1})
    pre[callee_8] = Account(balance=0, nonce=1, storage={0x0: 0x1})
    pre.deploy_contract(
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
    pre[callee_10] = Account(balance=0, nonce=1, storage={0x0: 0x1})
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
    pre[callee_11] = Account(balance=0, nonce=1, storage={0x0: 0x1})

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=100000,
        nonce=1,
    )

    post = {
        callee: Account(storage={0: 1}),
        callee_1: Account(storage={0: 1}),
        callee_3: Account(storage={0: 1}),
        callee_6: Account(storage={0: 1}),
        callee_7: Account(storage={0: 1}),
        callee_8: Account(storage={0: 1}),
        callee_10: Account(storage={0: 1}),
        callee_11: Account(storage={0: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
