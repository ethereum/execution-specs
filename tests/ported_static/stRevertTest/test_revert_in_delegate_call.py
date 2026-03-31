"""
Test_revert_in_delegate_call.

Ported from:
state_tests/stRevertTest/RevertInDelegateCallFiller.json
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
    Fork,
)
from execution_testing.vm import Op

from execution_testing.forks import Amsterdam

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertInDelegateCallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_in_delegate_call(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_revert_in_delegate_call."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xA2333EEF5630066B928DEA5FD85A239F511B5B067D1441EE7AC290D0122B917B
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000 if fork >= Amsterdam else 1000000,
    )

    # Source: lll
    # { [[ 0 ]] (DELEGATECALL 50000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 64 0 64 ) [[ 1 ]] (RETURNDATASIZE) (RETURNDATACOPY 63 0 32) [[2]](MLOAD 63)}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.DELEGATECALL(
                gas=0xC350,
                address=0xC3ECFE24C185AD3C946EBFF4624131E8AF5220A2,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
        + Op.RETURNDATACOPY(dest_offset=0x3F, offset=0x0, size=0x20)
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x3F))
        + Op.STOP,
        balance=1000,
        nonce=0,
        address=Address(0x23EA33DC3AA11F5A1DA3643BB13956382B9B6767),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 32 10) (REVERT 32 32) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x20, value=0xA)
        + Op.REVERT(offset=0x20, size=0x20)
        + Op.STOP,
        nonce=0,
        address=Address(0xC3ECFE24C185AD3C946EBFF4624131E8AF5220A2),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5F5E100)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=2105044 if fork >= Amsterdam else 105044,
    )

    post = {target: Account(storage={1: 32, 2: 10})}

    state_test(env=env, pre=pre, post=post, tx=tx)
