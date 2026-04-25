"""
Test_raw_create_gas.

Ported from:
state_tests/stEIP150singleCodeGasPrices/RawCreateGasFiller.json
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
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP150singleCodeGasPrices/RawCreateGasFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_raw_create_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_raw_create_gas."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
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
    # { [0] (GAS) (CREATE 0 0 0) [[1]] (SUB @0 (GAS)) }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.CREATE(value=0x0, offset=0x0, size=0x0))
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=500000,
    )

    post = {
        contract_0: Account(storage={1: 32022}),
        compute_create_address(address=contract_0, nonce=0): Account(
            balance=0
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
