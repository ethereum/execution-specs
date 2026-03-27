"""
Test_returndatacopy_after_successful_staticcall.

Ported from:
state_tests/stReturnDataTest/returndatacopy_after_successful_staticcallFiller.json
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
    [
        "state_tests/stReturnDataTest/returndatacopy_after_successful_staticcallFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatacopy_after_successful_staticcall(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_returndatacopy_after_successful_staticcall."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    addr_0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6 = Address(
        "0x6c7410da158fa432392fcad5989e1b28280f99d8"
    )
    sender = EOA(
        key=0x834185262E53584684BF2B72C64E510013C235D0F45E462DB65900455DF45A35
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=111669149696,
    )

    pre[addr_0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6] = Account(
        balance=0x1000000
    )
    # Source: lll
    # { (STATICCALL 60000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) (RETURNDATACOPY 0x0 0x0 32) ( SSTORE 0 (MLOAD 0))}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.STATICCALL(
                gas=0xEA60,
                address=0x52FD0CBC013EE33577EEC035031DBC4489A1E0BD,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x20)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={
            0: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
        },
        nonce=0,
        address=Address("0x4bedf636cb41e5dcf09d038de843004824dfbb3a"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0x0 (CALLER)) (RETURN 0 32) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLER)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.STOP,
        balance=0x6400000000,
        nonce=0,
        address=Address("0x52fd0cbc013ee33577eec035031dbc4489a1e0bd"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=100000,
        gas_price=10,
    )

    post = {
        target: Account(
            storage={0: 0x4BEDF636CB41E5DCF09D038DE843004824DFBB3A},
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
