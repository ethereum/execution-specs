"""
test_returndatacopy_after_successful_delegatecall

Ported from:
state_tests/stReturnDataTest/returndatacopy_after_successful_delegatecallFiller.json
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
    ["state_tests/stReturnDataTest/returndatacopy_after_successful_delegatecallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatacopy_after_successful_delegatecall(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_returndatacopy_after_successful_delegatecall"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x834185262e53584684bf2b72c64e510013c235d0f45e462db65900455df45a35
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

    # Source: lll
    # { (DELEGATECALL 60000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) (RETURNDATACOPY 0x0 0x0 32) ( SSTORE 0 (MLOAD 0))}
    target = pre.deploy_contract(
        code=Op.POP(Op.DELEGATECALL(gas=0xea60, address=0x52fd0cbc013ee33577eec035031dbc4489a1e0bd, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x20)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0)) + Op.STOP,
        storage={
            0: 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff,
        },
        nonce=0,
        address=Address("0xb669c96e9e7ccfd69d0fd0ffcf9260e9d1e6f5c4"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0x0 (CALLER)) (RETURN 0 32) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.CALLER)
        + Op.RETURN(offset=0x0, size=0x20) + Op.STOP,
        balance=0x6400000000,
        nonce=0,
        address=Address("0x52fd0cbc013ee33577eec035031dbc4489a1e0bd"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=100000,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(
                storage={0: 0xc102734f6a1e4747310179c0a0fc16e674aa901d},
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
