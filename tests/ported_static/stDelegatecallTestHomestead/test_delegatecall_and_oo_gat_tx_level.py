"""
test_delegatecall_and_oo_gat_tx_level

Ported from:
state_tests/stDelegatecallTestHomestead/delegatecallAndOOGatTxLevelFiller.json
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
    ["state_tests/stDelegatecallTestHomestead/delegatecallAndOOGatTxLevelFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegatecall_and_oo_gat_tx_level(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_delegatecall_and_oo_gat_tx_level"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: lll
    # {  [[ 0 ]] (DELEGATECALL 3000001 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0 ) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.DELEGATECALL(gas=0x2dc6c1, address=0x896f13e800125c0ccec44f3c434335f0a97bc1b, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        balance=0x186a0,
        nonce=0,
        address=Address("0x830ab9ad91366bfb2bb745e4a637f97b25087928"),  # noqa: E501
    )
    # Source: raw
    # 0x6001600155603760005360026000f3
    addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.MSTORE8(offset=0x0, value=0x37)
        + Op.RETURN(offset=0x0, size=0x2),
        balance=23,
        nonce=0,
        address=Address("0x0896f13e800125c0ccec44f3c434335f0a97bc1b"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=3000000,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={0: 1, 1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
