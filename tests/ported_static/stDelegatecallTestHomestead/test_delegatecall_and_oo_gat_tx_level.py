"""
Test_delegatecall_and_oo_gat_tx_level.

Ported from:
state_tests/stDelegatecallTestHomestead/delegatecallAndOOGatTxLevelFiller.json
"""

import pytest
from execution_testing import (
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
        "state_tests/stDelegatecallTestHomestead/delegatecallAndOOGatTxLevelFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegatecall_and_oo_gat_tx_level(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_delegatecall_and_oo_gat_tx_level."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: raw
    # 0x6001600155603760005360026000f3
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.MSTORE8(offset=0x0, value=0x37)
        + Op.RETURN(offset=0x0, size=0x2),
        balance=23,
        nonce=0,
    )
    # Source: lll
    # {  [[ 0 ]] (DELEGATECALL 3000001 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0 ) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.DELEGATECALL(
                gas=0x2DC6C1,
                address=addr,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=0x186A0,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=3000000,
    )

    post = {target: Account(storage={0: 1, 1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
