"""
Test_return_test2.

Ported from:
state_tests/stInitCodeTest/ReturnTest2Filler.json
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
    ["state_tests/stInitCodeTest/ReturnTest2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_return_test2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_return_test2."""
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
        gas_limit=1000000000,
    )

    # Source: lll
    # {(MSTORE 0 0x15)(CALL 7000 0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b 0 0 32 32 32) [[0]](MLOAD 0) [[1]](MLOAD 32) (RETURN 0 64)}  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x15)
        + Op.POP(
            Op.CALL(
                gas=0x1B58,
                address=0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x20,
                ret_size=0x20,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
        + Op.RETURN(offset=0x0, size=0x40)
        + Op.STOP,
        nonce=0,
        address=Address(0x194F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )
    pre[sender] = Account(balance=0x989680)
    # Source: lll
    # {(MSTORE 0 (MUL 3 (CALLDATALOAD 0)))(RETURN 0 32)}
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0, value=Op.MUL(0x3, Op.CALLDATALOAD(offset=0x0))
        )
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.STOP,
        balance=0x186A0,
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=250000,
    )

    post = {contract_0: Account(storage={0: 21, 1: 63})}

    state_test(env=env, pre=pre, post=post, tx=tx)
