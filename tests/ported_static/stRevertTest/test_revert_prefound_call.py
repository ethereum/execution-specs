"""
Test_revert_prefound_call.

Ported from:
state_tests/stRevertTest/RevertPrefoundCallFiller.json
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
    ["state_tests/stRevertTest/RevertPrefoundCallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_prefound_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_revert_prefound_call."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    addr = Address(0x85FDDE91FD0CE22A2968E1F1B2EBB9F9E5A180BA)
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
    pre[addr] = Account(balance=1)
    # Source: lll
    # { [[0]] (CALL 50000 <eoa:0x7db299e0885c85039f56fa504a13dd8ce8a56aa7> 0 0 32 0 32) [[1]]12 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0xC350,
                address=0x85FDDE91FD0CE22A2968E1F1B2EBB9F9E5A180BA,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x1, value=0xC)
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address(0x10E193907AA28773CC8F835C3B27BB02D064CE8C),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=94000,
    )

    post = {addr: Account(storage={}, code=b"", balance=1, nonce=0)}

    state_test(env=env, pre=pre, post=post, tx=tx)
