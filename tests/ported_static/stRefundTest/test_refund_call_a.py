"""
Test_refund_call_a.

Ported from:
state_tests/stRefundTest/refund_CallAFiller.json
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
    ["state_tests/stRefundTest/refund_CallAFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_call_a(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_refund_call_a."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
    sender = EOA(
        key=0x752660E61324E901F7231DFAE39984F4D433A241D533838E4700925F477814FD
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: lll
    # { [[ 0 ]] (CALL 5500 <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 0 )}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x157C,
                address=0xF4C9FC42FAEDA49049E3B8E2B97A17CC2FE95718,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        storage={1: 1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x3D72F604B4D56320853A5ECE45772DBBF419F315),  # noqa: E501
    )
    pre[sender] = Account(balance=0x1312D00)
    # Source: lll
    # { [[ 1 ]] 0 }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={1: 1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xF4C9FC42FAEDA49049E3B8E2B97A17CC2FE95718),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=200000,
        value=10,
    )

    post = {
        target: Account(storage={0: 1, 1: 1}, balance=0xDE0B6B3A764000A),
        coinbase: Account(balance=0),
        sender: Account(balance=0x12A2AD2, nonce=1),
        addr: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
