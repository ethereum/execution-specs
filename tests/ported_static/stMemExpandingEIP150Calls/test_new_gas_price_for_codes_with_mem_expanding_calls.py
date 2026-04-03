"""
Test_new_gas_price_for_codes_with_mem_expanding_calls.

Ported from:
state_tests/stMemExpandingEIP150Calls/NewGasPriceForCodesWithMemExpandingCallsFiller.json
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
    [
        "state_tests/stMemExpandingEIP150Calls/NewGasPriceForCodesWithMemExpandingCallsFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_new_gas_price_for_codes_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_new_gas_price_for_codes_with_mem_expanding_calls."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x3956FC06BD55836ACDB92DA0E38A15F2E568C088022CF2278180477F3F7702A
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: hex
    # 0x1122334455667788991011121314151617181920212223242526272829303132
    addr = pre.deploy_contract(  # noqa: F841
        code=bytes.fromhex(
            "1122334455667788991011121314151617181920212223242526272829303132"
        ),
        balance=111,
        nonce=0,
        address=Address(0x6B6AF3C6E1714081C8C3085ACBAC8C2B21FADF0B),  # noqa: E501
    )
    # Source: hex
    # 0x6011606455
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x64, value=0x11),
        nonce=0,
        address=Address(0x7B8C83E74CC8DFADB03138C2743C70588ACE4222),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A5100000)
    # Source: hex
    # 0x73<contract:0x1000000000000000000000000000000000000010>3b60015560146000600073<contract:0x1000000000000000000000000000000000000010>3c60005160025560005460045560ff60ff60ff60ff600173<contract:0x1000000000000000000000000000000000000011>617530f160055560ff60ff60ff60ff600173<contract:0x1000000000000000000000000000000000000011>617530f260065560ff60ff60ff60ff73<contract:0x1000000000000000000000000000000000000011>617530f460075560ff60ff60ff60ff6000731000000000000000000000000000000000000013617530f160085573<eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b>316003555a600a55  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.EXTCODESIZE(
                address=0x6B6AF3C6E1714081C8C3085ACBAC8C2B21FADF0B
            ),
        )
        + Op.EXTCODECOPY(
            address=0x6B6AF3C6E1714081C8C3085ACBAC8C2B21FADF0B,
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
                address=0x7B8C83E74CC8DFADB03138C2743C70588ACE4222,
                value=0x1,
                args_offset=0xFF,
                args_size=0xFF,
                ret_offset=0xFF,
                ret_size=0xFF,
            ),
        )
        + Op.SSTORE(
            key=0x6,
            value=Op.CALLCODE(
                gas=0x7530,
                address=0x7B8C83E74CC8DFADB03138C2743C70588ACE4222,
                value=0x1,
                args_offset=0xFF,
                args_size=0xFF,
                ret_offset=0xFF,
                ret_size=0xFF,
            ),
        )
        + Op.SSTORE(
            key=0x7,
            value=Op.DELEGATECALL(
                gas=0x7530,
                address=0x7B8C83E74CC8DFADB03138C2743C70588ACE4222,
                args_offset=0xFF,
                args_size=0xFF,
                ret_offset=0xFF,
                ret_size=0xFF,
            ),
        )
        + Op.SSTORE(
            key=0x8,
            value=Op.CALL(
                gas=0x7530,
                address=0x1000000000000000000000000000000000000013,
                value=0x0,
                args_offset=0xFF,
                args_size=0xFF,
                ret_offset=0xFF,
                ret_size=0xFF,
            ),
        )
        + Op.SSTORE(
            key=0x3,
            value=Op.BALANCE(
                address=0xF1100237A29F570CBF8B107BA3CB5BF2DB42BD3F
            ),
        )
        + Op.SSTORE(key=0xA, value=Op.GAS),
        storage={0: 18},
        nonce=0,
        address=Address(0x23A2EC54F5F8589778DA7C2199CAF3B179A24CB9),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        addr: Account(balance=111),
        target: Account(
            storage={
                0: 18,
                1: 32,
                2: 0x1122334455667788991011121314151617181920000000000000000000000000,  # noqa: E501
                3: 0xE8D4A4B47280,
                4: 18,
                7: 1,
                8: 1,
                10: 0x60AE9,
                100: 17,
            },
        ),
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
