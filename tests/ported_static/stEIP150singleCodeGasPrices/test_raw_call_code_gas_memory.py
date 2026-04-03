"""
Test_raw_call_code_gas_memory.

Ported from:
state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasMemoryFiller.json
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
        "state_tests/stEIP150singleCodeGasPrices/RawCallCodeGasMemoryFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_raw_call_code_gas_memory(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_raw_call_code_gas_memory."""
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
    # { [0] (GAS) (CALLCODE 30000 <contract:0x094f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 8000 0 8000) [[1]] (SUB @0 (GAS)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(
            Op.CALLCODE(
                gas=0x7530,
                address=0xE497CD0909C3691E0B6D2A42E26F36696FC27BA5,
                value=0x0,
                args_offset=0x0,
                args_size=0x1F40,
                ret_offset=0x0,
                ret_size=0x1F40,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
        nonce=0,
        address=Address(0xEFBB83CB8BB5ED4F8CBCE07972C071D88020EA1F),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=500000,
    )

    post = {
        addr: Account(storage={}),
        target: Account(storage={1: 25608, 2: 29998}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
