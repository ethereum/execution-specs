"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callcodecallcallcode_ABCB_RECURSIVE2Filler.json
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
        "tests/static/state_tests/stStaticCall/static_callcodecallcallcode_ABCB_RECURSIVE2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_value, expected_post",
    [
        (
            "0000000000000000000000002733821fa13c4ead1c9631c76820333f42059b7c",
            0,
            {
                Address("0xba3c5101ad0b43de0f1853243eb3f9811eaee1e0"): Account(
                    storage={0: 1, 1: 1}
                )
            },
        ),
        (
            "0000000000000000000000002733821fa13c4ead1c9631c76820333f42059b7c",
            1,
            {
                Address("0xba3c5101ad0b43de0f1853243eb3f9811eaee1e0"): Account(
                    storage={0: 1, 1: 1}
                )
            },
        ),
        (
            "0000000000000000000000006acc177800643d95ab1daee1bd55cf99e3814e07",
            0,
            {
                Address("0xba3c5101ad0b43de0f1853243eb3f9811eaee1e0"): Account(
                    storage={0: 1, 1: 1}
                )
            },
        ),
        (
            "0000000000000000000000006acc177800643d95ab1daee1bd55cf99e3814e07",
            1,
            {
                Address("0xba3c5101ad0b43de0f1853243eb3f9811eaee1e0"): Account(
                    storage={0: 1, 1: 1}
                )
            },
        ),
    ],
    ids=["case0", "case1", "case2", "case3"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_callcodecallcallcode_abcb_recursive2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_value: int,
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
        gas_limit=3000000000,
    )

    pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=0x7A120,
                address=0x2733821FA13C4EAD1C9631C76820333F42059B7C,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        balance=0x2540BE400,
        nonce=0,
        address=Address("0x1a3c543695d7ca3a7d5522e9c7aabe5512571706"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=0xF4240,
                address=0x1A3C543695D7CA3A7D5522E9C7AABE5512571706,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        balance=0x2540BE400,
        nonce=0,
        address=Address("0x2733821fa13c4ead1c9631c76820333f42059b7c"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=0xF4240,
                address=0xB81EB378451B4361DF035AEA57913023DFFBF39A,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        balance=0x2540BE400,
        nonce=0,
        address=Address("0x6acc177800643d95ab1daee1bd55cf99e3814e07"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=0x7A120,
                address=0x6ACC177800643D95AB1DAEE1BD55CF99E3814E07,
                value=0x1,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        balance=0x2540BE400,
        nonce=0,
        address=Address("0xb81eb378451b4361df035aea57913023dffbf39a"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (CALLCODE 25000000 (CALLDATALOAD 0) (CALLVALUE) 0 64 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALLCODE(
                    gas=0x17D7840,
                    address=Op.CALLDATALOAD(offset=0x0),
                    value=Op.CALLVALUE,
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
        address=Address("0xba3c5101ad0b43de0f1853243eb3f9811eaee1e0"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=600000,
        value=tx_value,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
