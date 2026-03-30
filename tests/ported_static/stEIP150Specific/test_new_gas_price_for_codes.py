"""
Test_new_gas_price_for_codes.

Ported from:
state_tests/stEIP150Specific/NewGasPriceForCodesFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP150Specific/NewGasPriceForCodesFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_new_gas_price_for_codes(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_new_gas_price_for_codes."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
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

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: raw
    # 0x1122334455667788991011121314151617181920212223242526272829303132
    addr = pre.deploy_contract(  # noqa: F841
        code=bytes.fromhex(
            "1122334455667788991011121314151617181920212223242526272829303132"
        ),
        balance=111,
        nonce=0,
        address=Address(0xC572A70AFAAB9D01D0A2AFB855BFBAFB47C8211B),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 100 0x11) }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x64, value=0x11) + Op.STOP,
        nonce=0,
        address=Address(0xAD9D325B811CB0701839C07C6F139F3799476798),  # noqa: E501
    )
    # Source: lll
    # { [999] (GAS) (SSTORE 1 (EXTCODESIZE <contract:0x1000000000000000000000000000000000000010>)) (EXTCODECOPY <contract:0x1000000000000000000000000000000000000010> 0 0 20) (SSTORE 2 (MLOAD 0)) (SSTORE 4 (SLOAD 0)) (SSTORE 5 (CALL 30000 <contract:0x1000000000000000000000000000000000000011> 1 0 0 0 0)) (SSTORE 6 (CALLCODE 30000 <contract:0x1000000000000000000000000000000000000011> 1 0 0 0 0)) (SSTORE 7 (DELEGATECALL 30000 <contract:0x1000000000000000000000000000000000000011> 0 0 0 0)) (SSTORE 8 (CALL 30000 0x1000000000000000000000000000000000000013 0 0 0 0 0)) (SSTORE 3 (BALANCE <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b>)) (SSTORE 10 (SUB (MLOAD 999) (GAS))) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3E7, value=Op.GAS)
        + Op.SSTORE(
            key=0x1,
            value=Op.EXTCODESIZE(
                address=0xC572A70AFAAB9D01D0A2AFB855BFBAFB47C8211B
            ),
        )
        + Op.EXTCODECOPY(
            address=0xC572A70AFAAB9D01D0A2AFB855BFBAFB47C8211B,
            dest_offset=0x0,
            offset=0x0,
            size=0x14,
        )
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x4, value=Op.SLOAD(key=0x0))
        + Op.SSTORE(
            key=0x5,
            value=Op.CALL(
                gas=0x7530,
                address=0xAD9D325B811CB0701839C07C6F139F3799476798,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x6,
            value=Op.CALLCODE(
                gas=0x7530,
                address=0xAD9D325B811CB0701839C07C6F139F3799476798,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x7,
            value=Op.DELEGATECALL(
                gas=0x7530,
                address=0xAD9D325B811CB0701839C07C6F139F3799476798,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x8,
            value=Op.CALL(
                gas=0x7530,
                address=0x1000000000000000000000000000000000000013,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x3,
            value=Op.BALANCE(
                address=0xFAA10B404AB607779993C016CD5DA73AE1F29D7E
            ),
        )
        + Op.SSTORE(key=0xA, value=Op.SUB(Op.MLOAD(offset=0x3E7), Op.GAS))
        + Op.STOP,
        storage={0: 18},
        nonce=0,
        address=Address(0xFD9AFC8315A88141164E2A753157EA3E0F72C707),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        target: Account(
            storage={
                0: 18,
                1: 32,
                2: 0x1122334455667788991011121314151617181920000000000000000000000000,  # noqa: E501
                3: 0xE8D4498280,
                4: 18,
                7: 1,
                8: 1,
                10: 0x2CB0A,
                100: 17,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
