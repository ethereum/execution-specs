"""
Test_suicide_to_existing_contract.

Ported from:
state_tests/stEIP150Specific/SuicideToExistingContractFiller.json
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
    ["state_tests/stEIP150Specific/SuicideToExistingContractFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicide_to_existing_contract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_suicide_to_existing_contract."""
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
    # { [0] (GAS) (CALL 60000 <contract:0x1000000000000000000000000000000000000118> 0 0 0 0 0) [[1]] (SUB @0 (GAS)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0xEA60,
                address=0x79968A94DBEDB20475585E9DD4DAE6333ADD4C01,
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
        address=Address(0xE110D543AADC3060D6B9E80D3E16BE7A828128EC),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT <contract:target:0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b>) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=0xE110D543AADC3060D6B9E80D3E16BE7A828128EC
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x79968A94DBEDB20475585E9DD4DAE6333ADD4C01),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        addr: Account(
            storage={},
            code=bytes.fromhex(
                "73e110d543aadc3060d6b9e80d3e16be7a828128ecff00"
            ),
            balance=0,
            nonce=0,
        ),
        target: Account(storage={1: 7637}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
