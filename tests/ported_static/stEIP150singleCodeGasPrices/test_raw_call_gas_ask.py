"""
Test_raw_call_gas_ask.

Ported from:
state_tests/stEIP150singleCodeGasPrices/RawCallGasAskFiller.json
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
    ["state_tests/stEIP150singleCodeGasPrices/RawCallGasAskFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_raw_call_gas_ask(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_raw_call_gas_ask."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

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
    )
    # Source: lll
    # { [0] (GAS) (CALL 3000000 <contract:0x094f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[1]] (SUB @0 (GAS)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0x2DC6C0,
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=500000,
    )

    post = {
        addr: Account(storage={2: 0x727BB}),
        target: Account(storage={1: 24739}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
