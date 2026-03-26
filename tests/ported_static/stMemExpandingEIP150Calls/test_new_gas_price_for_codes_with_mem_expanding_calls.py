"""
test_new_gas_price_for_codes_with_mem_expanding_calls

Ported from:
state_tests/stMemExpandingEIP150Calls/NewGasPriceForCodesWithMemExpandingCallsFiller.json
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
    ["state_tests/stMemExpandingEIP150Calls/NewGasPriceForCodesWithMemExpandingCallsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_new_gas_price_for_codes_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_new_gas_price_for_codes_with_mem_expanding_calls"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x3956fc06bd55836acdb92da0e38a15f2e568c088022cf2278180477f3f7702a
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: hex
    # 0x1122334455667788991011121314151617181920212223242526272829303132
    addr_0x1000000000000000000000000000000000000010 = pre.deploy_contract(
        code=bytes.fromhex("1122334455667788991011121314151617181920212223242526272829303132"),  # noqa: E501
        balance=111,
        nonce=0,
        address=Address("0x6b6af3c6e1714081c8c3085acbac8c2b21fadf0b"),  # noqa: E501
    )
    # Source: hex
    # 0x6011606455
    addr_0x1000000000000000000000000000000000000011 = pre.deploy_contract(
        code=Op.SSTORE(key=0x64, value=0x11),
        nonce=0,
        address=Address("0x7b8c83e74cc8dfadb03138c2743c70588ace4222"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xe8d4a5100000)
    # Source: hex
    # 0x73<contract:0x1000000000000000000000000000000000000010>3b60015560146000600073<contract:0x1000000000000000000000000000000000000010>3c60005160025560005460045560ff60ff60ff60ff600173<contract:0x1000000000000000000000000000000000000011>617530f160055560ff60ff60ff60ff600173<contract:0x1000000000000000000000000000000000000011>617530f260065560ff60ff60ff60ff73<contract:0x1000000000000000000000000000000000000011>617530f460075560ff60ff60ff60ff6000731000000000000000000000000000000000000013617530f160085573<eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b>316003555a600a55
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.EXTCODESIZE(address=0x6b6af3c6e1714081c8c3085acbac8c2b21fadf0b))  # noqa: E501
        + Op.EXTCODECOPY(address=0x6b6af3c6e1714081c8c3085acbac8c2b21fadf0b, dest_offset=0x0, offset=0x0, size=0x14)
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x4, value=Op.SLOAD(key=0x0))
        + Op.SSTORE(key=0x5, value=Op.CALL(gas=0x7530, address=0x7b8c83e74cc8dfadb03138c2743c70588ace4222, value=0x1, args_offset=0xff, args_size=0xff, ret_offset=0xff, ret_size=0xff))  # noqa: E501
        + Op.SSTORE(key=0x6, value=Op.CALLCODE(gas=0x7530, address=0x7b8c83e74cc8dfadb03138c2743c70588ace4222, value=0x1, args_offset=0xff, args_size=0xff, ret_offset=0xff, ret_size=0xff))  # noqa: E501
        + Op.SSTORE(key=0x7, value=Op.DELEGATECALL(gas=0x7530, address=0x7b8c83e74cc8dfadb03138c2743c70588ace4222, args_offset=0xff, args_size=0xff, ret_offset=0xff, ret_size=0xff))  # noqa: E501
        + Op.SSTORE(key=0x8, value=Op.CALL(gas=0x7530, address=0x1000000000000000000000000000000000000013, value=0x0, args_offset=0xff, args_size=0xff, ret_offset=0xff, ret_size=0xff))  # noqa: E501
        + Op.SSTORE(key=0x3, value=Op.BALANCE(address=0xf1100237a29f570cbf8b107ba3cb5bf2db42bd3f))  # noqa: E501
        + Op.SSTORE(key=0xa, value=Op.GAS),
        storage={0: 18},
        nonce=0,
        address=Address("0x23a2ec54f5f8589778da7c2199caf3b179a24cb9"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=600000,
        nonce=0,
        gas_price=10,
    )

    post = {
        addr_0x1000000000000000000000000000000000000010: Account(balance=111),
        target: Account(
                storage={
            0: 18,
            1: 32,
            2: 0x1122334455667788991011121314151617181920000000000000000000000000,
            3: 0xe8d4a4b47280,
            4: 18,
            7: 1,
            8: 1,
            10: 0x60ae9,
            100: 17,
        },
            ),
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
