"""
Test_return_test.

Ported from:
state_tests/stInitCodeTest/ReturnTestFiller.json
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
    ["state_tests/stInitCodeTest/ReturnTestFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_return_test(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_return_test."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x194F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_1 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
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
    # {(CALL 2000 0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b 0 30 1 31 1) [[0]](MLOAD 0) (RETURN 30 2)}  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0x7D0,
                address=0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                value=0x0,
                args_offset=0x1E,
                args_size=0x1,
                ret_offset=0x1F,
                ret_size=0x1,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.RETURN(offset=0x1E, size=0x2)
        + Op.STOP,
        nonce=0,
        address=Address(0x194F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )
    pre[sender] = Account(balance=0x989680)
    # Source: lll
    # {(MSTORE 0 0x15) (RETURN 31 1)}
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x15)
        + Op.RETURN(offset=0x1F, size=0x1)
        + Op.STOP,
        balance=0x186A0,
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=300000,
    )

    post = {contract_0: Account(storage={0: 21})}

    state_test(env=env, pre=pre, post=post, tx=tx)
