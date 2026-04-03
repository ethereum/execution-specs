"""
Test_raw_call_gas_value_transfer.

Ported from:
state_tests/stEIP150singleCodeGasPrices/RawCallGasValueTransferFiller.json
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
        "state_tests/stEIP150singleCodeGasPrices/RawCallGasValueTransferFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_raw_call_gas_value_transfer(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_raw_call_gas_value_transfer."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # { [[2]] (GAS) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x2, value=Op.GAS) + Op.STOP,
        nonce=0,
        address=Address(0xE497CD0909C3691E0B6D2A42E26F36696FC27BA5),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { [0] (GAS) (CALL 30000 <contract:0x094f5374fce5edbc8e2a8697c15331677e6ebf0b> 10 0 0 0 0) [[1]] (SUB @0 (GAS)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0x7530,
                address=0xE497CD0909C3691E0B6D2A42E26F36696FC27BA5,
                value=0xA,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
        nonce=0,
        address=Address(0xC2955AF3F56C0D3150BE7ABBD80A01914337D211),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=500000,
        value=10,
    )

    post = {
        addr: Account(storage={2: 32298}),
        target: Account(storage={1: 31439}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
