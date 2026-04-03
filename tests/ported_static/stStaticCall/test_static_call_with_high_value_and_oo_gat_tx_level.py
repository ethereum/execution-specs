"""
Test_static_call_with_high_value_and_oo_gat_tx_level.

Ported from:
state_tests/stStaticCall/static_callWithHighValueAndOOGatTxLevelFiller.json
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
        "state_tests/stStaticCall/static_callWithHighValueAndOOGatTxLevelFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_call_with_high_value_and_oo_gat_tx_level(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_call_with_high_value_and_oo_gat_tx_level."""
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
        gas_limit=30000000,
    )

    # Source: lll
    # {  [[ 0 ]] (STATICCALL 3000001 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0 ) [[ 1 ]] (MLOAD 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x2DC6C1,
                address=0xD5D9E9E0158920B17B6DF82FAC474B3E2691EE99,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0x186A0,
        nonce=0,
        address=Address(0x5B4A9566E26075AA8FFBEE639B15CBF0292368F6),  # noqa: E501
    )
    # Source: raw
    # 0x603760005360026000f3
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0x0, value=0x37)
        + Op.RETURN(offset=0x0, size=0x2),
        balance=23,
        nonce=0,
        address=Address(0xD5D9E9E0158920B17B6DF82FAC474B3E2691EE99),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=3000000,
    )

    post = {target: Account(storage={0: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
