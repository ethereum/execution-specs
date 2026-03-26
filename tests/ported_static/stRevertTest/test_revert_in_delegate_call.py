"""
test_revert_in_delegate_call

Ported from:
state_tests/stRevertTest/RevertInDelegateCallFiller.json
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
    ["state_tests/stRevertTest/RevertInDelegateCallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_in_delegate_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_revert_in_delegate_call"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xa2333eef5630066b928dea5fd85a239f511b5b067d1441ee7ac290d0122b917b
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # { [[ 0 ]] (DELEGATECALL 50000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 64 0 64 ) [[ 1 ]] (RETURNDATASIZE) (RETURNDATACOPY 63 0 32) [[2]](MLOAD 63)}
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.DELEGATECALL(gas=0xc350, address=0xc3ecfe24c185ad3c946ebff4624131e8af5220a2, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
        + Op.RETURNDATACOPY(dest_offset=0x3f, offset=0x0, size=0x20)
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x3f)) + Op.STOP,
        balance=1000,
        nonce=0,
        address=Address("0x23ea33dc3aa11f5a1da3643bb13956382b9b6767"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 32 10) (REVERT 32 32) }
    addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x20, value=0xa) + Op.REVERT(offset=0x20, size=0x20)
        + Op.STOP,
        nonce=0,
        address=Address("0xc3ecfe24c185ad3c946ebff4624131e8af5220a2"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5f5e100)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=105044,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={1: 32, 2: 10})}

    state_test(env=env, pre=pre, post=post, tx=tx)
