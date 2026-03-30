"""
Test_ab_acalls2.

Ported from:
state_tests/stSystemOperationsTest/ABAcalls2Filler.json
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
    ["state_tests/stSystemOperationsTest/ABAcalls2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_ab_acalls2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_ab_acalls2."""
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
        gas_limit=10000000000,
    )

    # Source: lll
    # {  [[ 0 ]] (ADD (SLOAD 0) 1) (CALL (- (GAS) 100000) <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 1 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.CALL(
            gas=Op.SUB(Op.GAS, 0x186A0),
            address=0xA890CEB693666313E0A5A1BE4F59F06C1E33F5C9,
            value=0x1,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xC58B2120D2AD0CBFCCD6EBAAE6C11258ACEAC41B),  # noqa: E501
    )
    # Source: lll
    # { [[ 0 ]] (ADD (SLOAD 0) 1) (CALL (- (GAS) 100000) <contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0 0) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.CALL(
            gas=Op.SUB(Op.GAS, 0x186A0),
            address=0xC58B2120D2AD0CBFCCD6EBAAE6C11258ACEAC41B,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xA890CEB693666313E0A5A1BE4F59F06C1E33F5C9),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1000000000,
        value=0x186A0,
    )

    post = {
        target: Account(storage={0: 201}),
        addr: Account(storage={0: 201}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
