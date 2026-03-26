"""
test_static_call_sha256_3

Ported from:
state_tests/stStaticCall/static_CallSha256_3Filler.json
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
    ["state_tests/stStaticCall/static_CallSha256_3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_call_sha256_3(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_call_sha256_3"""
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
    # { (MSTORE 0 0xf34578907f) [[ 2 ]] (STATICCALL 500 2 0 37 0 32) [[ 0 ]] (MLOAD 0)}
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0xf34578907f)
        + Op.SSTORE(key=0x2, value=Op.STATICCALL(gas=0x1f4, address=0x2, args_offset=0x0, args_size=0x25, ret_offset=0x0, ret_size=0x20))  # noqa: E501
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0)) + Op.STOP,
        balance=0x1312d00,
        nonce=0,
        address=Address("0x9b35a511ede9cdecc6dfc827744e0ca1d0e5f236"),  # noqa: E501
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
            0: 0x7392925565d67be8e9620aacbcfaecd8cb6ec58d709d25da9eccf1d08a41ce35,
            2: 1,
        },
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
