"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_callcall_00Filler.json
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
    ["tests/static/state_tests/stStaticCall/static_callcall_00Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "0000000000000000000000002f9ec0afcb4edcd7d38c6a48f5e36038263ca3cd",
            {
                Address("0x2f9ec0afcb4edcd7d38c6a48f5e36038263ca3cd"): Account(
                    storage={0: 1}
                ),
                Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"): Account(
                    storage={0: 1, 1: 1}
                ),
            },
        ),
        (
            "000000000000000000000000bf23f3306533431b2ee5e4ca95e0a0834c090105",
            {
                Address("0xbf23f3306533431b2ee5e4ca95e0a0834c090105"): Account(
                    storage={0: 1}
                ),
                Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"): Account(
                    storage={0: 1, 1: 1}
                ),
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_callcall_00(
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
        gas_limit=30000000,
    )

    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x1)
            + Op.MSTORE(offset=0x20, value=Op.CALLER)
            + Op.MSTORE(offset=0x40, value=Op.CALLVALUE)
            + Op.MSTORE(offset=0x60, value=Op.ADDRESS)
            + Op.MSTORE(offset=0x80, value=Op.ORIGIN)
            + Op.MSTORE(offset=0xA0, value=Op.CALLDATASIZE)
            + Op.MSTORE(offset=0xC0, value=Op.CODESIZE)
            + Op.MSTORE(offset=0xE0, value=Op.GASPRICE)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x29736372c0fab51db4556614ef27d74a89acfe21"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0x55730,
                    address=0x620B442C84D5068E6B57D390A1AC99130205406E,
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
        address=Address("0x2f9ec0afcb4edcd7d38c6a48f5e36038263ca3cd"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x2, value=0x1)
            + Op.SSTORE(key=0x4, value=Op.CALLER)
            + Op.SSTORE(key=0x7, value=Op.CALLVALUE)
            + Op.SSTORE(key=0xE6, value=Op.ADDRESS)
            + Op.SSTORE(key=0xE8, value=Op.ORIGIN)
            + Op.SSTORE(key=0xEC, value=Op.CALLDATASIZE)
            + Op.SSTORE(key=0xEE, value=Op.CODESIZE)
            + Op.SSTORE(key=0xF0, value=Op.GASPRICE)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x33f368f0b54063613cf5944941e8e0e4eeb64697"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=0x3D090,
                address=0x33F368F0B54063613CF5944941E8E0E4EEB64697,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x620b442c84d5068e6b57d390a1ac99130205406e"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0x55730,
                    address=0xDCC76191E9F918ECFE9FBA5414884D5EE621AE00,
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
    pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=0x3D090,
                address=0x29736372C0FAB51DB4556614EF27D74A89ACFE21,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xdcc76191e9f918ecfe9fba5414884d5ee621ae00"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=3000000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
