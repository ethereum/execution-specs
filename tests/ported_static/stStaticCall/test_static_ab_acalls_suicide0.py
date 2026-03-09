"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_ABAcallsSuicide0Filler.json
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
        "tests/static/state_tests/stStaticCall/static_ABAcallsSuicide0Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "000000000000000000000000195198c66c5e31767d41365ff8003c5fe4387110",
            {
                Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"): Account(
                    storage={0: 1, 1: 1}
                )
            },
        ),
        (
            "00000000000000000000000015631f76b02193e5716cbd4b4d696f2f7a39f0a4",
            {
                Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"): Account(
                    storage={0: 1, 1: 1}
                )
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_ab_acalls_suicide0(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
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
        gas_limit=100000000,
    )

    pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=Op.PC,
                value=Op.STATICCALL(
                    gas=0x186A0,
                    address=0x644AC2B24A9316ED4C55001E5EDA02D77F729C7B,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SELFDESTRUCT(
                address=0xC20B4779ED25A1CCF1848F1CBCC84433FCB9D083
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x15631f76b02193e5716cbd4b4d696f2f7a39f0a4"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=Op.PC,
                value=Op.STATICCALL(
                    gas=0x186A0,
                    address=0xC20B4779ED25A1CCF1848F1CBCC84433FCB9D083,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SELFDESTRUCT(
                address=0xC20B4779ED25A1CCF1848F1CBCC84433FCB9D083
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x195198c66c5e31767d41365ff8003c5fe4387110"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=Op.PC,
                value=Op.ADD(
                    0x1,
                    Op.STATICCALL(
                        gas=0xC350,
                        address=0x15631F76B02193E5716CBD4B4D696F2F7A39F0A4,
                        args_offset=0x0,
                        args_size=0x0,
                        ret_offset=0x0,
                        ret_size=0x0,
                    ),
                ),
            )
            + Op.STOP
        ),
        balance=23,
        nonce=0,
        address=Address("0x644ac2b24a9316ed4c55001e5eda02d77f729c7b"),  # noqa: E501
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
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=Op.PC,
                value=Op.ADD(
                    0x1,
                    Op.STATICCALL(
                        gas=0xC350,
                        address=0x195198C66C5E31767D41365FF8003C5FE4387110,
                        args_offset=0x0,
                        args_size=0x0,
                        ret_offset=0x0,
                        ret_size=0x0,
                    ),
                ),
            )
            + Op.STOP
        ),
        balance=23,
        nonce=0,
        address=Address("0xc20b4779ed25a1ccf1848f1cbcc84433fcb9d083"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=10000000,
        value=100000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
