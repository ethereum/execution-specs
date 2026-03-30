"""
Test_delegatecall_emptycontract.

Ported from:
state_tests/stDelegatecallTestHomestead/delegatecallEmptycontractFiller.json
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
    [
        "state_tests/stDelegatecallTestHomestead/delegatecallEmptycontractFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegatecall_emptycontract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_delegatecall_emptycontract."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x11489F9B076D3F3185EBE5C6E2DBEDBE9E283A6CE75895780134252B3DD5DBCC
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # { [[ 0 ]] (DELEGATECALL 50000 0x945304eb96065b2a98b57a48a06ae28d285a71b5 0 64 0 64 )}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.DELEGATECALL(
                gas=0xC350,
                address=0x945304EB96065B2A98B57A48A06AE28D285A71B5,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=1000,
        nonce=0,
        address=Address(0x4A88CF3B3F1DABDD27E62FCB5DF86D7D685E0044),  # noqa: E501
    )
    pre[sender] = Account(balance=0x10C8E0)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=105044,
    )

    post = {target: Account(storage={0: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
