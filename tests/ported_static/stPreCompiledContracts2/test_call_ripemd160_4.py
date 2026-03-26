"""
test_call_ripemd160_4

Ported from:
state_tests/stPreCompiledContracts2/CallRipemd160_4Filler.json
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
    ["state_tests/stPreCompiledContracts2/CallRipemd160_4Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_ripemd160_4(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_call_ripemd160_4"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869
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

    # Source: lll
    # { (MSTORE 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) [[ 2 ]] (CALL 720 3 0 0 32 0 32) [[ 0 ]] (MLOAD 0)}
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
        + Op.SSTORE(key=0x2, value=Op.CALL(gas=0x2d0, address=0x3, value=0x0, args_offset=0x0, args_size=0x20, ret_offset=0x0, ret_size=0x20))  # noqa: E501
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0)) + Op.STOP,
        balance=0x1312d00,
        nonce=0,
        address=Address("0x93e74099c6b1cf5e73a1cdd021c6942f9a814d9b"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=365224,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(
                storage={
            0: 0x1cf4e77f5966e13e109703cd8a0df7ceda7f3dc3,
            2: 1,
        },
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
