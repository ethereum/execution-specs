"""
test_new_gas_price_for_codes

Ported from:
state_tests/stEIP150Specific/NewGasPriceForCodesFiller.json
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
    ["state_tests/stEIP150Specific/NewGasPriceForCodesFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_new_gas_price_for_codes(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_new_gas_price_for_codes"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52
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

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: raw
    # 0x1122334455667788991011121314151617181920212223242526272829303132
    addr_0x1000000000000000000000000000000000000010 = pre.deploy_contract(
        code=bytes.fromhex("1122334455667788991011121314151617181920212223242526272829303132"),  # noqa: E501
        balance=111,
        nonce=0,
        address=Address("0xc572a70afaab9d01d0a2afb855bfbafb47c8211b"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 100 0x11) }
    addr_0x1000000000000000000000000000000000000011 = pre.deploy_contract(
        code=Op.SSTORE(key=0x64, value=0x11) + Op.STOP,
        nonce=0,
        address=Address("0xad9d325b811cb0701839c07c6f139f3799476798"),  # noqa: E501
    )
    # Source: lll
    # { [999] (GAS) (SSTORE 1 (EXTCODESIZE <contract:0x1000000000000000000000000000000000000010>)) (EXTCODECOPY <contract:0x1000000000000000000000000000000000000010> 0 0 20) (SSTORE 2 (MLOAD 0)) (SSTORE 4 (SLOAD 0)) (SSTORE 5 (CALL 30000 <contract:0x1000000000000000000000000000000000000011> 1 0 0 0 0)) (SSTORE 6 (CALLCODE 30000 <contract:0x1000000000000000000000000000000000000011> 1 0 0 0 0)) (SSTORE 7 (DELEGATECALL 30000 <contract:0x1000000000000000000000000000000000000011> 0 0 0 0)) (SSTORE 8 (CALL 30000 0x1000000000000000000000000000000000000013 0 0 0 0 0)) (SSTORE 3 (BALANCE <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b>)) (SSTORE 10 (SUB (MLOAD 999) (GAS))) }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3e7, value=Op.GAS)
        + Op.SSTORE(key=0x1, value=Op.EXTCODESIZE(address=0xc572a70afaab9d01d0a2afb855bfbafb47c8211b))  # noqa: E501
        + Op.EXTCODECOPY(address=0xc572a70afaab9d01d0a2afb855bfbafb47c8211b, dest_offset=0x0, offset=0x0, size=0x14)
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x4, value=Op.SLOAD(key=0x0))
        + Op.SSTORE(key=0x5, value=Op.CALL(gas=0x7530, address=0xad9d325b811cb0701839c07c6f139f3799476798, value=0x1, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x6, value=Op.CALLCODE(gas=0x7530, address=0xad9d325b811cb0701839c07c6f139f3799476798, value=0x1, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x7, value=Op.DELEGATECALL(gas=0x7530, address=0xad9d325b811cb0701839c07c6f139f3799476798, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x8, value=Op.CALL(gas=0x7530, address=0x1000000000000000000000000000000000000013, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x3, value=Op.BALANCE(address=0xfaa10b404ab607779993c016cd5da73ae1f29d7e))  # noqa: E501
        + Op.SSTORE(key=0xa, value=Op.SUB(Op.MLOAD(offset=0x3e7), Op.GAS))
        + Op.STOP,
        storage={0: 18},
        nonce=0,
        address=Address("0xfd9afc8315a88141164e2a753157ea3e0f72c707"),  # noqa: E501
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
        target: Account(
                storage={
            0: 18,
            1: 32,
            2: 0x1122334455667788991011121314151617181920000000000000000000000000,
            3: 0xe8d4498280,
            4: 18,
            7: 1,
            8: 1,
            10: 0x2cb0a,
            100: 17,
        },
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
