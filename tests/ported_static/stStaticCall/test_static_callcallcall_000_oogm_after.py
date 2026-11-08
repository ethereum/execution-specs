"""
Test_static_callcallcall_000_oogm_after.

Ported from:
state_tests/stStaticCall/static_callcallcall_000_OOGMAfterFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callcallcall_000_OOGMAfterFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
def test_static_callcallcall_000_oogm_after(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_callcallcall_000_oogm_after."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # {  (MSTORE 3 1) }
    addr_3 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
    )
    # Source: lll
    # {  (MSTORE 3 1) (STATICCALL 120020 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) (MSTORE 32 1) }  # noqa: E501
    addr_2 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x1D4D4,
                address=addr_3,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x20, value=0x1)
        + Op.STOP,
    )
    # Source: lll
    # {  (MSTORE 3 1) (STATICCALL 400080 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (SSTORE 3 1)}  # noqa: E501
    addr = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x61AD0,
                address=addr_2,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x3, value=0x1)
        + Op.STOP,
    )
    # Source: lll
    # {  [[ 0 ]] (STATICCALL 600150 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 111 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x92856,
                address=addr,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x6F, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1720000,
    )

    post = {
        target: Account(storage={0: 0, 1: 0, 2: 0, 3: 0, 111: 1}),
        addr: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_2: Account(storage={2: 0, 3: 0}),
        addr_3: Account(storage={3: 0}),
    }

    state_test(pre=pre, post=post, tx=tx)
