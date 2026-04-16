"""
Test_static_call_sha256_3.

Ported from:
state_tests/stStaticCall/static_CallSha256_3Filler.json
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
    ["state_tests/stStaticCall/static_CallSha256_3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_call_sha256_3(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_call_sha256_3."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: lll
    # { (MSTORE 0 0xf34578907f) [[ 2 ]] (STATICCALL 500 2 0 37 0 32) [[ 0 ]] (MLOAD 0)}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0xF34578907F)
        + Op.SSTORE(
            key=0x2,
            value=Op.STATICCALL(
                gas=0x1F4,
                address=0x2,
                args_offset=0x0,
                args_size=0x25,
                ret_offset=0x0,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0x1312D00,
        nonce=0,
        address=Address(0x9B35A511EDE9CDECC6DFC827744E0CA1D0E5F236),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=365224,
        value=0x186A0,
    )

    post = {
        target: Account(
            storage={
                0: 0x7392925565D67BE8E9620AACBCFAECD8CB6EC58D709D25DA9ECCF1D08A41CE35,  # noqa: E501
                2: 1,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
